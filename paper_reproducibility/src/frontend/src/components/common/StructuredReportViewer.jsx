import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { clsx } from 'clsx';

/**
 * StructuredReportViewer Component
 * Displays ISTQB/IEEE compliant test reports in a structured, tabbed interface
 */
export default function StructuredReportViewer({ reportData }) {
  const [activeSection, setActiveSection] = useState(null);
  const [viewMode, setViewMode] = useState('sections'); // 'sections' or 'full'

  // Parse report data (could be JSON or markdown)
  const parseReport = () => {
    try {
      // Clean reportData: remove ```json and ``` wrappers if present
      let cleanData = typeof reportData === 'string' ? reportData.trim() : reportData;
      
      if (typeof cleanData === 'string') {
        if (cleanData.startsWith('```json')) {
          cleanData = cleanData.replace(/^```json\n?/, '').replace(/\n?```$/, '');
        } else if (cleanData.startsWith('```')) {
          cleanData = cleanData.replace(/^```\n?/, '').replace(/\n?```$/, '');
        }
      }
      
      const parsed = typeof cleanData === 'string' ? JSON.parse(cleanData) : cleanData;
      
      if (parsed.sections) {
        return {
          format: 'structured',
          metadata: parsed.report_metadata || {},
          sections: parsed.sections || {},
          fullMarkdown: parsed.full_report_markdown || ''
        };
      }
    } catch (e) {
      // Not JSON, treat as markdown
    }
    
    // Parse markdown into sections
    return {
      format: 'markdown',
      sections: parseMarkdownSections(reportData),
      fullMarkdown: reportData
    };
  };

  // Parse markdown by headers
  const parseMarkdownSections = (markdown) => {
    if (!markdown) return {};
    
    const sections = {};
    const lines = markdown.split('\n');
    let currentSection = null;
    let currentContent = [];
    
    // Define section mappings
    const sectionMappings = {
      'TEST SUMMARY': { key: 'test_summary', icon: '📋' },
      'TEST METRICS': { key: 'test_metrics', icon: '📊' },
      'DEFECT SUMMARY': { key: 'defect_summary', icon: '🐛' },
      'TEST COMPLETION CRITERIA': { key: 'completion_criteria', icon: '🎯' },
      'SESSION-BY-SESSION': { key: 'session_analysis', icon: '🔄' },
      'SESSION ANALYSIS': { key: 'session_analysis', icon: '🔄' },
      'COMPARATIVE ANALYSIS': { key: 'comparative_analysis', icon: '📈' },
      'CROSS-SESSION ANALYSIS': { key: 'comparative_analysis', icon: '📈' },
      'RISK ASSESSMENT': { key: 'risk_assessment', icon: '⚠️' },
      'RECOMMENDATIONS': { key: 'recommendations', icon: '💡' },
      'ACTION ITEMS': { key: 'recommendations', icon: '💡' },
      'METRICS DASHBOARD': { key: 'metrics_dashboard', icon: '📊' },
      'QUALITY ASSESSMENT': { key: 'quality_assessment', icon: '🎯' },
      'PROCESS BREAKDOWN': { key: 'process_breakdown', icon: '📈' },
      'APPENDICES': { key: 'appendices', icon: '📋' }
    };
    
    for (const line of lines) {
      // Check if line is a section header (## or ###)
      if (line.match(/^#{1,3}\s+(.+)/)) {
        // Save previous section
        if (currentSection) {
          sections[currentSection.key] = {
            title: currentSection.title,
            icon: currentSection.icon,
            content: currentContent.join('\n').trim()
          };
        }
        
        // Start new section
        const headerText = line.replace(/^#{1,3}\s+/, '').trim();
        const cleanHeader = headerText.replace(/[📋📊🐛🎯🔄📈⚠️💡📊]/g, '').trim().toUpperCase();
        
        // Find matching section
        let matched = false;
        for (const [key, mapping] of Object.entries(sectionMappings)) {
          if (cleanHeader.includes(key)) {
            currentSection = {
              key: mapping.key,
              title: headerText,
              icon: mapping.icon
            };
            currentContent = [];
            matched = true;
            break;
          }
        }
        
        if (!matched) {
          currentSection = null;
        }
      } else if (currentSection) {
        currentContent.push(line);
      }
    }
    
    // Save last section
    if (currentSection) {
      sections[currentSection.key] = {
        title: currentSection.title,
        icon: currentSection.icon,
        content: currentContent.join('\n').trim()
      };
    }
    
    return sections;
  };

  const report = parseReport();
  const sections = Object.entries(report.sections || {});
  
  // Auto-select first section
  if (activeSection === null && sections.length > 0) {
    setActiveSection(sections[0][0]);
  }

  return (
    <div className="structured-report-viewer bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">
              📊 Test Report {report.metadata?.report_id && `(${report.metadata.report_id})`}
            </h2>
            {report.metadata?.standards_applied && (
              <p className="text-blue-100 text-sm mt-1">
                Standards: {report.metadata.standards_applied.join(' • ')}
              </p>
            )}
          </div>
          
          {/* View Mode Toggle */}
          <div className="flex gap-2 bg-white/10 rounded-lg p-1">
            <button
              onClick={() => setViewMode('sections')}
              className={clsx(
                'px-4 py-2 rounded-md text-sm font-medium transition-colors',
                viewMode === 'sections'
                  ? 'bg-white text-blue-600'
                  : 'text-white hover:bg-white/20'
              )}
            >
              📑 Sections
            </button>
            <button
              onClick={() => setViewMode('full')}
              className={clsx(
                'px-4 py-2 rounded-md text-sm font-medium transition-colors',
                viewMode === 'full'
                  ? 'bg-white text-blue-600'
                  : 'text-white hover:bg-white/20'
              )}
            >
              📄 Full Report
            </button>
          </div>
        </div>
      </div>

      {viewMode === 'sections' ? (
        <div className="flex h-[calc(100vh-250px)]">
          {/* Sidebar Navigation */}
          <div className="w-80 border-r border-gray-200 overflow-y-auto bg-gray-50">
            <div className="p-4 space-y-1">
              {sections.map(([key, section]) => (
                <button
                  key={key}
                  onClick={() => setActiveSection(key)}
                  className={clsx(
                    'w-full text-left px-4 py-3 rounded-lg transition-all flex items-center gap-3',
                    activeSection === key
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'hover:bg-gray-100 text-gray-700'
                  )}
                >
                  <span className="text-2xl">{section.icon}</span>
                  <span className="font-medium text-sm">{section.title}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto">
            {activeSection && sections.find(([key]) => key === activeSection) && (
              <div className="p-8">
                <div className="prose prose-blue max-w-none">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-6">
                          <table className="min-w-full divide-y divide-gray-300 border border-gray-300" {...props} />
                        </div>
                      ),
                      th: ({ node, ...props }) => (
                        <th className="px-4 py-3 bg-gray-50 text-left text-sm font-semibold text-gray-900 border-b border-gray-300" {...props} />
                      ),
                      td: ({ node, ...props }) => (
                        <td className="px-4 py-3 text-sm text-gray-700 border-b border-gray-200" {...props} />
                      ),
                      code: ({ node, inline, ...props }) => (
                        inline 
                          ? <code className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm" {...props} />
                          : <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto" {...props} />
                      )
                    }}
                  >
                    {sections.find(([key]) => key === activeSection)[1].content}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Full Report View */
        <div className="p-8 overflow-y-auto h-[calc(100vh-250px)]">
          <div className="prose prose-blue max-w-none">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto my-6">
                    <table className="min-w-full divide-y divide-gray-300 border border-gray-300" {...props} />
                  </div>
                ),
                th: ({ node, ...props }) => (
                  <th className="px-4 py-3 bg-gray-50 text-left text-sm font-semibold text-gray-900 border-b border-gray-300" {...props} />
                ),
                td: ({ node, ...props }) => (
                  <td className="px-4 py-3 text-sm text-gray-700 border-b border-gray-200" {...props} />
                ),
                code: ({ node, inline, ...props }) => (
                  inline 
                    ? <code className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm" {...props} />
                    : <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto" {...props} />
                )
              }}
            >
              {report.fullMarkdown || reportData}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
