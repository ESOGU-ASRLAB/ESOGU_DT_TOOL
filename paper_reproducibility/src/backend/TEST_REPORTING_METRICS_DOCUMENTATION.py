"""
Test Reporting Matematiksel Metrikler ve Formüller
=================================================

Bu dokümanda STLC Manager Test Reporting modülünde kullanılan
tüm matematiksel hesaplamalar, formüller ve metrikler yer almaktadır.

Standart Uyumluluğu:
- IEEE 829-2008: Test Metrics
- ISTQB: Quality Metrics
- ISO 25010: Software Quality Model
- ISO/IEC/IEEE 29119-3: Test Metrics
"""

# =============================================================================
# 1. TEST SCENARIO GENERATION METRİKLERİ
# =============================================================================

"""
1.1 COMPLETENESS SCORE (Tamlık Skoru)
-------------------------------------
Formula:
    completeness_ratio = complete_scenarios / total_scenarios
    completeness_score = 1 + (completeness_ratio × 9)
    
Parametreler:
    - complete_scenarios: Tüm zorunlu alanları olan senaryo sayısı
    - total_scenarios: Toplam senaryo sayısı
    
Zorunlu Alanlar:
    - ScenarioID
    - Title
    - Description
    - Objective
    
Ölçek: 1-10
Hedef: ≥ 8.0

Örnek:
    45 senaryo, 40 tanesi tam
    completeness_ratio = 40 / 45 = 0.889
    completeness_score = 1 + (0.889 × 9) = 9.0


1.2 CLARITY SCORE (Netlik Skoru)
--------------------------------
Formula:
    avg_desc_length = total_description_words / total_scenarios
    
    length_score = min(avg_desc_length / 50, 1.0) if avg_desc_length < 100
                  else max(1.0 - (avg_desc_length - 100) / 200, 0.5)
    
    structure_ratio = structured_scenarios / total_scenarios
    
    clarity_raw = (0.5 × length_score) + (0.5 × structure_ratio)
    clarity_score = 1 + (clarity_raw × 9)

Parametreler:
    - avg_desc_length: Ortalama açıklama uzunluğu (kelime)
    - structured_scenarios: Yapılandırılmış senaryo sayısı
    
Yapılandırılma Kriterleri:
    Description içinde: "step", "expected", "precondition", "result" kelimeleri
    
Optimal Uzunluk: 30-100 kelime
Ölçek: 1-10
Hedef: ≥ 7.0

Örnek:
    Ortalama 65 kelime, 35/45 yapılandırılmış
    length_score = min(65/50, 1.0) = 1.0
    structure_ratio = 35/45 = 0.778
    clarity_raw = (0.5 × 1.0) + (0.5 × 0.778) = 0.889
    clarity_score = 1 + (0.889 × 9) = 9.0


1.3 COVERAGE SCORE (Kapsam Skoru)
---------------------------------
Formula:
    category_diversity = min(unique_categories / 3, 1.0)
    
    type_diversity = (types_with_cases / total_test_types)
    
    coverage_raw = (0.5 × category_diversity) + (0.5 × type_diversity)
    coverage_score = 1 + (coverage_raw × 9)

Parametreler:
    - unique_categories: Benzersiz kategori sayısı
    - types_with_cases: Test tipi çeşitliliği (0-5)
    
Test Tipleri:
    - Functional (fonksiyonel)
    - Edge (sınır değer)
    - Negative (negatif)
    - Performance (performans)
    - Security (güvenlik)
    
Hedef Kategori: ≥ 3
Ölçek: 1-10
Hedef: ≥ 7.0

Örnek:
    4 kategori, 3 test tipi (functional, edge, negative)
    category_diversity = min(4/3, 1.0) = 1.0
    type_diversity = 3/5 = 0.6
    coverage_raw = (0.5 × 1.0) + (0.5 × 0.6) = 0.8
    coverage_score = 1 + (0.8 × 9) = 8.2


1.4 DEPTH SCORE (Derinlik Skoru)
--------------------------------
Formula:
    precond_ratio = scenarios_with_preconditions / total_scenarios
    steps_ratio = scenarios_with_steps / total_scenarios
    expected_ratio = scenarios_with_expected_results / total_scenarios
    
    depth_raw = (0.3 × precond_ratio) + (0.4 × steps_ratio) + (0.3 × expected_ratio)
    depth_score = 1 + (depth_raw × 9)

Parametreler:
    - scenarios_with_preconditions: Ön koşullu senaryo sayısı
    - scenarios_with_steps: Adım içeren senaryo sayısı
    - scenarios_with_expected_results: Beklenen sonuç içeren senaryo sayısı
    
Ağırlıklar:
    - Preconditions: %30
    - Steps: %40
    - Expected Results: %30
    
Ölçek: 1-10
Hedef: ≥ 6.0

Örnek:
    30/45 precondition, 40/45 steps, 42/45 expected results
    precond_ratio = 30/45 = 0.667
    steps_ratio = 40/45 = 0.889
    expected_ratio = 42/45 = 0.933
    depth_raw = (0.3 × 0.667) + (0.4 × 0.889) + (0.3 × 0.933) = 0.836
    depth_score = 1 + (0.836 × 9) = 8.5


1.5 OVERALL QUALITY SCORE (Genel Kalite Skoru)
----------------------------------------------
Formula:
    overall_score = (0.25 × completeness) + (0.25 × clarity) + 
                   (0.25 × coverage) + (0.25 × depth)

Ağırlıklar: Eşit (her biri %25)
Ölçek: 1-10
Hedef: ≥ 7.5

Örnek:
    completeness = 9.0, clarity = 9.0, coverage = 8.2, depth = 8.5
    overall = (0.25 × 9.0) + (0.25 × 9.0) + (0.25 × 8.2) + (0.25 × 8.5)
    overall = 2.25 + 2.25 + 2.05 + 2.125 = 8.675 ≈ 8.7
"""

# =============================================================================
# 2. TEST CASE GENERATION METRİKLERİ
# =============================================================================

"""
2.1 COMPLETENESS SCORE
---------------------
Formula:
    completeness_ratio = complete_test_cases / total_test_cases
    completeness_score = 1 + (completeness_ratio × 9)

Tamlık Kriterleri:
    (Steps VE ExpectedResult) VEYA (Description VE Objective)

Ölçek: 1-10
Hedef: ≥ 8.5

Örnek:
    180 test case, 170 tam
    completeness_ratio = 170/180 = 0.944
    completeness_score = 1 + (0.944 × 9) = 9.5


2.2 CLARITY SCORE
----------------
Formula (Adım bazlı):
    avg_steps = total_steps / total_test_cases
    steps_score = min(avg_steps / 5, 1.0) if avg_steps < 10
                 else max(1.0 - (avg_steps - 10) / 20, 0.5)
    
    test_data_ratio = cases_with_test_data / total_test_cases
    clarity_raw = (0.5 × steps_score) + (0.5 × test_data_ratio)
    clarity_score = 1 + (clarity_raw × 9)

Formula (Açıklama bazlı):
    avg_desc_length = total_description_words / total_test_cases
    desc_score = min(avg_desc_length / 65, 1.0) if avg_desc_length < 130
                else max(1.0 - (avg_desc_length - 130) / 100, 0.5)
    clarity_score = 1 + (desc_score × 9)

Optimal Değerler:
    - Adım sayısı: 3-7 adım
    - Açıklama: 30-100 kelime
    
Ölçek: 1-10
Hedef: ≥ 8.0

Örnek:
    Ortalama 4.5 adım, 140/180 test data var
    steps_score = min(4.5/5, 1.0) = 0.9
    test_data_ratio = 140/180 = 0.778
    clarity_raw = (0.5 × 0.9) + (0.5 × 0.778) = 0.839
    clarity_score = 1 + (0.839 × 9) = 8.6


2.3 COVERAGE SCORE (Pozitif/Negatif Oran)
-----------------------------------------
Formula:
    ratio_score = 1.0 - |((positive_count / negative_count) - 2)| / 4
    ratio_score = max(0.5, min(ratio_score, 1.0))
    coverage_score = 1 + (ratio_score × 9)

Hedef Oran: 2:1 (Pozitif:Negatif)
Ölçek: 1-10
Hedef: ≥ 7.0

Örnek:
    120 pozitif, 60 negatif
    ratio = 120/60 = 2.0 (ideal!)
    ratio_score = 1.0 - |2.0 - 2| / 4 = 1.0
    coverage_score = 1 + (1.0 × 9) = 10.0


2.4 DEPTH SCORE
--------------
Formula:
    detailed_ratio = detailed_test_cases / total_test_cases
    depth_score = 1 + (detailed_ratio × 9)

Detaylılık Kriterleri:
    - ≥3 adım (eski format) VEYA
    - ≥15 kelime objective (yeni format)

Ölçek: 1-10
Hedef: ≥ 7.0

Örnek:
    135/180 detaylı test case
    detailed_ratio = 135/180 = 0.75
    depth_score = 1 + (0.75 × 9) = 7.75
"""

# =============================================================================
# 3. TEST CASE OPTIMIZATION METRİKLERİ
# =============================================================================

"""
3.1 OPTIMIZATION RATE (Optimizasyon Oranı)
------------------------------------------
Formula:
    optimization_rate = (original_count - optimized_count) / original_count
    reduction_percentage = optimization_rate × 100

Parametreler:
    - original_count: Orijinal test case sayısı
    - optimized_count: Optimize edilmiş test case sayısı
    
Optimal Aralık: %20-%40 azalma
Ölçek: 0-1 (veya %0-%100)

Örnek:
    180 orijinal, 115 optimize
    optimization_rate = (180 - 115) / 180 = 0.361
    reduction_percentage = 36.1%


3.2 COMPLETENESS SCORE (Gerekçe Tamlığı)
----------------------------------------
Formula:
    completeness_ratio = cases_with_justification / total_optimized_cases
    completeness_score = 1 + (completeness_ratio × 9)

Ölçek: 1-10
Hedef: ≥ 9.0

Örnek:
    115 optimize case, 110 gerekçeli
    completeness_ratio = 110/115 = 0.957
    completeness_score = 1 + (0.957 × 9) = 9.6


3.3 CLARITY SCORE (Gerekçe Kalitesi)
------------------------------------
Formula:
    avg_rationale_length = total_rationale_words / total_optimized_cases
    clarity_raw = min(avg_rationale_length / 20, 1.0) if avg_rationale_length < 40
                 else 0.7
    clarity_score = 1 + (clarity_raw × 9)

Optimal Uzunluk: 10-30 kelime
Ölçek: 1-10
Hedef: ≥ 7.0

Örnek:
    Ortalama 18 kelime
    clarity_raw = min(18/20, 1.0) = 0.9
    clarity_score = 1 + (0.9 × 9) = 9.1


3.4 COVERAGE SCORE (Kapsam Koruma)
----------------------------------
Formula:
    if 0.2 ≤ optimization_rate ≤ 0.4:
        coverage_raw = 1.0
    elif optimization_rate < 0.2:
        coverage_raw = optimization_rate / 0.2
    else:
        coverage_raw = max(0.6, 1.0 - (optimization_rate - 0.4) / 0.3)
    
    coverage_score = 1 + (coverage_raw × 9)

İdeal Aralık: %20-%40 azalma
Ölçek: 1-10
Hedef: ≥ 8.0

Örnek:
    36.1% azalma (0.361)
    İdeal aralıkta, coverage_raw = 1.0
    coverage_score = 1 + (1.0 × 9) = 10.0
"""

# =============================================================================
# 4. TEST EXECUTION METRİKLERİ
# =============================================================================

"""
4.1 PASS RATE (Başarı Oranı)
----------------------------
Formula:
    pass_rate = (passed_tests / total_executed_tests) × 100

Parametreler:
    - passed_tests: Başarılı test sayısı
    - total_executed_tests: Toplam çalıştırılan test sayısı
    
Ölçek: %0-%100
Hedef: ≥ %90

Örnek:
    85 başarılı, 92 toplam
    pass_rate = (85 / 92) × 100 = 92.39%


4.2 DEFECT DETECTION RATE (Hata Bulma Oranı)
--------------------------------------------
Formula:
    defect_detection_rate = (failed_tests / total_executed_tests) × 100

Parametreler:
    - failed_tests: Başarısız test sayısı
    - total_executed_tests: Toplam çalıştırılan test sayısı
    
Ölçek: %0-%100
Optimal: %5-%15

Örnek:
    7 başarısız, 92 toplam
    defect_detection_rate = (7 / 92) × 100 = 7.61%


4.3 TEST EXECUTION EFFICIENCY
-----------------------------
Formula:
    execution_efficiency = total_executed_tests / planned_tests

Parametreler:
    - total_executed_tests: Çalıştırılan test sayısı
    - planned_tests: Planlanan test sayısı
    
Ölçek: 0-1 (veya %0-%100)
Hedef: ≥ 0.95 (%95)

Örnek:
    92 çalıştırıldı, 95 planlı
    execution_efficiency = 92 / 95 = 0.968 = %96.8


4.4 COMPLETENESS SCORE (Test Execution)
---------------------------------------
Formula:
    completeness_ratio = tests_with_results / total_executed_tests
    completeness_score = 1 + (completeness_ratio × 9)

Ölçek: 1-10
Hedef: = 10.0

Örnek:
    92/92 sonuçlu
    completeness_ratio = 92/92 = 1.0
    completeness_score = 1 + (1.0 × 9) = 10.0


4.5 STABILITY SCORE (Kararlılık)
--------------------------------
Formula:
    stability_ratio = passed_tests / total_executed_tests
    stability_score = 1 + (stability_ratio × 9)

Ölçek: 1-10
Hedef: ≥ 9.0

Örnek:
    85 başarılı, 92 toplam
    stability_ratio = 85/92 = 0.924
    stability_score = 1 + (0.924 × 9) = 9.3
"""

# =============================================================================
# 5. ISTQB METRİKLERİ
# =============================================================================

"""
5.1 TEST EFFECTIVENESS (Test Etkinliği)
---------------------------------------
Formula:
    test_effectiveness = (defects_found_in_testing / total_defects) × 100

Parametreler:
    - defects_found_in_testing: Test sırasında bulunan hata sayısı
    - total_defects: Toplam hata sayısı (test + production)
    
Ölçek: %0-%100
Hedef: ≥ %85
Standart: ISTQB Test Manager


5.2 DEFECT REMOVAL EFFICIENCY (DRE)
-----------------------------------
Formula:
    DRE = (defects_removed_before_release / total_defects) × 100

Parametreler:
    - defects_removed_before_release: Yayından önce giderilen hata sayısı
    - total_defects: Toplam hata sayısı
    
Ölçek: %0-%100
Hedef: ≥ %90
Standart: ISTQB Test Manager, IEEE 829


5.3 REQUIREMENT COVERAGE (Gereksinim Kapsamı)
---------------------------------------------
Formula:
    requirement_coverage = (covered_requirements / total_requirements) × 100

Parametreler:
    - covered_requirements: Kapsanan gereksinim sayısı
    - total_requirements: Toplam gereksinim sayısı
    
Ölçek: %0-%100
Hedef: = %100
Standart: IEEE 829-2008, ISO 29119-3


5.4 CODE COVERAGE (Kod Kapsamı)
-------------------------------
Formula:
    statement_coverage = (executed_statements / total_statements) × 100
    branch_coverage = (executed_branches / total_branches) × 100
    path_coverage = (executed_paths / total_paths) × 100

Ölçek: %0-%100
Hedef:
    - Statement: ≥ %85
    - Branch: ≥ %70
    - Path: ≥ %50
Standart: ISTQB Foundation, ISO 29119-3


5.5 TEST EXECUTION PRODUCTIVITY
-------------------------------
Formula:
    productivity = test_cases_executed / effort_hours

Parametreler:
    - test_cases_executed: Çalıştırılan test case sayısı
    - effort_hours: Harcanan saat
    
Ölçek: Test/Saat
Hedef: ≥ 10 test/saat (manuel), ≥ 100 test/saat (otomatik)
Standart: ISTQB Test Manager
"""

# =============================================================================
# 6. ISO 25010 KALİTE KARAKTERİSTİKLERİ
# =============================================================================

"""
6.1 FUNCTIONAL SUITABILITY (İşlevsel Uygunluk)
----------------------------------------------
Alt Karakteristikler:
    - Functional Completeness: %95 gereksinim kapsamı
    - Functional Correctness: %92 pass rate
    - Functional Appropriateness: Kullanılabilirlik skoru ≥ 8/10


6.2 PERFORMANCE EFFICIENCY (Performans Verimliliği)
--------------------------------------------------
Alt Karakteristikler:
    - Time Behaviour: Yanıt süresi ≤ 2 saniye
    - Resource Utilization: CPU ≤ %80, Memory ≤ %70
    - Capacity: Eşzamanlı kullanıcı ≥ 1000


6.3 RELIABILITY (Güvenilirlik)
------------------------------
Alt Karakteristikler:
    - Maturity: MTBF (Mean Time Between Failures) ≥ 720 saat
    - Availability: Uptime ≥ %99.9
    - Fault Tolerance: Hata durumlarında düzgün çalışma
    - Recoverability: Kurtarma süresi ≤ 5 dakika
"""

# =============================================================================
# 7. TABLO VE RAPOR ÖRNEĞİ
# =============================================================================

"""
ÖRNEK METRIK TABLOSU (Makale İçin Kullanılabilir)
================================================

| Metrik Adı | Formül | Değer | Hedef | Standart |
|------------|--------|-------|-------|----------|
| Test Senaryoları | N/A | 45 | ≥30 | ISTQB |
| Completeness Score | 1+(c/t×9) | 9.0/10 | ≥8.0 | IEEE 829 |
| Clarity Score | 1+((0.5×l+0.5×s)×9) | 9.0/10 | ≥7.0 | ISTQB |
| Coverage Score | 1+((0.5×cat+0.5×type)×9) | 8.2/10 | ≥7.0 | ISO 29119 |
| Depth Score | 1+((0.3×p+0.4×s+0.3×e)×9) | 8.5/10 | ≥6.0 | IEEE 829 |
| Overall Quality | Σ(scores)/4 | 8.7/10 | ≥7.5 | ISO 29119 |
| Test Cases | N/A | 180 | ≥120 | ISTQB |
| Positive/Negative | p:n | 120:60 | 2:1 | ISTQB |
| Optimization Rate | (o-n)/o×100 | 36.1% | 20-40% | ISTQB TM |
| Pass Rate | p/t×100 | 92.4% | ≥90% | IEEE 829 |
| Defect Detection | f/t×100 | 7.6% | 5-15% | ISTQB |
| Req. Coverage | c/t×100 | 95% | 100% | ISO 29119 |


ÖRNEK KOMPOZİT METRIK HESAPLAMA
================================

Genel Proje Kalite Skoru:

    Project_Quality = (0.20 × Scenario_Quality) +
                     (0.30 × TestCase_Quality) +
                     (0.15 × Optimization_Quality) +
                     (0.35 × Execution_Quality)

Değerler:
    Scenario_Quality = 8.7
    TestCase_Quality = 8.8
    Optimization_Quality = 9.2
    Execution_Quality = 9.3

Hesaplama:
    Project_Quality = (0.20 × 8.7) + (0.30 × 8.8) + (0.15 × 9.2) + (0.35 × 9.3)
                   = 1.74 + 2.64 + 1.38 + 3.255
                   = 9.015
                   ≈ 9.0/10

Sonuç: Proje kalitesi "EXCELLENT" (≥9.0)
"""

print(__doc__)
