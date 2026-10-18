import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TestCaseOptimization from './TestCaseOptimization';

export default function TestCaseOptimizationForm({ onRun, onSetOutput, process, sessionId, disabled, onTestCaseOptimization, onPromptChange, currentPrompt, onOptimizationResults }) {
  // Ref to store the run function from TestCaseOptimization
  const runFunctionRef = React.useRef(null);
  const [canRun, setCanRun] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  // TestCaseOptimization component'inden run function'ını al
  const handleRunFunction = (runFn) => {
    runFunctionRef.current = runFn;
    setCanRun(!!runFn);
    
    console.log('TestCaseOptimizationForm - Run function updated:', {
      hasFunction: !!runFn,
      canRun: !!runFn
    });
  };

  // TestCaseOptimization'dan gelen loading durumunu takip et
  const handleLoadingChange = (loading) => {
    setIsRunning(loading);
  };

  // Expose the run function to the parent component
  React.useEffect(() => {
    const runHandler = {
      handleRun: runFunctionRef.current,
      canRun: canRun || isRunning, // Button should be enabled when canRun OR when running (to allow stopping)
      isRunning: isRunning
    };
    
    console.log('TestCaseOptimizationForm - Updating parent with:', runHandler);
    
    // Call onTestCaseOptimization to set the form state in TabPanel
    if (onTestCaseOptimization && typeof onTestCaseOptimization === 'function') {
      onTestCaseOptimization(runHandler);
    }
    
    // onRun prop'u için handler'ı bağla
    if (onRun && typeof onRun === 'function') {
      onRun.current = runFunctionRef.current;
    }
  }, [canRun, isRunning, onTestCaseOptimization, onRun]);

  return (
    <TestCaseOptimization 
      onPromptChange={onPromptChange}
      onRunFunction={handleRunFunction}
      onLoadingChange={handleLoadingChange}
      onOptimizationResults={onOptimizationResults}
    />
  );
}
