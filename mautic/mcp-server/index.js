#!/usr/bin/env node

/**
 * Mautic MCP Server
 * 
 * A Model Context Protocol server for Mautic marketing automation.
 * Uses HTTP Basic Auth for authentication.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

// Environment configuration
const MAUTIC_BASE_URL = process.env.MAUTIC_BASE_URL || "http://localhost:8080/api";
const MAUTIC_USERNAME = process.env.MAUTIC_USERNAME;
const MAUTIC_PASSWORD = process.env.MAUTIC_PASSWORD;

if (!MAUTIC_USERNAME || !MAUTIC_PASSWORD) {
  console.error("Error: MAUTIC_USERNAME and MAUTIC_PASSWORD environment variables are required");
  process.exit(1);
}

// Create Basic Auth header
const basicAuth = "Basic " + Buffer.from(`${MAUTIC_USERNAME}:${MAUTIC_PASSWORD}`).toString("base64");

// API client
async function mauticRequest(endpoint, options = {}) {
  const url = `${MAUTIC_BASE_URL.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Authorization": basicAuth,
      "Content-Type": "application/json",
      "Accept": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  // Handle empty responses
  const contentLength = response.headers.get("content-length");
  if (contentLength === "0" || response.status === 204) {
    return null;
  }

  return response.json();
}

// Tool definitions
const TOOLS = [
  {
    name: "search_contacts",
    description: "Search contacts in Mautic with optional filters",
    inputSchema: {
      type: "object",
      properties: {
        search: { type: "string", description: "Search term (name, email, etc.)" },
        limit: { type: "number", description: "Maximum results (default: 20)" },
        start: { type: "number", description: "Pagination offset" },
      },
    },
  },
  {
    name: "get_contact",
    description: "Get a single contact by ID",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "number", description: "Contact ID" },
      },
      required: ["id"],
    },
  },
  {
    name: "create_contact",
    description: "Create a new contact",
    inputSchema: {
      type: "object",
      properties: {
        email: { type: "string", description: "Email address (required)" },
        firstname: { type: "string", description: "First name" },
        lastname: { type: "string", description: "Last name" },
        company: { type: "string", description: "Company name" },
        phone: { type: "string", description: "Phone number" },
        tags: { type: "string", description: "Comma-separated tags" },
        custom: { type: "object", description: "Additional custom fields" },
      },
      required: ["email"],
    },
  },
  {
    name: "update_contact",
    description: "Update an existing contact",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "number", description: "Contact ID" },
        email: { type: "string" },
        firstname: { type: "string" },
        lastname: { type: "string" },
        company: { type: "string" },
        phone: { type: "string" },
        tags: { type: "string" },
        custom: { type: "object", description: "Additional custom fields" },
      },
      required: ["id"],
    },
  },
  {
    name: "delete_contact",
    description: "Delete a contact by ID",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "number", description: "Contact ID" },
      },
      required: ["id"],
    },
  },
  {
    name: "list_companies",
    description: "List companies in Mautic",
    inputSchema: {
      type: "object",
      properties: {
        search: { type: "string", description: "Search term" },
        limit: { type: "number", description: "Maximum results (default: 20)" },
      },
    },
  },
  {
    name: "get_company",
    description: "Get a company by ID",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "number", description: "Company ID" },
      },
      required: ["id"],
    },
  },
  {
    name: "create_company",
    description: "Create a new company",
    inputSchema: {
      type: "object",
      properties: {
        companyname: { type: "string", description: "Company name (required)" },
        companyemail: { type: "string", description: "Company email" },
        companyphone: { type: "string", description: "Phone number" },
        companywebsite: { type: "string", description: "Website URL" },
        companyaddress1: { type: "string", description: "Address line 1" },
        companycity: { type: "string", description: "City" },
        companystate: { type: "string", description: "State/Province" },
        companyzipcode: { type: "string", description: "ZIP/Postal code" },
        companycountry: { type: "string", description: "Country" },
      },
      required: ["companyname"],
    },
  },
  {
    name: "list_campaigns",
    description: "List all campaigns",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", description: "Maximum results (default: 20)" },
      },
    },
  },
  {
    name: "get_campaign",
    description: "Get campaign details by ID",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "number", description: "Campaign ID" },
      },
      required: ["id"],
    },
  },
  {
    name: "add_contact_to_campaign",
    description: "Add a contact to a campaign",
    inputSchema: {
      type: "object",
      properties: {
        campaignId: { type: "number", description: "Campaign ID" },
        contactId: { type: "number", description: "Contact ID" },
      },
      required: ["campaignId", "contactId"],
    },
  },
  {
    name: "list_segments",
    description: "List contact segments",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", description: "Maximum results (default: 20)" },
      },
    },
  },
  {
    name: "get_segment_contacts",
    description: "Get contacts in a segment",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "number", description: "Segment ID" },
        limit: { type: "number", description: "Maximum results (default: 20)" },
      },
      required: ["id"],
    },
  },
  {
    name: "add_contact_to_segment",
    description: "Add a contact to a segment",
    inputSchema: {
      type: "object",
      properties: {
        segmentId: { type: "number", description: "Segment ID" },
        contactId: { type: "number", description: "Contact ID" },
      },
      required: ["segmentId", "contactId"],
    },
  },
  {
    name: "list_forms",
    description: "List all forms",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", description: "Maximum results (default: 20)" },
      },
    },
  },
  {
    name: "get_form",
    description: "Get form details by ID",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "number", description: "Form ID" },
      },
      required: ["id"],
    },
  },
  {
    name: "list_emails",
    description: "List emails",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", description: "Maximum results (default: 20)" },
      },
    },
  },
  {
    name: "get_email",
    description: "Get email details by ID",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "number", description: "Email ID" },
      },
      required: ["id"],
    },
  },
  {
    name: "send_email_to_contact",
    description: "Send an email to a specific contact",
    inputSchema: {
      type: "object",
      properties: {
        emailId: { type: "number", description: "Email ID" },
        contactId: { type: "number", description: "Contact ID" },
      },
      required: ["emailId", "contactId"],
    },
  },
];

// Tool handlers
const HANDLERS = {
  async search_contacts(args) {
    const params = new URLSearchParams();
    if (args.search) params.append("search", args.search);
    if (args.limit) params.append("limit", String(args.limit));
    if (args.start) params.append("start", String(args.start));
    
    const data = await mauticRequest(`/contacts?${params.toString()}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async get_contact(args) {
    const data = await mauticRequest(`/contacts/${args.id}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async create_contact(args) {
    const contactData = {
      email: args.email,
      firstname: args.firstname,
      lastname: args.lastname,
      company: args.company,
      phone: args.phone,
      tags: args.tags,
      ...args.custom,
    };

    const data = await mauticRequest("/contacts/new", {
      method: "POST",
      body: JSON.stringify(contactData),
    });
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async update_contact(args) {
    const { id, ...updateData } = args;
    const data = await mauticRequest(`/contacts/${id}/edit`, {
      method: "PATCH",
      body: JSON.stringify(updateData),
    });
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async delete_contact(args) {
    await mauticRequest(`/contacts/${args.id}/delete`, { method: "DELETE" });
    return {
      content: [{ type: "text", text: `Contact ${args.id} deleted successfully` }],
    };
  },

  async list_companies(args) {
    const params = new URLSearchParams();
    if (args.search) params.append("search", args.search);
    if (args.limit) params.append("limit", String(args.limit));
    
    const data = await mauticRequest(`/companies?${params.toString()}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async get_company(args) {
    const data = await mauticRequest(`/companies/${args.id}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async create_company(args) {
    const data = await mauticRequest("/companies/new", {
      method: "POST",
      body: JSON.stringify(args),
    });
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async list_campaigns(args) {
    const params = new URLSearchParams();
    if (args.limit) params.append("limit", String(args.limit));
    
    const data = await mauticRequest(`/campaigns?${params.toString()}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async get_campaign(args) {
    const data = await mauticRequest(`/campaigns/${args.id}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async add_contact_to_campaign(args) {
    const data = await mauticRequest(`/campaigns/${args.campaignId}/contact/${args.contactId}/add`, {
      method: "POST",
    });
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async list_segments(args) {
    const params = new URLSearchParams();
    if (args.limit) params.append("limit", String(args.limit));
    
    const data = await mauticRequest(`/segments?${params.toString()}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async get_segment_contacts(args) {
    const params = new URLSearchParams();
    if (args.limit) params.append("limit", String(args.limit));
    
    const data = await mauticRequest(`/segments/${args.id}/contacts?${params.toString()}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async add_contact_to_segment(args) {
    const data = await mauticRequest(`/segments/${args.segmentId}/contact/${args.contactId}/add`, {
      method: "POST",
    });
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async list_forms(args) {
    const params = new URLSearchParams();
    if (args.limit) params.append("limit", String(args.limit));
    
    const data = await mauticRequest(`/forms?${params.toString()}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async get_form(args) {
    const data = await mauticRequest(`/forms/${args.id}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async list_emails(args) {
    const params = new URLSearchParams();
    if (args.limit) params.append("limit", String(args.limit));
    
    const data = await mauticRequest(`/emails?${params.toString()}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async get_email(args) {
    const data = await mauticRequest(`/emails/${args.id}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },

  async send_email_to_contact(args) {
    const data = await mauticRequest(`/emails/${args.emailId}/send/contact/${args.contactId}`, {
      method: "POST",
    });
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  },
};

// Server setup
const server = new Server(
  {
    name: "mautic-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS,
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  const handler = HANDLERS[name];
  if (!handler) {
    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
  }

  try {
    return await handler(args || {});
  } catch (error) {
    console.error(`Error in ${name}:`, error);
    throw new McpError(
      ErrorCode.InternalError,
      `Error executing ${name}: ${error.message}`
    );
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("Mautic MCP Server running on stdio");
