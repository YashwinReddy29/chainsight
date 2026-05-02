import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { extractDependencies } from './tools/extract-dependencies.js';
import { checkCVE } from './tools/check-cve.js';
import { classifyLicense } from './tools/classify-license.js';
import { scoreFreshness } from './tools/score-freshness.js';

const server = new Server(
  { name: 'chainsight-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'extract_dependencies',
      description: 'Parse source code to extract all external package dependencies with names, versions, and ecosystems. Also parses DEPENDENCIES blocks from ChainSight Security Auditor mode.',
      inputSchema: {
        type: 'object',
        properties: {
          code: { type: 'string', description: 'Source code to parse' },
          ecosystem: { type: 'string', enum: ['PyPI','npm','Go','Maven','Cargo'], description: 'Force ecosystem (optional, auto-detected if omitted)' }
        },
        required: ['code']
      }
    },
    {
      name: 'check_cve',
      description: 'Query OSV.dev vulnerability database for CVEs. Free API, no key needed. Returns CVE IDs, severity, affected versions, fix recommendations.',
      inputSchema: {
        type: 'object',
        properties: {
          packages: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                name: { type: 'string' },
                version: { type: 'string' },
                ecosystem: { type: 'string' }
              },
              required: ['name', 'ecosystem']
            }
          }
        },
        required: ['packages']
      }
    },
    {
      name: 'classify_license',
      description: 'Look up package license from PyPI or npm registry. Returns SPDX identifier for CycloneDX SBOM.',
      inputSchema: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          version: { type: 'string' },
          ecosystem: { type: 'string' }
        },
        required: ['name', 'ecosystem']
      }
    },
    {
      name: 'score_freshness',
      description: 'THE CORE CHAINSIGHT FEATURE. Identifies Bob blind spots — CVEs published after Bob training cutoff (2024-11-01) that Bob could not know about when generating code.',
      inputSchema: {
        type: 'object',
        properties: {
          cves: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                id: { type: 'string' },
                published: { type: 'string' }
              },
              required: ['id']
            }
          }
        },
        required: ['cves']
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    let result;
    switch (name) {
      case 'extract_dependencies': result = await extractDependencies(args); break;
      case 'check_cve':            result = await checkCVE(args); break;
      case 'classify_license':     result = await classifyLicense(args); break;
      case 'score_freshness':      result = await scoreFreshness(args); break;
      default: throw new Error(`Unknown tool: ${name}`);
    }
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
  } catch (error) {
    return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message, tool: name }, null, 2) }], isError: true };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error('ChainSight MCP Server running on stdio');
console.error('Tools: extract_dependencies, check_cve, classify_license, score_freshness');
