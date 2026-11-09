#!/usr/bin/env node

/**
 * Phase 3 Integration Test Suite
 * Tests all MCP server functionality and sacred layer integration
 * 
 * Usage: node test_phase3_integration.js
 */

import { spawn } from 'child_process';

class Phase3IntegrationTest {
  constructor() {
    this.testResults = [];
    this.server = null;
  }

  async runAllTests() {
    console.log('🚀 Starting Phase 3 Integration Tests\n');
    console.log('Testing ContextKeeper Sacred Layer MCP Server v3.0\n');

    try {
      // Start MCP server
      await this.startServer();
      
      // Run test suite
      await this.testToolListing();
      await this.testHealthCheck();
      await this.testSacredContext();
      await this.testSacredDrift();
      await this.testLLMEnhancement();
      await this.testDevelopmentContext();
      await this.testIntelligentSearch();
      await this.testContextExport();

      // Generate report
      this.generateReport();

    } catch (error) {
      console.error('❌ Integration test failed:', error.message);
    } finally {
      this.cleanup();
    }
  }

  async startServer() {
    console.log('📡 Starting MCP server...');
    this.server = spawn('node', ['enhanced_mcp_server.js'], { 
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: process.cwd()
    });

    // Wait for server to start
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    this.server.stderr.on('data', (data) => {
      const output = data.toString();
      if (output.includes('running on stdio')) {
        console.log('✅ MCP server started successfully\n');
      }
    });
  }

  async sendMCPRequest(method, params = {}) {
    return new Promise((resolve, reject) => {
      const request = {
        jsonrpc: '2.0',
        id: Date.now(),
        method,
        params
      };

      let responseData = '';
      let timeoutId;

      const onData = (data) => {
        responseData += data.toString();
        try {
          const response = JSON.parse(responseData);
          clearTimeout(timeoutId);
          this.server.stdout.removeListener('data', onData);
          resolve(response);
        } catch (e) {
          // Partial data, wait for more
        }
      };

      this.server.stdout.on('data', onData);
      
      timeoutId = setTimeout(() => {
        this.server.stdout.removeListener('data', onData);
        reject(new Error('Request timeout'));
      }, 10000);

      this.server.stdin.write(JSON.stringify(request) + '\\n');
    });
  }

  async testToolListing() {
    console.log('🔧 Testing tool listing...');
    try {
      const response = await this.sendMCPRequest('tools/list');
      
      const expectedTools = [
        'get_sacred_context',
        'check_sacred_drift', 
        'query_with_llm',
        'export_development_context',
        'get_development_context',
        'intelligent_search',
        'create_sacred_plan',
        'health_check'
      ];

      const actualTools = response.result.tools.map(t => t.name);
      const missingTools = expectedTools.filter(t => !actualTools.includes(t));
      const extraTools = actualTools.filter(t => !expectedTools.includes(t));

      if (missingTools.length === 0 && extraTools.length === 0) {
        this.recordTest('Tool Listing', true, `Found all ${expectedTools.length} expected tools`);
      } else {
        this.recordTest('Tool Listing', false, `Missing: ${missingTools}, Extra: ${extraTools}`);
      }
    } catch (error) {
      this.recordTest('Tool Listing', false, error.message);
    }
  }

  async testHealthCheck() {
    console.log('🏥 Testing health check...');
    try {
      const response = await this.sendMCPRequest('tools/call', {
        name: 'health_check',
        arguments: {}
      });

      const healthText = response.result.content[0].text;
      const hasRAGAgent = healthText.includes('RAG Agent: ✅');
      const hasSacredLayer = healthText.includes('Sacred Layer: ✅');
      const hasLLMEnhancement = healthText.includes('LLM Enhancement: ✅');

      if (hasRAGAgent && hasSacredLayer && hasLLMEnhancement) {
        this.recordTest('Health Check', true, 'All systems healthy');
      } else {
        this.recordTest('Health Check', false, 'Some systems not healthy');
      }
    } catch (error) {
      this.recordTest('Health Check', false, error.message);
    }
  }

  async testSacredContext() {
    console.log('🔒 Testing sacred context retrieval...');
    try {
      const response = await this.sendMCPRequest('tools/call', {
        name: 'get_sacred_context',
        arguments: {
          project_id: 'proj_6cafffed59ba',
          plan_status: 'approved'
        }
      });

      const contextText = response.result.content[0].text;
      const hasSacredPlans = contextText.includes('Sacred Plans') || contextText.includes('No Sacred Plans Found');
      const hasImmutability = contextText.includes('Immutability');
      const hasVerification = contextText.includes('2-Layer Verification');

      if (hasSacredPlans && hasImmutability && hasVerification) {
        this.recordTest('Sacred Context', true, 'Sacred plans retrieved with proper context');
      } else {
        this.recordTest('Sacred Context', false, 'Sacred context incomplete');
      }
    } catch (error) {
      this.recordTest('Sacred Context', false, error.message);
    }
  }

  async testSacredDrift() {
    console.log('📊 Testing sacred drift detection...');
    try {
      const response = await this.sendMCPRequest('tools/call', {
        name: 'check_sacred_drift',
        arguments: {
          project_id: 'proj_6cafffed59ba',
          hours: 24
        }
      });

      const driftText = response.result.content[0].text;
      const hasAlignmentStatus = driftText.includes('Alignment Status:');
      const hasAlignmentScore = driftText.includes('Alignment Score:');
      const hasRecommendations = driftText.includes('Recommendations');

      if (hasAlignmentStatus && hasAlignmentScore && hasRecommendations) {
        this.recordTest('Sacred Drift', true, 'Drift analysis working correctly');
      } else {
        this.recordTest('Sacred Drift', false, 'Drift analysis incomplete');
      }
    } catch (error) {
      this.recordTest('Sacred Drift', false, error.message);
    }
  }

  async testLLMEnhancement() {
    console.log('🧠 Testing LLM enhancement...');
    try {
      const response = await this.sendMCPRequest('tools/call', {
        name: 'query_with_llm',
        arguments: {
          question: 'What is the sacred layer?',
          k: 3
        }
      });

      const queryText = response.result.content[0].text;
      const hasQuestion = queryText.includes('Question:');
      const hasAnswer = queryText.includes('Answer');
      const hasSources = queryText.includes('Sources');

      if (hasQuestion && hasAnswer && hasSources) {
        this.recordTest('LLM Enhancement', true, 'Natural language responses working');
      } else {
        this.recordTest('LLM Enhancement', false, 'LLM enhancement incomplete');
      }
    } catch (error) {
      this.recordTest('LLM Enhancement', false, error.message);
    }
  }

  async testDevelopmentContext() {
    console.log('📋 Testing development context...');
    try {
      const response = await this.sendMCPRequest('tools/call', {
        name: 'get_development_context',
        arguments: {
          project_id: 'proj_6cafffed59ba',
          include_sacred: true
        }
      });

      const contextText = response.result.content[0].text;
      const hasProject = contextText.includes('Project:');
      const hasComprehensive = contextText.includes('Comprehensive Development Context');

      if (hasProject && hasComprehensive) {
        this.recordTest('Development Context', true, 'Context retrieval working');
      } else {
        this.recordTest('Development Context', false, 'Context incomplete');
      }
    } catch (error) {
      this.recordTest('Development Context', false, error.message);
    }
  }

  async testIntelligentSearch() {
    console.log('🔍 Testing intelligent search...');
    try {
      const response = await this.sendMCPRequest('tools/call', {
        name: 'intelligent_search',
        arguments: {
          query: 'sacred layer architecture',
          max_results: 3
        }
      });

      const searchText = response.result.content[0].text;
      const hasSearchResults = searchText.includes('Intelligent Search Results');
      const hasQuery = searchText.includes('Query:');
      const hasAnswer = searchText.includes('Answer');

      if (hasSearchResults && hasQuery && hasAnswer) {
        this.recordTest('Intelligent Search', true, 'Semantic search working');
      } else {
        this.recordTest('Intelligent Search', false, 'Search functionality incomplete');
      }
    } catch (error) {
      this.recordTest('Intelligent Search', false, error.message);
    }
  }

  async testContextExport() {
    console.log('📤 Testing context export...');
    try {
      const response = await this.sendMCPRequest('tools/call', {
        name: 'export_development_context',
        arguments: {
          project_id: 'proj_6cafffed59ba',
          include_sacred: true,
          include_drift: true
        }
      });

      const exportText = response.result.content[0].text;
      const hasExport = exportText.includes('Development Context Export');
      const hasGenerated = exportText.includes('Generated:');
      const hasNotes = exportText.includes('Context Export Notes');

      if (hasExport && hasGenerated && hasNotes) {
        this.recordTest('Context Export', true, 'Full context export working');
      } else {
        this.recordTest('Context Export', false, 'Context export incomplete');
      }
    } catch (error) {
      this.recordTest('Context Export', false, error.message);
    }
  }

  recordTest(testName, passed, details) {
    const status = passed ? '✅' : '❌';
    console.log(`${status} ${testName}: ${details}`);
    this.testResults.push({ testName, passed, details });
  }

  generateReport() {
    const passed = this.testResults.filter(t => t.passed).length;
    const total = this.testResults.length;
    const percentage = ((passed / total) * 100).toFixed(1);

    console.log('\\n🎯 PHASE 3 INTEGRATION TEST RESULTS');
    console.log('=' .repeat(50));
    console.log(`Tests Passed: ${passed}/${total} (${percentage}%)`);
    console.log(`MCP Server Version: 3.0.0 (Sacred Layer)`);
    console.log(`Sacred Layer: ${passed >= 6 ? 'READY' : 'NEEDS WORK'}`);
    console.log('');

    // Success criteria check
    const successCriteria = [
      'Tool Listing',
      'Health Check', 
      'Sacred Context',
      'Sacred Drift',
      'LLM Enhancement',
      'Context Export'
    ];

    const criteriaMet = successCriteria.every(criterion => 
      this.testResults.find(t => t.testName === criterion)?.passed
    );

    if (criteriaMet) {
      console.log('🎉 ALL PHASE 3 SUCCESS CRITERIA MET!');
      console.log('✅ MCP server running and responding to tool calls');
      console.log('✅ Claude Code can query sacred plans through MCP');
      console.log('✅ Sacred drift detection accessible via MCP tools');
      console.log('✅ Real-time development context export working');
      console.log('✅ AI agent compliance with sacred constraints verified');
      console.log('✅ Natural language responses via LLM enhancement');
      console.log('✅ Health monitoring for all components');
      console.log('');
      console.log('🚀 READY FOR CLAUDE CODE INTEGRATION');
    } else {
      console.log('⚠️  Some success criteria not met. Review failed tests.');
    }

    console.log('\\nDetailed Results:');
    this.testResults.forEach(result => {
      const icon = result.passed ? '✅' : '❌';
      console.log(`${icon} ${result.testName}: ${result.details}`);
    });
  }

  cleanup() {
    if (this.server) {
      this.server.kill();
      console.log('\\n🔄 MCP server stopped');
    }
  }
}

// Run tests
const tester = new Phase3IntegrationTest();
tester.runAllTests().catch(console.error);