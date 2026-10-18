import sys
import json
import os
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from pymongo import MongoClient, UpdateOne

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QTableView, QMessageBox, QSpinBox, QFormLayout, QGroupBox
)


# =========================================================
# CONFIG
# =========================================================

JSON_FILE = "calculation_db.coverage_db.json"

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB_NAME = "calculation_db"
MONGO_DECISION_COLLECTION = "human_oracle_decisions"

DECISIONS = ["Unique", "Similar", "Unclear"]
DEFAULT_CONFIDENCE = 3


# =========================================================
# DATA LOAD
# =========================================================

def load_json_documents(json_file: str) -> List[Dict[str, Any]]:
    if not os.path.exists(json_file):
        raise FileNotFoundError(f"Input file not found: {json_file}")

    with open(json_file, "r", encoding="utf-8-sig") as f:
        content = f.read().strip()

    if not content:
        return []

    if content.startswith("["):
        return json.loads(content)

    return [json.loads(line) for line in content.splitlines() if line.strip()]


def normalize_test_case(test_case: Any) -> Dict[str, str]:
    if not isinstance(test_case, dict):
        test_case = {}

    return {
        "original_id": str(test_case.get("TestCaseID", "")),
        "scenario_id": str(test_case.get("ScenarioID", "")),
        "title": str(test_case.get("Title", "")),
        "description": str(test_case.get("Description", "")),
        "objective": str(test_case.get("Objective", "")),
        "category": str(test_case.get("Category", "")),
        "comments": str(test_case.get("Comments", "")),
    }


def get_process_name(test_case_optimization: Dict[str, Any], optimization_output: Dict[str, Any]) -> str:
    return (
        optimization_output.get("process_name")
        or optimization_output.get("process_title")
        or test_case_optimization.get("process_name")
        or test_case_optimization.get("process_title")
        or ""
    )


def get_optimization_type(optimization_output: Dict[str, Any], comparison_logs: List[Dict[str, Any]]) -> str:
    optimization_type = optimization_output.get("optimization_type")
    if optimization_type:
        return optimization_type
    if comparison_logs:
        return comparison_logs[0].get("optimization_type", "")
    return ""


def create_case_key(
    session_id: str,
    process_name: str,
    optimization_type: str,
    used_model: str,
    test_case: Dict[str, str],
) -> str:
    raw = "|".join([
        str(session_id),
        str(process_name),
        str(optimization_type),
        str(used_model),
        str(test_case.get("scenario_id", "")),
        str(test_case.get("original_id", "")),
        str(test_case.get("title", "")),
        str(test_case.get("description", "")),
        str(test_case.get("objective", "")),
    ])
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def extract_all_test_cases(documents: List[Dict[str, Any]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for doc_index, document in enumerate(documents):
        session_id = document.get("session_id", "")
        created_at = document.get("created_at", "")
        processes = document.get("processes", {})

        if "test_case_optimization" not in processes:
            continue

        test_case_optimization = processes.get("test_case_optimization", {})
        optimization_output = test_case_optimization.get("output", {})

        unique_test_cases = optimization_output.get("unique_test_cases", []) or []
        similar_test_cases = optimization_output.get("similar_test_cases", []) or []
        comparison_logs = optimization_output.get("comparison_logs", []) or []

        process_name = get_process_name(test_case_optimization, optimization_output)
        optimization_type = get_optimization_type(optimization_output, comparison_logs)
        used_model = optimization_output.get("used_model", "")
        timestamp = optimization_output.get("timestamp", "")

        for test_case in unique_test_cases:
            normalized = normalize_test_case(test_case)
            rows.append({
                "case_key": create_case_key(session_id, process_name, optimization_type, used_model, normalized),
                "document_index": doc_index,
                "session_id": session_id,
                "created_at": created_at,
                "process_name": process_name,
                "optimization_type": optimization_type,
                "used_model": used_model,
                "timestamp": timestamp,
                "original_llm_label": "Unique",
                **normalized,
            })

        for item in similar_test_cases:
            duplicate_case = normalize_test_case(item.get("DuplicateCase", {}))
            matched_with = normalize_test_case(item.get("MatchedWith", {}))

            for label, test_case in [
                ("Similar-DuplicateCase", duplicate_case),
                ("Similar-MatchedWith", matched_with),
            ]:
                rows.append({
                    "case_key": create_case_key(session_id, process_name, optimization_type, used_model, test_case),
                    "document_index": doc_index,
                    "session_id": session_id,
                    "created_at": created_at,
                    "process_name": process_name,
                    "optimization_type": optimization_type,
                    "used_model": used_model,
                    "timestamp": timestamp,
                    "original_llm_label": label,
                    **test_case,
                })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df = df.drop_duplicates(subset=["case_key"]).sort_values(
        by=[
            "session_id",
            "process_name",
            "optimization_type",
            "used_model",
            "scenario_id",
            "original_id",
            "title",
        ],
        na_position="last",
    ).reset_index(drop=True)

    df.insert(0, "row_ref", [f"R{i:04d}" for i in range(1, len(df) + 1)])
    return df


# =========================================================
# MONGODB
# =========================================================

class OracleRepository:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB_NAME]
        self.collection = self.db[MONGO_DECISION_COLLECTION]

        # Important:
        # If the old unique index case_key_1 exists in MongoDB, drop it manually once:
        # db.human_oracle_decisions.dropIndex("case_key_1")
        # This application now uses row_ref as the unique key.
        self.collection.create_index("row_ref", unique=True)
        self.collection.create_index("session_id")
        self.collection.create_index("process_name")
        self.collection.create_index("decision")

    def load_decisions(self) -> Dict[str, Dict[str, Any]]:
        records = list(self.collection.find({}, {"_id": 0}))
        return {item["row_ref"]: item for item in records if "row_ref" in item}

    def save_many(self, records: List[Dict[str, Any]]) -> None:
        now = datetime.now().isoformat(timespec="seconds")

        operations = []
        for record in records:
            row_ref = record.get("row_ref", "")
            if not row_ref:
                continue

            record["oracle_saved_at"] = now

            operations.append(
                UpdateOne(
                    {"row_ref": row_ref},
                    {"$set": record},
                    upsert=True,
                )
            )

        if operations:
            self.collection.bulk_write(operations)


# =========================================================
# TABLE MODEL
# =========================================================

class TestCaseTableModel(QAbstractTableModel):
    COLUMNS = [
        "row_ref",
        "original_id",
        "title",
        "decision",
        "similar_to",
        "used_model",
        "optimization_type",
        "original_llm_label",
    ]

    HEADERS = [
        "Ref",
        "TC ID",
        "Title",
        "Decision",
        "Similar To",
        "Model",
        "Opt.",
        "LLM Label",
    ]

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.df = df.copy()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.df)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            value = self.df.iloc[index.row()].get(self.COLUMNS[index.column()], "")
            return str(value)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.HEADERS[section]

        return str(section + 1)

    def get_row(self, row_index: int) -> Dict[str, Any]:
        return self.df.iloc[row_index].to_dict()

    def update_df(self, df: pd.DataFrame):
        self.beginResetModel()
        self.df = df.copy()
        self.endResetModel()


# =========================================================
# MAIN WINDOW
# =========================================================

class HumanOracleApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Human Oracle for Test Case Uniqueness - PySide6")
        self.resize(1500, 900)

        self.repo = OracleRepository()

        documents = load_json_documents(JSON_FILE)
        self.all_df = extract_all_test_cases(documents)

        if self.all_df.empty:
            raise RuntimeError("No test cases found in input JSON.")

        self.saved_decisions = self.repo.load_decisions()
        self.all_df = self.merge_saved_decisions(self.all_df)

        self.filtered_df = self.all_df.copy()
        self.current_case: Optional[Dict[str, Any]] = None

        self.build_ui()
        self.populate_filters()
        self.apply_filters()

    def merge_saved_decisions(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["decision"] = "Unique"
        df["similar_to"] = ""
        df["confidence"] = DEFAULT_CONFIDENCE
        df["oracle_saved_at"] = ""
        df["dirty"] = False

        for idx, row in df.iterrows():
            saved = self.saved_decisions.get(row["row_ref"])
            if not saved:
                continue

            df.at[idx, "decision"] = saved.get("decision", "Unique")
            df.at[idx, "similar_to"] = saved.get("similar_to", "")
            df.at[idx, "confidence"] = int(saved.get("confidence", DEFAULT_CONFIDENCE) or DEFAULT_CONFIDENCE)
            df.at[idx, "oracle_saved_at"] = saved.get("oracle_saved_at", "")
            df.at[idx, "dirty"] = False

        return df

    def build_ui(self):
        root = QWidget()
        root_layout = QVBoxLayout(root)

        top_layout = QHBoxLayout()

        self.process_combo = QComboBox()

        self.session_info_label = QLabel("Session: -")
        self.session_info_label.setStyleSheet("font-weight: bold;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search title / description / objective")

        self.apply_button = QPushButton("Apply Filter")
        self.copy_process_json_button = QPushButton("Copy Process JSON")
        self.save_all_button = QPushButton("Save All Changes")
        self.reload_button = QPushButton("Reload Decisions")

        top_layout.addWidget(QLabel("Process"))
        top_layout.addWidget(self.process_combo)
        top_layout.addWidget(self.session_info_label)
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.apply_button)
        top_layout.addWidget(self.copy_process_json_button)
        top_layout.addWidget(self.save_all_button)
        top_layout.addWidget(self.reload_button)

        root_layout.addLayout(top_layout)

        splitter = QSplitter(Qt.Horizontal)

        self.table_model = TestCaseTableModel(pd.DataFrame())
        self.table = QTableView()
        self.table.setModel(self.table_model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        splitter.addWidget(self.table)

        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)

        self.title_label = QLabel("Select a test case")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.meta_label = QLabel("")
        self.meta_label.setWordWrap(True)

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)

        self.objective_text = QTextEdit()
        self.objective_text.setReadOnly(True)

        oracle_group = QGroupBox("Human Oracle Decision")
        oracle_form = QFormLayout(oracle_group)

        self.decision_combo = QComboBox()
        self.decision_combo.addItems(DECISIONS)

        self.similar_to_input = QLineEdit()

        self.confidence_spin = QSpinBox()
        self.confidence_spin.setMinimum(1)
        self.confidence_spin.setMaximum(5)
        self.confidence_spin.setValue(DEFAULT_CONFIDENCE)

        self.apply_current_button = QPushButton("Apply Current Change")

        oracle_form.addRow("Decision", self.decision_combo)
        oracle_form.addRow("Similar To", self.similar_to_input)
        oracle_form.addRow("Confidence", self.confidence_spin)
        oracle_form.addRow(self.apply_current_button)

        detail_layout.addWidget(self.title_label)
        detail_layout.addWidget(self.meta_label)
        detail_layout.addWidget(QLabel("Description"))
        detail_layout.addWidget(self.description_text)
        detail_layout.addWidget(QLabel("Objective"))
        detail_layout.addWidget(self.objective_text)
        detail_layout.addWidget(oracle_group)

        splitter.addWidget(detail_widget)
        splitter.setSizes([900, 600])

        root_layout.addWidget(splitter)
        self.setCentralWidget(root)

        self.apply_button.clicked.connect(self.apply_filters)
        self.process_combo.currentTextChanged.connect(self.apply_filters)
        self.search_input.returnPressed.connect(self.apply_filters)
        self.copy_process_json_button.clicked.connect(self.copy_selected_process_json)
        self.apply_current_button.clicked.connect(self.apply_current_change)
        self.save_all_button.clicked.connect(self.save_all_changes)
        self.reload_button.clicked.connect(self.reload_decisions)
        self.table.selectionModel().selectionChanged.connect(self.on_table_selection_changed)

    def populate_filters(self):
        self.process_combo.clear()

        processes = sorted(
            self.all_df["process_name"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        self.process_combo.addItems(processes)

    def apply_filters(self):
        df = self.all_df.copy()

        selected_process = self.process_combo.currentText()
        if selected_process:
            df = df[df["process_name"].astype(str) == selected_process]

        search_text = self.search_input.text().strip().lower()
        if search_text:
            mask = (
                df["title"].astype(str).str.lower().str.contains(search_text, na=False)
                | df["description"].astype(str).str.lower().str.contains(search_text, na=False)
                | df["objective"].astype(str).str.lower().str.contains(search_text, na=False)
            )
            df = df[mask]

        self.filtered_df = df.reset_index(drop=True)
        self.table_model.update_df(self.filtered_df)

        sessions = sorted(
            self.filtered_df["session_id"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        if len(sessions) == 1:
            self.session_info_label.setText(f"Session: {sessions[0]}")
        elif len(sessions) > 1:
            self.session_info_label.setText(f"Sessions: {', '.join(sessions)}")
        else:
            self.session_info_label.setText("Session: -")

        dirty_count = int((self.all_df["dirty"] == True).sum())
        self.statusBar().showMessage(
            f"Displayed: {len(self.filtered_df)} | Total: {len(self.all_df)} | Unsaved changes: {dirty_count}"
        )

        if len(self.filtered_df) > 0:
            self.table.selectRow(0)

    def on_table_selection_changed(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return

        row_index = selected[0].row()
        self.current_case = self.table_model.get_row(row_index)
        self.load_case_to_detail(self.current_case)

    def load_case_to_detail(self, row: Dict[str, Any]):
        self.title_label.setText(
            f"{row.get('row_ref', '')} — {row.get('original_id', '')} — {row.get('title', '')}"
        )

        self.meta_label.setText(
            f"Session: {row.get('session_id', '')} | "
            f"Scenario: {row.get('scenario_id', '')} | "
            f"Model: {row.get('used_model', '')} | "
            f"Optimization: {row.get('optimization_type', '')} | "
            f"LLM Label: {row.get('original_llm_label', '')} | "
            f"Saved: {row.get('oracle_saved_at', '-') or '-'}"
        )

        self.description_text.setPlainText(str(row.get("description", "")))
        self.objective_text.setPlainText(str(row.get("objective", "")))

        decision = row.get("decision", "Unique")
        self.decision_combo.setCurrentText(decision if decision in DECISIONS else "Unique")

        self.similar_to_input.setText(str(row.get("similar_to", "")))
        self.confidence_spin.setValue(int(row.get("confidence", DEFAULT_CONFIDENCE) or DEFAULT_CONFIDENCE))

    def apply_current_change(self):
        if not self.current_case:
            return

        row_ref = self.current_case.get("row_ref", "")

        decision = self.decision_combo.currentText()
        similar_to = self.similar_to_input.text().strip()
        confidence = self.confidence_spin.value()

        mask_all = self.all_df["row_ref"] == row_ref
        mask_filtered = self.filtered_df["row_ref"] == row_ref

        self.all_df.loc[mask_all, "decision"] = decision
        self.all_df.loc[mask_all, "similar_to"] = similar_to
        self.all_df.loc[mask_all, "confidence"] = confidence
        self.all_df.loc[mask_all, "dirty"] = True

        self.filtered_df.loc[mask_filtered, "decision"] = decision
        self.filtered_df.loc[mask_filtered, "similar_to"] = similar_to
        self.filtered_df.loc[mask_filtered, "confidence"] = confidence
        self.filtered_df.loc[mask_filtered, "dirty"] = True

        self.table_model.update_df(self.filtered_df)

        dirty_count = int((self.all_df["dirty"] == True).sum())

        self.statusBar().showMessage(
            f"Applied change for {row_ref}. Unsaved changes: {dirty_count}"
        )

    def build_record_from_row(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "row_ref": row_dict.get("row_ref", ""),
            "original_id": row_dict.get("original_id", ""),
            "title": row_dict.get("title", ""),
            "description": row_dict.get("description", ""),
            "objective": row_dict.get("objective", ""),
            "decision": row_dict.get("decision", "Unique"),
            "similar_to": row_dict.get("similar_to", ""),
            "scenario_id": row_dict.get("scenario_id", ""),
            "category": row_dict.get("category", ""),
            "comments": row_dict.get("comments", ""),
            "session_id": row_dict.get("session_id", ""),
            "created_at": row_dict.get("created_at", ""),
            "process_name": row_dict.get("process_name", ""),
            "optimization_type": row_dict.get("optimization_type", ""),
            "used_model": row_dict.get("used_model", ""),
            "timestamp": row_dict.get("timestamp", ""),
            "original_llm_label": row_dict.get("original_llm_label", ""),
            "confidence": int(row_dict.get("confidence", DEFAULT_CONFIDENCE) or DEFAULT_CONFIDENCE),
            "reviewer_id": "human_expert_1",
        }

    def save_all_changes(self):
        dirty_df = self.all_df[self.all_df["dirty"] == True].copy()

        if dirty_df.empty:
            QMessageBox.information(
                self,
                "No Changes",
                "Kaydedilecek değişiklik bulunmuyor."
            )
            return

        records = []

        for _, row in dirty_df.iterrows():
            records.append(self.build_record_from_row(row.to_dict()))

        self.repo.save_many(records)

        saved_at = datetime.now().isoformat(timespec="seconds")
        changed_row_refs = dirty_df["row_ref"].tolist()

        self.all_df.loc[self.all_df["row_ref"].isin(changed_row_refs), "dirty"] = False
        self.all_df.loc[self.all_df["row_ref"].isin(changed_row_refs), "oracle_saved_at"] = saved_at

        QMessageBox.information(
            self,
            "Saved",
            f"{len(records)} changed records saved to MongoDB."
        )

        self.apply_filters()

    def copy_selected_process_json(self):
        selected_process = self.process_combo.currentText()

        if not selected_process:
            QMessageBox.warning(
                self,
                "No Process Selected",
                "Kopyalanacak process seçili değil."
            )
            return

        process_df = self.all_df[
            self.all_df["process_name"].astype(str) == selected_process
        ].copy()

        if process_df.empty:
            QMessageBox.warning(
                self,
                "No Data",
                "Seçilen process için test case bulunamadı."
            )
            return

        process_df = process_df.sort_values(
            by=["row_ref", "scenario_id", "original_id", "title"],
            na_position="last"
        )

        export_records = []

        for _, row in process_df.iterrows():
            export_records.append({
                "row_ref": row.get("row_ref", ""),
                "original_id": row.get("original_id", ""),
                "title": row.get("title", ""),
                "description": row.get("description", ""),
                "objective": row.get("objective", ""),
                "decision": row.get("decision", ""),
                "similar_to": row.get("similar_to", "")
            })

        export_json = json.dumps(
            export_records,
            ensure_ascii=False,
            indent=2
        )

        QApplication.clipboard().setText(export_json)

        sessions = sorted(
            process_df["session_id"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        session_text = ", ".join(sessions) if sessions else "-"

        QMessageBox.information(
            self,
            "Copied",
            f"{len(export_records)} test case JSON formatında panoya kopyalandı.\n\n"
            f"Process: {selected_process}\n"
            f"Session: {session_text}"
        )

    def reload_decisions(self):
        self.saved_decisions = self.repo.load_decisions()
        self.all_df = self.merge_saved_decisions(self.all_df)
        self.apply_filters()
        QMessageBox.information(self, "Reloaded", "MongoDB decisions reloaded.")


# =========================================================
# MAIN
# =========================================================

def main():
    app = QApplication(sys.argv)

    try:
        window = HumanOracleApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "Error", str(e))
        raise


if __name__ == "__main__":
    main()
