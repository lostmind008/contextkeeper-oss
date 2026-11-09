#!/usr/bin/env node

/**
 * Enhanced MCP Server for ContextKeeper
 * Provides advanced development context to Claude Code and other AI assistants
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';

const execAsync = promisify(exec);

const CACHE_TTL_SECONDS = parseInt(process.env.MCP_CACHE_TTL_SECONDS, 10) || 300;
const RAG_AGENT_BASE_URL = process.env.RAG_AGENT_URL || 'http://localhost:5556';

class EnhancedContextKeeperMCP {
  constructor() {
    this.server = new Server(
      {
        name: 'contextkeeper-enhanced',
        version: '2.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    this.cache = new Map();
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          // Project Context Tools
          {
            name: 'get_development_context',
            description: 'Get comprehensive development context including project status, git activity, objectives, decisions, and drift analysis',
            inputSchema: {
              type: 'object',
              properties: {
                project_id: {
                  type: 'string',
                  description: 'Optional project ID. Uses focused project if not provided'
                },
                include_git: {
                  type: 'boolean',
                  description: 'Include git activity analysis (default: true)',
                  default: true
                },
                include_drift: {
                  type: 'boolean',
                  description: 'Include drift analysis (default: true)',
                  default: true
                },
                hours: {
                  type: 'number',
                  description: 'Hours of history to analyze (default: 24)',
                  default: 24
                }
              }
            }
          },
          
          // Intelligent Search
          {
            name: 'intelligent_search',
            description: 'Search with semantic understanding across code, decisions, objectives, and git history',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Natural language search query'
                },
                search_types: {
                  type: 'array',
                  items: {
                    type: 'string',
                    enum: ['code', 'decisions', 'objectives', 'git_activity', 'all']
                  },
                  description: 'Types of content to search (default: all)',
                  default: ['all']
                },
                project_id: {
                  type: 'string',
                  description: 'Optional: limit to specific project'
                },
                max_results: {
                  type: 'number',
                  description: 'Maximum results per type (default: 5)',
                  default: 5
                }
              },
              required: ['query']
            }
          },

          // Git Integration
          {
            name: 'analyze_git_activity',
            description: 'Analyze git activity, uncommitted changes, and branch status',
            inputSchema: {
              type: 'object',
              properties: {
                project_id: {
                  type: 'string',
                  description: 'Project ID to analyze'
                },
                include_uncommitted: {
                  type: 'boolean',
                  description: 'Include uncommitted changes (default: true)',
                  default: true
                },
                include_branches: {
                  type: 'boolean',
                  description: 'Include branch analysis (default: true)',
                  default: true
                }
              }
            }
          },

          // Drift Detection
          {
            name: 'check_development_drift',
            description: 'Analyze if current development aligns with objectives and get recommendations',
            inputSchema: {
              type: 'object',
              properties: {
                project_id: {
                  type: 'string',
                  description: 'Project ID to analyze'
                },
                hours: {
                  type: 'number',
                  description: 'Hours of activity to analyze (default: 24)',
                  default: 24
                },
                include_recommendations: {
                  type: 'boolean',
                  description: 'Include actionable recommendations (default: true)',
                  default: true
                }
              }
            }
          },

          // Project Management
          {
            name: 'manage_objectives',
            description: 'Add, update, or complete project objectives',
            inputSchema: {
              type: 'object',
              properties: {
                action: {
                  type: 'string',
                  enum: ['add', 'complete', 'update', 'list'],
                  description: 'Action to perform'
                },
                project_id: {
                  type: 'string',
                  description: 'Project ID'
                },
                objective_id: {
                  type: 'string',
                  description: 'Objective ID (for complete/update actions)'
                },
                title: {
                  type: 'string',
                  description: 'Objective title (for add/update)'
                },
                description: {
                  type: 'string',
                  description: 'Objective description'
                },
                priority: {
                  type: 'string',
                  enum: ['low', 'medium', 'high'],
                  description: 'Priority level',
                  default: 'medium'
                }
              },
              required: ['action']
            }
          },
          
          // Decision Tracking
          {
            name: 'track_decision',
            description: 'Record an architectural or implementation decision with context',
            inputSchema: {
              type: 'object',
              properties: {
                decision: {
                  type: 'string',
                  description: 'The decision made'
                },
                reasoning: {
                  type: 'string',
                  description: 'Why this decision was made'
                },
                alternatives_considered: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Other options that were considered'
                },
                tags: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Tags for categorization (e.g., architecture, security)',
                  default: []
                },
                project_id: {
                  type: 'string',
                  description: 'Project ID (optional, uses focused project)'
                }
              },
              required: ['decision', 'reasoning']
            }
          },

          // Development Flow
          {
            name: 'suggest_next_action',
            description: 'Get AI-powered suggestions for what to work on next based on objectives and current state',
            inputSchema: {
              type: 'object',
              properties: {
                project_id: {
                  type: 'string',
                  description: 'Project ID'
                },
                consider_blockers: {
                  type: 'boolean',
                  description: 'Consider potential blockers (default: true)',
                  default: true
                }
              }
            }
          },

          // Code Generation Context
          {
            name: 'get_code_context',
            description: 'Get relevant code examples and patterns for implementing a feature',
            inputSchema: {
              type: 'object',
              properties: {
                feature_description: {
                  type: 'string',
                  description: 'What you want to implement'
                },
                project_id: {
                  type: 'string',
                  description: 'Project ID'
                },
                include_similar: {
                  type: 'boolean',
                  description: 'Include similar implementations (default: true)',
                  default: true
                }
              },
              required: ['feature_description']
            }
          },

          // Daily Workflow
          {
            name: 'daily_briefing',
            description: 'Get a comprehensive daily briefing with all projects, objectives, and recommendations',
            inputSchema: {
              type: 'object',
              properties: {
                include_all_projects: {
                  type: 'boolean',
                  description: 'Include all projects, not just active (default: false)',
                  default: false
                }
              }
            }
          }
        ]
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        // Check cache for expensive operations
        const cacheKey = `${name}-${JSON.stringify(args)}`;
        if (this.shouldCache(name) && this.cache.has(cacheKey)) {
          const cached = this.cache.get(cacheKey);
          if (Date.now() - cached.timestamp < CACHE_TTL_SECONDS * 1000) {
            return cached.result;
          }
        }

        let result;
        switch (name) {
          case 'get_development_context':
            result = await this.getDevelopmentContext(args);
            break;
          
          case 'intelligent_search':
            result = await this.intelligentSearch(args);
            break;

          case 'analyze_git_activity':
            result = await this.analyzeGitActivity(args);
            break;

          case 'check_development_drift':
            result = await this.checkDevelopmentDrift(args);
            break;

          case 'manage_objectives':
            result = await this.manageObjectives(args);
            break;

          case 'track_decision':
            result = await this.trackDecision(args);
            break;
          
          case 'suggest_next_action':
            result = await this.suggestNextAction(args);
            break;

          case 'get_code_context':
            result = await this.getCodeContext(args);
            break;

          case 'daily_briefing':
            result = await this.dailyBriefing(args);
            break;
          
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }

        // Cache expensive operations
        if (this.shouldCache(name)) {
          this.cache.set(cacheKey, {
            result,
            timestamp: Date.now()
          });
        }

        return result;
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error.message}`
        );
      }
    });
  }

  shouldCache(toolName) {
    const cacheableTools = [
      'get_development_context',
      'analyze_git_activity',
      'check_development_drift',
      'daily_briefing'
    ];
    return cacheableTools.includes(toolName);
  }

  async ragRequest(endpoint, method = 'GET', data = null) {
    try {
      const options = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (data) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(`${RAG_AGENT_BASE_URL}${endpoint}`, options);
      
      if (!response.ok) {
        throw new Error(`RAG Agent API error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to communicate with ContextKeeper: ${error.message}`
      );
    }
  }

  async getDevelopmentContext(args) {
    const { project_id, include_git = true, include_drift = true, hours = 24 } = args;
    
    // CRITICAL: Require project_id
    let effectiveProjectId = project_id;
    
    if (!effectiveProjectId) {
      // Try focused project as fallback
      try {
        const focusedResponse = await this.ragRequest('/projects/focused', 'GET');
        if (focusedResponse && focusedResponse.project_id) {
          effectiveProjectId = focusedResponse.project_id;
        }
      } catch (error) {
        console.error('Failed to get focused project:', error);
      }
      
      if (!effectiveProjectId) {
        throw new McpError(
          ErrorCode.InvalidParams,
          'Project ID required. No focused project available.'
        );
      }
    }
    
    // Validate project before proceeding
    const validationResponse = await this.ragRequest(
      `/projects/validate/${effectiveProjectId}`, 
      'GET'
    );
    
    if (!validationResponse.valid) {
      throw new McpError(
        ErrorCode.InvalidParams,
        `Project ${effectiveProjectId} is not accessible`
      );
    }
    
    // Get project context
    const context = await this.ragRequest(
      `/projects/${effectiveProjectId}/context`
    );

    let formattedContext = `# Development Context\n\n`;

    if (context.project) {
      formattedContext += `## Project: ${context.project.name}\n`;
      formattedContext += `Status: ${context.project.status}\n`;
      formattedContext += `Last Active: ${this.formatTimeAgo(context.project.last_active)}\n\n`;
    }

    // Add objectives with progress
    if (context.pending_objectives && context.pending_objectives.length > 0) {
      formattedContext += `## Active Objectives (${context.pending_objectives.length})\n`;
      for (const obj of context.pending_objectives) {
        formattedContext += `### ${obj.priority.toUpperCase()}: ${obj.title}\n`;
        if (obj.description) {
          formattedContext += `${obj.description}\n`;
        }
        formattedContext += `Created: ${this.formatTimeAgo(obj.created_at)}\n\n`;
      }
    }

    // Add recent decisions
    if (context.recent_decisions && context.recent_decisions.length > 0) {
      formattedContext += `## Recent Decisions\n`;
      for (const decision of context.recent_decisions.slice(0, 5)) {
        formattedContext += `### ${decision.decision}\n`;
        if (decision.reasoning) {
          formattedContext += `**Reasoning:** ${decision.reasoning}\n`;
        }
        if (decision.tags && decision.tags.length > 0) {
          formattedContext += `**Tags:** ${decision.tags.join(', ')}\n`;
        }
        formattedContext += `*${this.formatTimeAgo(decision.timestamp)}*\n\n`;
      }
    }

    // Add git activity if requested
    if (include_git && effectiveProjectId) {
      try {
        const gitActivity = await this.getGitSummary(effectiveProjectId, hours);
        if (gitActivity) {
          formattedContext += gitActivity;
        }
      } catch (error) {
        console.error('Failed to get git activity:', error);
      }
    }

    // Add drift analysis if requested
    if (include_drift && effectiveProjectId) {
      try {
        const driftAnalysis = await this.ragRequest(`/projects/${effectiveProjectId}/drift?hours=${hours}`);
        if (driftAnalysis.analysis) {
          formattedContext += `## Objective Alignment\n`;
          formattedContext += `**Status:** ${driftAnalysis.analysis.status}\n`;
          formattedContext += `**Alignment Score:** ${(driftAnalysis.analysis.alignment_score * 100).toFixed(0)}%\n\n`;

          if (driftAnalysis.analysis.recommendations) {
            formattedContext += `### Recommendations\n`;
            for (const rec of driftAnalysis.analysis.recommendations) {
              formattedContext += `- ${rec}\n`;
            }
            formattedContext += '\n';
          }
        }
      } catch (error) {
        console.error('Failed to get drift analysis:', error);
      }
    }

    // Add statistics
    formattedContext += `## Project Statistics\n`;
    formattedContext += `- Total Decisions: ${context.statistics?.total_decisions || 0}\n`;
    formattedContext += `- Total Objectives: ${context.statistics?.total_objectives || 0}\n`;
    formattedContext += `- Completed Objectives: ${context.statistics?.completed_objectives || 0}\n`;

    return {
      content: [
        {
          type: 'text',
          text: formattedContext
        }
      ]
    };
  }

  async intelligentSearch(args) {
    const { query, search_types = ['all'], project_id, max_results = 5 } = args;
    
    // CRITICAL: Enforce project context
    let effectiveProjectId = project_id;
    
    if (!effectiveProjectId) {
      // Try to get focused project as fallback
      try {
        const focusedResponse = await this.ragRequest('/projects/focused', 'GET');
        if (focusedResponse && focusedResponse.project_id) {
          effectiveProjectId = focusedResponse.project_id;
          console.log(`Using focused project: ${effectiveProjectId}`);
        }
      } catch (error) {
        console.error('Failed to get focused project:', error);
      }
      
      // If still no project context, fail closed
      if (!effectiveProjectId) {
        throw new McpError(
          ErrorCode.InvalidParams, 
          'No project context available. Please specify project_id or set a focused project.'
        );
      }
    }
    
    // Validate project exists before querying
    try {
      const validationResponse = await this.ragRequest(
        `/projects/validate/${effectiveProjectId}`, 
        'GET'
      );
      
      if (!validationResponse.valid) {
        throw new McpError(
          ErrorCode.InvalidParams,
          `Project ${effectiveProjectId} is not accessible`
        );
      }
    } catch (error) {
      throw new McpError(
        ErrorCode.InvalidParams,
        `Failed to validate project ${effectiveProjectId}: ${error.message}`
      );
    }
    
    // Perform search with enforced project_id
    const searchResults = await this.ragRequest('/query', 'POST', {
      question: query,
      k: max_results * 3,
      project_id: effectiveProjectId  // Always send validated project_id
    });

    if (searchResults.error) {
      throw new McpError(ErrorCode.InternalError, searchResults.error);
    }

    // Log for security audit
    console.log(`Search executed - Project: ${effectiveProjectId}, Query: ${query.substring(0, 50)}...`);

    // Categorize results by type
    const categorized = {
      code: [],
      decisions: [],
      objectives: [],
      git_activity: [],
      other: []
    };

    // Process results...
    if (searchResults.results) {
      for (const result of searchResults.results) {
        const metadata = result.metadata || {};
        const content = result.content || '';
        
        // Categorize based on metadata or content patterns
        if (metadata.type === 'code' || /\.(py|js|ts|java|cpp)$/.test(metadata.file || '')) {
          categorized.code.push(result);
        } else if (content.includes('Decision:') || content.includes('Reasoning:')) {
          categorized.decisions.push(result);
        } else if (content.includes('Objective:') || content.includes('Goal:')) {
          categorized.objectives.push(result);
        } else if (metadata.source === 'git' || content.includes('commit')) {
          categorized.git_activity.push(result);
        } else {
          categorized.other.push(result);
        }
      }
    }

    // Filter by requested search types
    const filteredResults = {};
    if (search_types.includes('all')) {
      filteredResults = categorized;
    } else {
      for (const type of search_types) {
        if (categorized[type]) {
          filteredResults[type] = categorized[type].slice(0, max_results);
        }
      }
    }

    // Format results for display
    let formattedResults = `# Search Results for: "${query}"\n`;
    formattedResults += `**Project**: ${effectiveProjectId}\n\n`;

    for (const [type, results] of Object.entries(filteredResults)) {
      if (results.length > 0) {
        formattedResults += `## ${type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}\n\n`;

        for (const result of results.slice(0, max_results)) {
          if (type === 'code') {
            formattedResults += `### ${result.metadata.file}\n`;
            if (result.metadata.start_line) {
              formattedResults += `Lines ${result.metadata.start_line}-${result.metadata.end_line}\n`;
            }
            formattedResults += `\`\`\`\n${result.content}\n\`\`\`\n\n`;
          } else {
            formattedResults += `### ${result.content.split('\n')[0]}\n`;
            formattedResults += `${result.content}\n\n`;
          }
        }
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: formattedResults
        }
      ]
    };
  }

  async analyzeGitActivity(args) {
    const { project_id, include_uncommitted = true, include_branches = true } = args;
    
    if (!project_id) {
      throw new McpError(ErrorCode.InvalidParams, 'project_id is required');
    }

    // Get project info
    const project = await this.ragRequest(`/projects/${project_id}/context`);
    if (!project.project) {
      throw new McpError(ErrorCode.InvalidParams, 'Project not found');
    }

    const projectPath = project.project.root_path;
    let analysis = `# Git Activity Analysis\n\n`;

    try {
      // Get current branch
      const { stdout: branch } = await execAsync('git branch --show-current', { cwd: projectPath });
      analysis += `## Current Branch: ${branch.trim()}\n\n`;

      // Get recent commits
      const { stdout: commits } = await execAsync(
        'git log --oneline --decorate --graph -10',
        { cwd: projectPath }
      );
      analysis += `## Recent Commits\n\`\`\`\n${commits}\`\`\`\n\n`;

      if (include_uncommitted) {
        // Get uncommitted changes
        const { stdout: status } = await execAsync('git status --short', { cwd: projectPath });
        if (status.trim()) {
          analysis += `## Uncommitted Changes\n\`\`\`\n${status}\`\`\`\n\n`;

          // Get diff summary
          try {
            const { stdout: diff } = await execAsync('git diff --stat', { cwd: projectPath });
            if (diff.trim()) {
              analysis += `## Diff Summary\n\`\`\`\n${diff}\`\`\`\n\n`;
            }
          } catch (error) {
            // No diff is okay
          }
        }
      }

      if (include_branches) {
        // Get all branches
        const { stdout: branches } = await execAsync(
          'git branch -a --format="%(refname:short) (%(committerdate:relative))"',
          { cwd: projectPath }
        );
        analysis += `## All Branches\n\`\`\`\n${branches}\`\`\`\n`;
      }

    } catch (error) {
      analysis += `\n⚠️ Git analysis error: ${error.message}\n`;
    }

    return {
      content: [
        {
          type: 'text',
          text: analysis
        }
      ]
    };
  }

  async checkDevelopmentDrift(args) {
    const { project_id, hours = 24, include_recommendations = true } = args;
    
    if (!project_id) {
      throw new McpError(ErrorCode.InvalidParams, 'project_id is required');
    }

    const driftAnalysis = await this.ragRequest(`/projects/${project_id}/drift?hours=${hours}`);

    if (!driftAnalysis.analysis) {
      return {
        content: [
          {
            type: 'text',
            text: 'No drift analysis available'
          }
        ]
      };
    }

    let report = driftAnalysis.report || `# Drift Analysis\n\n`;
    
    // Add visual representation
    const { alignment_score, status, objective_progress } = driftAnalysis.analysis;
    
    report += `\n## Visual Summary\n`;
    report += this.createProgressBar('Overall Alignment', alignment_score);

    if (objective_progress) {
      report += `\n### Objective Progress\n`;
      for (const [obj, progress] of Object.entries(objective_progress)) {
        report += this.createProgressBar(obj, progress);
      }
    }

    if (!include_recommendations) {
      // Remove recommendations section
      const recIndex = report.indexOf('Recommendations:');
      if (recIndex > -1) {
        report = report.substring(0, recIndex);
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: report
        }
      ]
    };
  }

  async suggestNextAction(args) {
    const { project_id, consider_blockers = true } = args;
    
    // Get project context
    const context = await this.ragRequest(
      project_id ? `/projects/${project_id}/context` : '/context'
    );

    // Get drift analysis
    const driftAnalysis = project_id ?
      await this.ragRequest(`/projects/${project_id}/drift?hours=24`) : null;

    let suggestions = `# Suggested Next Actions\n\n`;

    // Analyze pending objectives
    const pendingObjectives = context.pending_objectives || [];
    const highPriorityObjectives = pendingObjectives.filter(o => o.priority === 'high');
    const lowProgressObjectives = [];

    if (driftAnalysis?.analysis?.objective_progress) {
      for (const [obj, progress] of Object.entries(driftAnalysis.analysis.objective_progress)) {
        if (progress < 0.3) {
          const objective = pendingObjectives.find(o => o.title === obj);
          if (objective) {
            lowProgressObjectives.push(objective);
          }
        }
      }
    }

    // Priority 1: High priority with low progress
    const urgentObjectives = highPriorityObjectives.filter(o =>
      lowProgressObjectives.some(lo => lo.title === o.title)
    );
    
    if (urgentObjectives.length > 0) {
      suggestions += `## 🚨 Urgent: High Priority with Low Progress\n`;
      for (const obj of urgentObjectives) {
        suggestions += `### ${obj.title}\n`;
        suggestions += `${obj.description || 'No description'}\n`;
        suggestions += `**Why now:** High priority objective with minimal progress\n\n`;
      }
    }

    // Priority 2: Low progress objectives
    if (lowProgressObjectives.length > 0 && urgentObjectives.length === 0) {
      suggestions += `## 📊 Focus Needed: Low Progress Objectives\n`;
      for (const obj of lowProgressObjectives.slice(0, 3)) {
        suggestions += `### ${obj.title}\n`;
        suggestions += `${obj.description || 'No description'}\n`;
        suggestions += `**Priority:** ${obj.priority}\n\n`;
      }
    }

    // Priority 3: Continue current momentum
    if (driftAnalysis?.analysis?.aligned_count > 0) {
      suggestions += `## ✅ Continue Current Work\n`;
      suggestions += `Your recent activity aligns well with objectives. `;
      suggestions += `Consider continuing your current approach.\n\n`;
    }

    // Consider blockers
    if (consider_blockers) {
      // Check for uncommitted changes
      try {
        const gitStatus = await this.analyzeGitActivity({
          project_id,
          include_uncommitted: true,
          include_branches: false
        });

        if (gitStatus.content[0].text.includes('Uncommitted Changes')) {
          suggestions += `## ⚠️ Potential Blocker: Uncommitted Changes\n`;
          suggestions += `You have uncommitted changes. Consider:\n`;
          suggestions += `- Review and commit current changes\n`;
          suggestions += `- Stash changes if switching context\n\n`;
        }
      } catch (error) {
        // Git check failed, not critical
      }
    }

    // Add decision points
    if (context.recent_decisions && context.recent_decisions.length > 0) {
      const recentDecision = context.recent_decisions[0];
      suggestions += `## 💡 Recent Decision Context\n`;
      suggestions += `Your recent decision: "${recentDecision.decision}"\n`;
      suggestions += `Consider how your next action aligns with this.\n`;
    }

    return {
      content: [
        {
          type: 'text',
          text: suggestions
        }
      ]
    };
  }

  async manageObjectives(args) {
    const { action, project_id, objective_id, title, description, priority = 'medium' } = args;
    
    if (!action) {
      throw new McpError(ErrorCode.InvalidParams, 'action is required');
    }

    try {
      let result;
      let responseText = `# Objective Management\n\n`;

      switch (action) {
        case 'add':
          if (!title) {
            throw new McpError(ErrorCode.InvalidParams, 'title is required for add action');
          }
          
          result = await this.ragRequest('/objectives', 'POST', {
            project_id,
            title,
            description,
            priority
          });
          
          responseText += `## Objective Added\n`;
          responseText += `**Title**: ${title}\n`;
          responseText += `**Priority**: ${priority}\n`;
          responseText += `**Project**: ${project_id || 'Focused Project'}\n`;
          if (description) {
            responseText += `**Description**: ${description}\n`;
          }
          responseText += `**ID**: ${result.objective_id || 'Generated'}\n`;
          break;

        case 'complete':
          if (!objective_id) {
            throw new McpError(ErrorCode.InvalidParams, 'objective_id is required for complete action');
          }
          
          result = await this.ragRequest(`/objectives/${objective_id}/complete`, 'POST', {
            project_id
          });
          
          responseText += `## Objective Completed\n`;
          responseText += `**ID**: ${objective_id}\n`;
          responseText += `**Status**: Completed\n`;
          responseText += `**Completed At**: ${new Date().toISOString()}\n`;
          break;

        case 'update':
          if (!objective_id) {
            throw new McpError(ErrorCode.InvalidParams, 'objective_id is required for update action');
          }
          
          const updateData = {};
          if (title) updateData.title = title;
          if (description) updateData.description = description;
          if (priority) updateData.priority = priority;
          
          result = await this.ragRequest(`/objectives/${objective_id}`, 'PUT', {
            project_id,
            ...updateData
          });
          
          responseText += `## Objective Updated\n`;
          responseText += `**ID**: ${objective_id}\n`;
          if (title) responseText += `**New Title**: ${title}\n`;
          if (description) responseText += `**New Description**: ${description}\n`;
          if (priority) responseText += `**New Priority**: ${priority}\n`;
          break;

        case 'list':
          result = await this.ragRequest(
            project_id ? `/objectives?project_id=${project_id}` : '/objectives'
          );
          
          responseText += `## Project Objectives\n`;
          responseText += `**Project**: ${project_id || 'All Projects'}\n\n`;
          
          if (result.objectives && result.objectives.length > 0) {
            const pendingObjectives = result.objectives.filter(obj => obj.status === 'pending');
            const completedObjectives = result.objectives.filter(obj => obj.status === 'completed');
            
            if (pendingObjectives.length > 0) {
              responseText += `### Pending Objectives (${pendingObjectives.length})\n`;
              for (const obj of pendingObjectives) {
                responseText += `**${obj.priority.toUpperCase()}**: ${obj.title}\n`;
                if (obj.description) {
                  responseText += `${obj.description}\n`;
                }
                responseText += `*Created: ${this.formatTimeAgo(obj.created_at)}*\n\n`;
              }
            }
            
            if (completedObjectives.length > 0) {
              responseText += `### Completed Objectives (${completedObjectives.length})\n`;
              for (const obj of completedObjectives.slice(0, 5)) {
                responseText += `✅ ${obj.title}\n`;
                responseText += `*Completed: ${this.formatTimeAgo(obj.completed_at)}*\n\n`;
              }
            }
          } else {
            responseText += `No objectives found. Use 'add' action to create new objectives.\n`;
          }
          break;

        default:
          throw new McpError(ErrorCode.InvalidParams, `Unknown action: ${action}`);
      }

      return {
        content: [
          {
            type: 'text',
            text: responseText
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `# Objective Management Error\n\nFailed to ${action} objective: ${error.message}`
          }
        ]
      };
    }
  }

  async getCodeContext(args) {
    const { feature_description, project_id, include_similar = true } = args;
    
    if (!feature_description) {
      throw new McpError(ErrorCode.InvalidParams, 'feature_description is required');
    }

    try {
      // Get relevant code examples and patterns
      const codeContext = await this.ragRequest('/code-context', 'POST', {
        feature_description,
        project_id,
        include_similar,
        k: include_similar ? 10 : 5
      });

      let contextText = `# Code Context for Feature Implementation\n\n`;
      contextText += `**Feature**: ${feature_description}\n`;
      contextText += `**Project**: ${project_id || 'Focused Project'}\n\n`;

      if (codeContext.similar_implementations && codeContext.similar_implementations.length > 0) {
        contextText += `## Similar Implementations Found\n\n`;
        for (const impl of codeContext.similar_implementations) {
          contextText += `### ${impl.file}\n`;
          if (impl.function_name) {
            contextText += `**Function**: \`${impl.function_name}\`\n`;
          }
          if (impl.description) {
            contextText += `**Description**: ${impl.description}\n`;
          }
          contextText += `**Similarity**: ${(impl.similarity * 100).toFixed(0)}%\n`;
          contextText += `\`\`\`${impl.language || ''}\n${impl.code}\n\`\`\`\n\n`;
        }
      }

      if (codeContext.patterns && codeContext.patterns.length > 0) {
        contextText += `## Relevant Patterns\n\n`;
        for (const pattern of codeContext.patterns) {
          contextText += `### ${pattern.name}\n`;
          contextText += `${pattern.description}\n`;
          if (pattern.example) {
            contextText += `\`\`\`${pattern.language || ''}\n${pattern.example}\n\`\`\`\n\n`;
          }
        }
      }

      if (codeContext.dependencies && codeContext.dependencies.length > 0) {
        contextText += `## Related Dependencies\n\n`;
        for (const dep of codeContext.dependencies) {
          contextText += `- **${dep.name}**: ${dep.purpose}\n`;
          if (dep.file) {
            contextText += `  *File*: ${dep.file}\n`;
          }
        }
        contextText += `\n`;
      }

      if (codeContext.recommendations && codeContext.recommendations.length > 0) {
        contextText += `## Implementation Recommendations\n\n`;
        for (const rec of codeContext.recommendations) {
          contextText += `- ${rec}\n`;
        }
        contextText += `\n`;
      }

      // Add architectural guidelines if available
      if (codeContext.architectural_notes) {
        contextText += `## Architectural Guidelines\n\n`;
        contextText += `${codeContext.architectural_notes}\n\n`;
      }

      contextText += `## Next Steps\n`;
      contextText += `1. Review similar implementations above\n`;
      contextText += `2. Adapt patterns to your specific use case\n`;
      contextText += `3. Follow project coding standards\n`;
      contextText += `4. Consider dependencies and integration points\n`;

      return {
        content: [
          {
            type: 'text',
            text: contextText
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `# Code Context Error\n\nFailed to get code context for "${feature_description}": ${error.message}\n\nPlease ensure the feature description is clear and the project context is available.`
          }
        ]
      };
    }
  }

  async dailyBriefing(args) {
    const { include_all_projects = false } = args;

    try {
      // Get comprehensive daily briefing
      const briefing = await this.ragRequest(`/daily-briefing?include_all=${include_all_projects}`);

      let briefingText = `# Daily Development Briefing\n\n`;
      briefingText += `**Generated**: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}\n`;
      briefingText += `**Scope**: ${include_all_projects ? 'All Projects' : 'Active Projects'}\n\n`;

      // Project summaries
      if (briefing.projects && briefing.projects.length > 0) {
        briefingText += `## Project Status (${briefing.projects.length})\n\n`;
        for (const project of briefing.projects) {
          briefingText += `### ${project.name}\n`;
          briefingText += `**Status**: ${project.status}\n`;
          briefingText += `**Last Activity**: ${this.formatTimeAgo(project.last_active)}\n`;
          
          if (project.pending_objectives > 0) {
            briefingText += `**Pending Objectives**: ${project.pending_objectives}\n`;
          }
          
          if (project.recent_decisions > 0) {
            briefingText += `**Recent Decisions**: ${project.recent_decisions}\n`;
          }
          
          if (project.git_status) {
            briefingText += `**Git Status**: ${project.git_status}\n`;
          }
          
          briefingText += `\n`;
        }
      }

      // High priority objectives across all projects
      if (briefing.priority_objectives && briefing.priority_objectives.length > 0) {
        briefingText += `## High Priority Objectives\n\n`;
        for (const obj of briefing.priority_objectives) {
          briefingText += `### ${obj.title}\n`;
          briefingText += `**Project**: ${obj.project_name}\n`;
          briefingText += `**Priority**: ${obj.priority.toUpperCase()}\n`;
          if (obj.description) {
            briefingText += `**Description**: ${obj.description}\n`;
          }
          briefingText += `**Age**: ${this.formatTimeAgo(obj.created_at)}\n\n`;
        }
      }

      // Recent decisions with impact
      if (briefing.recent_decisions && briefing.recent_decisions.length > 0) {
        briefingText += `## Recent Architectural Decisions\n\n`;
        for (const decision of briefing.recent_decisions.slice(0, 5)) {
          briefingText += `### ${decision.decision}\n`;
          briefingText += `**Project**: ${decision.project_name || 'Multiple'}\n`;
          if (decision.reasoning) {
            briefingText += `**Reasoning**: ${decision.reasoning}\n`;
          }
          if (decision.tags && decision.tags.length > 0) {
            briefingText += `**Tags**: ${decision.tags.join(', ')}\n`;
          }
          briefingText += `**When**: ${this.formatTimeAgo(decision.timestamp)}\n\n`;
        }
      }

      // Development recommendations
      if (briefing.recommendations && briefing.recommendations.length > 0) {
        briefingText += `## Today's Recommendations\n\n`;
        for (const rec of briefing.recommendations) {
          briefingText += `${rec.priority === 'high' ? '🚨' : rec.priority === 'medium' ? '⚠️' : 'ℹ️'} ${rec.message}\n`;
          if (rec.project) {
            briefingText += `   *Project: ${rec.project}*\n`;
          }
        }
        briefingText += `\n`;
      }

      // Drift alerts
      if (briefing.drift_alerts && briefing.drift_alerts.length > 0) {
        briefingText += `## Alignment Alerts\n\n`;
        for (const alert of briefing.drift_alerts) {
          briefingText += `⚠️ **${alert.project}**: ${alert.message}\n`;
          briefingText += `   *Alignment Score: ${(alert.score * 100).toFixed(0)}%*\n`;
        }
        briefingText += `\n`;
      }

      // Summary statistics
      if (briefing.statistics) {
        briefingText += `## Development Statistics\n`;
        briefingText += `- **Active Projects**: ${briefing.statistics.active_projects || 0}\n`;
        briefingText += `- **Total Objectives**: ${briefing.statistics.total_objectives || 0}\n`;
        briefingText += `- **Completed This Week**: ${briefing.statistics.completed_this_week || 0}\n`;
        briefingText += `- **Decisions Tracked**: ${briefing.statistics.total_decisions || 0}\n`;
        briefingText += `- **Average Alignment**: ${briefing.statistics.average_alignment ? (briefing.statistics.average_alignment * 100).toFixed(0) + '%' : 'N/A'}\n`;
      }

      return {
        content: [
          {
            type: 'text',
            text: briefingText
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `# Daily Briefing Error\n\nFailed to generate daily briefing: ${error.message}\n\nPlease ensure the ContextKeeper service is running and project data is available.`
          }
        ]
      };
    }
  }

  async trackDecision(args) {
    const { decision, reasoning, alternatives_considered, tags = [], project_id } = args;
    
    try {
      // Add decision via RAG agent
      const result = await this.ragRequest('/decision', 'POST', {
        decision,
        reasoning,
        project_id,
        tags,
        alternatives_considered
      });
      
      let responseText = `# Decision Tracked\n\n`;
      responseText += `**Decision**: ${decision}\n`;
      responseText += `**Project**: ${project_id || 'Focused Project'}\n`;
      
      if (reasoning) {
        responseText += `\n## Reasoning\n${reasoning}\n`;
      }
      
      if (alternatives_considered && alternatives_considered.length > 0) {
        responseText += `\n## Alternatives Considered\n`;
        for (const alt of alternatives_considered) {
          responseText += `- ${alt}\n`;
        }
      }
      
      if (tags && tags.length > 0) {
        responseText += `\n## Tags\n`;
        responseText += `${tags.join(', ')}\n`;
      }
      
      responseText += `\n*Decision tracked at ${new Date().toISOString()}*`;
      
      return {
        content: [
          {
            type: 'text',
            text: responseText
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `# Error Tracking Decision\n\nFailed to track decision: ${error.message}`
          }
        ]
      };
    }
  }

  // Helper methods
  formatTimeAgo(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return 'just now';
  }

  createProgressBar(label, progress) {
    const width = 30;
    const filled = Math.round(progress * width);
    const empty = width - filled;
    const bar = '█'.repeat(filled) + '░'.repeat(empty);
    const percentage = (progress * 100).toFixed(0);
    return `${label}\n[${bar}] ${percentage}%\n\n`;
  }

  async getGitSummary(projectId, hours) {
    // This would integrate with the git activity tracker
    // For now, return a placeholder
    return `## Git Activity (Last ${hours}h)\n*Git integration pending*\n\n`;
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Enhanced ContextKeeper MCP server running on stdio');
  }
}

const server = new EnhancedContextKeeperMCP();
server.run().catch(console.error);