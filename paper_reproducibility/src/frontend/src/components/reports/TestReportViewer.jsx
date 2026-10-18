import React from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  ChevronDownIcon, 
  ChevronRightIcon, 
  ArrowDownTrayIcon, 
  DocumentTextIcon 
} from '@heroicons/react/24/outline';

/**
 * TestReportViewer - Interactive, collapsible markdown renderer for ISTQB/IEEE test reports
 */
const TestReportViewer = ({ output, isLoading }) => {
  const [error, setError] = React.useState(null);
  const [expandedSections, setExpandedSections] = React.useState({});
  const [viewMode, setViewMode] = React.useState('sections'); // 'sections' or 'full'
  
  // Clean output: remove code block wrappers and handle JSON responses
  const cleanOutput = React.useMemo(() => {
    if (!output) return '';
    
    let cleaned = output.trim();
    
    // Check if output is JSON format - convert to markdown
    if (cleaned.startsWith('{') && cleaned.endsWith('}')) {
      try {
        const jsonData = JSON.parse(cleaned);
        
        // Try to extract markdown from common JSON fields
        if (jsonData.full_report_markdown) {
          cleaned = jsonData.full_report_markdown;
        } else if (jsonData.report_content) {
          cleaned = jsonData.report_content;
        } else if (jsonData.markdown) {
          cleaned = jsonData.markdown;
        } else if (jsonData.sections) {
          // Convert sections object to markdown with proper headers
          const sections = jsonData.sections;
          const markdownParts = [];
          
          for (const [key, section] of Object.entries(sections)) {
            if (section && typeof section === 'object') {
              const title = section.title || key.replace(/_/g, ' ').toUpperCase();
              const icon = section.icon || '📋';
              let content = section.content || '';
              
              // Remove duplicate header from content if present
              // Content often starts with: # 📋 TEST SUMMARY
              const contentLines = content.split('\n');
              if (contentLines.length > 0 && contentLines[0].trim().startsWith('#')) {
                // Remove first line if it's a header (duplicate)
                content = contentLines.slice(1).join('\n').trim();
              }
              
              // Create proper markdown section with ## header
              markdownParts.push(`## ${icon} ${title}\n\n${content}`);
            }
          }
          
          cleaned = markdownParts.join('\n\n');
          console.log('✅ Converted JSON sections to markdown:', markdownParts.length, 'sections');
        }
      } catch (e) {
        console.warn('⚠️ Failed to parse JSON output, using as-is:', e.message);
        // Continue with original text
      }
    }
    
    // Remove ```markdown or ```json wrappers
    if (cleaned.startsWith('```')) {
      cleaned = cleaned.replace(/^```(?:markdown|json)?\n?/, '').replace(/\n?```$/, '');
    }
    
    return cleaned;
  }, [output]);

  // Parse report into sections based on ## headings
  const reportSections = React.useMemo(() => {
    if (!cleanOutput) return [];
    
    const lines = cleanOutput.split('\n');
    const sections = [];
    let currentSection = null;
    let headerContent = []; // Store content before first section
    
    lines.forEach((line, index) => {
      // Detect main sections (## headings with optional emoji/numbering)
      // Pattern: ## [emoji] [number.] TITLE or ## TITLE
      const mainHeadingMatch = line.match(/^##\s+(?:[📋📊🐛🎯⚠️💡📈📉✅❌🔍🚀📝🔄🏆📘💻⚡🧪]+\s*)?(?:\d+\.\s*)?(.+)/);
      
      if (mainHeadingMatch) {
        // Save previous section
        if (currentSection) {
          sections.push(currentSection);
        } else if (headerContent.length > 0) {
          // Save header content before first section
          sections.push({
            title: '__header__',
            content: headerContent.join('\n'),
            startLine: 0,
            icon: '📄',
            isHeader: true
          });
          headerContent = [];
        }
        
        // Extract icon from the line if present
        const iconMatch = line.match(/^##\s+([📋📊🐛🎯⚠️💡📈📉✅❌🔍🚀📝🔄🏆📘💻⚡🧪]+)/);
        
        // Start new section
        currentSection = {
          title: mainHeadingMatch[1].trim(),
          content: [line],
          startLine: index,
          icon: iconMatch ? iconMatch[1] : '📄'
        };
      } else if (currentSection) {
        currentSection.content.push(line);
      } else {
        // Content before first section (header, title, etc.)
        headerContent.push(line);
      }
    });
    
    // Add last section
    if (currentSection) {
      sections.push(currentSection);
    } else if (headerContent.length > 0) {
      // If no sections found, treat everything as header
      sections.push({
        title: '__header__',
        content: headerContent.join('\n'),
        startLine: 0,
        icon: '📄',
        isHeader: true
      });
    }
    
    // Convert content arrays to strings
    return sections.map(section => ({
      ...section,
      content: Array.isArray(section.content) ? section.content.join('\n') : section.content
    }));
  }, [cleanOutput]);

  // Toggle section expansion
  const toggleSection = (index) => {
    setExpandedSections(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Expand all sections
  const expandAll = () => {
    const allExpanded = {};
    reportSections.forEach((_, index) => {
      allExpanded[index] = true;
    });
    setExpandedSections(allExpanded);
  };

  // Collapse all sections
  const collapseAll = () => {
    setExpandedSections({});
  };

  // Download report as markdown file
  const downloadReport = () => {
    // Add metadata header to the report
    const reportDate = new Date().toISOString().split('T')[0];
    const reportTime = new Date().toLocaleTimeString();
    
    const enhancedReport = `<!--
================================================================================
STLC Manager - Test Report
================================================================================
Generated: ${reportDate} ${reportTime}
Standards Compliance:
  - ISTQB Foundation Level & Test Manager
  - IEEE 829-2008 Test Documentation
  - ISO/IEC/IEEE 29119-3 Software Testing
================================================================================
-->

${cleanOutput}

---

## 📄 Document Information

**Report Metadata:**
- Document Type: ISTQB & IEEE 829 Compliant Test Report
- Generated By: STLC Manager AI System
- Generation Date: ${reportDate}
- Generation Time: ${reportTime}
- Format: Markdown
- Standards: ISTQB Foundation/Test Manager, IEEE 829-2008, ISO/IEC/IEEE 29119-3

**Usage:**
- This report can be viewed in any Markdown viewer
- Recommended viewers: VS Code, Typora, GitHub, GitLab
- Can be converted to PDF using pandoc or similar tools
- Tables and formatting are best viewed in Markdown-compatible viewers

**Standards References:**
- [ISTQB](https://www.istqb.org/) - International Software Testing Qualifications Board
- [IEEE 829-2008](https://standards.ieee.org/) - IEEE Standard for Software Test Documentation
- [ISO/IEC/IEEE 29119](https://www.iso.org/) - Software Testing Standards

---

*End of Report*
`;
    
    const blob = new Blob([enhancedReport], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `STLC-Test-Report-${reportDate}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 m-4">
        <h3 className="text-lg font-semibold text-red-800 mb-2">⚠️ Rendering Error</h3>
        <p className="text-red-700 mb-4">{error.message}</p>
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-red-600 hover:text-red-800">Show raw content</summary>
          <pre className="mt-2 p-4 bg-white rounded border border-red-200 text-xs overflow-x-auto max-h-96">
            {cleanOutput.substring(0, 2000)}...
          </pre>
        </details>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Generating test report...</p>
        </div>
      </div>
    );
  }

  if (!output) {
    return (
      <div className="text-center p-12 text-gray-500">
        No report generated yet. Select sessions and generate a report.
      </div>
    );
  }

  // Render sectioned view
  const renderSectionedView = () => {
    return (
      <div className="space-y-3">
        {reportSections.map((section, index) => {
          // Skip rendering internal header section separately - it's shown at the top
          if (section.title === '__header__' || section.isHeader) {
            return (
              <div key={index} className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border-2 border-blue-200">
                <div className="prose prose-blue prose-lg max-w-none">
                  <ReactMarkdown components={markdownComponents}>
                    {section.content}
                  </ReactMarkdown>
                </div>
              </div>
            );
          }

          const isExpanded = expandedSections[index];

          return (
            <div 
              key={index} 
              className="border-2 border-gray-300 rounded-xl overflow-hidden bg-white shadow-md hover:shadow-lg transition-all duration-200"
            >
              {/* Section Header - Clickable */}
              <button
                onClick={() => toggleSection(index)}
                className="w-full flex items-center justify-between p-5 bg-gradient-to-r from-gray-50 via-white to-gray-50 hover:from-blue-50 hover:via-blue-50/50 hover:to-blue-50 transition-all duration-200 text-left border-b-2 border-gray-200"
              >
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{section.icon}</span>
                  <div>
                    <h3 className="text-xl font-bold text-gray-800">{section.title}</h3>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {isExpanded ? 'Click to collapse' : 'Click to expand'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isExpanded ? (
                    <ChevronDownIcon className="w-6 h-6 text-blue-600 font-bold" />
                  ) : (
                    <ChevronRightIcon className="w-6 h-6 text-gray-400" />
                  )}
                </div>
              </button>

              {/* Section Content - Collapsible */}
              {isExpanded && (
                <div className="p-6 bg-white">
                  <div className="prose prose-blue prose-lg max-w-none">
                    <ReactMarkdown components={markdownComponents}>
                      {section.content}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  // Render full view
  const renderFullView = () => {
    return (
      <div className="prose prose-blue prose-lg max-w-none">
        <ErrorBoundary onError={setError}>
          <ReactMarkdown components={markdownComponents}>
            {cleanOutput}
          </ReactMarkdown>
        </ErrorBoundary>
      </div>
    );
  };

  // Markdown component configuration
  const markdownComponents = {
    // Custom table styling
    table: ({ node, ...props }) => (
      <div className="overflow-x-auto my-6">
        <table className="min-w-full divide-y divide-gray-300 border border-gray-300 shadow-sm" {...props} />
      </div>
    ),
    thead: ({ node, ...props }) => (
      <thead className="bg-gray-50" {...props} />
    ),
    th: ({ node, ...props }) => (
      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b-2 border-gray-300" {...props} />
    ),
    td: ({ node, ...props }) => (
      <td className="px-4 py-3 text-sm text-gray-700 border-b border-gray-200" {...props} />
    ),
    // Custom code block styling
    code: ({ node, inline, ...props }) => (
      inline 
        ? <code className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
        : <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono" {...props} />
    ),
    // Custom heading styling with better spacing
    h1: ({ node, ...props }) => (
      <h1 className="text-3xl font-bold text-gray-900 mt-8 mb-4 pb-2 border-b-2 border-blue-600" {...props} />
    ),
    h2: ({ node, ...props }) => (
      <h2 className="text-2xl font-bold text-gray-800 mt-8 mb-3 pb-2 border-b border-gray-300" {...props} />
    ),
    h3: ({ node, ...props }) => (
      <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-2" {...props} />
    ),
    h4: ({ node, ...props }) => (
      <h4 className="text-lg font-semibold text-gray-700 mt-4 mb-2" {...props} />
    ),
    // Custom list styling
    ul: ({ node, ordered, ...props }) => (
      <ul className="list-disc list-inside space-y-1 my-4" {...props} />
    ),
    ol: ({ node, ordered, ...props }) => (
      <ol className="list-decimal list-inside space-y-1 my-4" {...props} />
    ),
    // Custom blockquote
    blockquote: ({ node, ...props }) => (
      <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-50 italic text-gray-700" {...props} />
    ),
    // Horizontal rule
    hr: ({ node, ...props }) => (
      <hr className="my-8 border-t-2 border-gray-300" {...props} />
    ),
  };

  return (
    <div className="test-report-viewer bg-white rounded-lg shadow-lg">
      {/* Standards Badge Header */}
      <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 px-6 py-5 mb-0 rounded-t-lg border-b-4 border-yellow-400">
        <div className="mb-3">
          <h2 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
            📊 STLC Test Report
            <span className="text-sm font-normal bg-white/20 px-2 py-1 rounded">Professional Standards Compliant</span>
          </h2>
          <p className="text-blue-100 text-sm">
            Generated using international software testing standards and best practices
          </p>
        </div>
        
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-white/90 text-blue-700 border-2 border-white shadow-sm">
              📘 ISTQB Foundation Level
            </span>
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-white/90 text-indigo-700 border-2 border-white shadow-sm">
              📘 ISTQB Test Manager (Advanced)
            </span>
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-white/90 text-purple-700 border-2 border-white shadow-sm">
              📘 IEEE 829-2008
            </span>
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-white/90 text-pink-700 border-2 border-white shadow-sm">
              📘 ISO/IEC/IEEE 29119-3
            </span>
          </div>
          
          {/* View Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={downloadReport}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white text-blue-700 hover:bg-blue-50 transition-colors shadow-md border-2 border-white"
              title="Download report as Markdown file"
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              Download Report
            </button>
          </div>
        </div>
      </div>
      
      {/* Standards Info Panel */}
      <div className="bg-blue-50 border-b-2 border-blue-200 px-6 py-3">
        <details className="group">
          <summary className="cursor-pointer text-sm font-medium text-blue-900 hover:text-blue-700 flex items-center gap-2">
            <span className="text-blue-600 group-open:rotate-90 transition-transform">▶</span>
            About Testing Standards Used in This Report
          </summary>
          <div className="mt-3 pl-6 text-sm text-blue-800 space-y-2">
            <p><strong>ISTQB Foundation Level:</strong> Provides basic testing terminology, test process methodology, and fundamental quality metrics.</p>
            <p><strong>ISTQB Test Manager:</strong> Advanced test management techniques including risk-based testing, strategic analysis, and resource optimization.</p>
            <p><strong>IEEE 829-2008:</strong> International standard for software test documentation structure, ensuring comprehensive and consistent reporting.</p>
            <p><strong>ISO/IEC/IEEE 29119-3:</strong> Modern test documentation best practices, quality assessment metrics, and agile methodology compliance.</p>
          </div>
        </details>
      </div>

      {/* View Mode Toggle & Section Controls */}
      <div className="px-6 mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('sections')}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'sections'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <DocumentTextIcon className="w-4 h-4" />
            Sections View
          </button>
          <button
            onClick={() => setViewMode('full')}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'full'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <DocumentTextIcon className="w-4 h-4" />
            Full View
          </button>
        </div>

        {viewMode === 'sections' && (
          <div className="flex items-center gap-2">
            <button
              onClick={expandAll}
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-green-100 text-green-700 hover:bg-green-200 transition-colors"
            >
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-orange-100 text-orange-700 hover:bg-orange-200 transition-colors"
            >
              Collapse All
            </button>
          </div>
        )}
      </div>

      {/* Report Content */}
      <div className="px-6 pb-6">
        {viewMode === 'sections' ? renderSectionedView() : renderFullView()}
      </div>
    </div>
  );
};

// Simple error boundary component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Markdown rendering error:', error, errorInfo);
    if (this.props.onError) {
      this.props.onError(error);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">⚠️ Error rendering markdown. Please check the report format.</p>
        </div>
      );
    }

    return this.props.children;
  }
}

export default TestReportViewer;
