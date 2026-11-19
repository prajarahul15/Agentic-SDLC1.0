---
name: contract-design
description: Use when planning any interface between lanes or with existing consumers - REST endpoints, database schema changes and shared frontend types - so implementers can work in parallel. Planner only.
---

# Contract design

A contract is the agreement that lets the Python, Postgres and React implementers work at the same time
without talking to each other. Define it completely before any task starts.

## When a contract is needed
- A new or changed REST endpoint.
- A new or changed table, column, index or constraint.
- A TypeScript type that mirrors an API payload.
- Any change to something existing code already consumes (check the impact analysis).

## Formats
### REST - OpenAPI 3 snippet
```yaml
paths:
  /orders/{orderId}/status:
    patch:
      summary: Change order status
      security: [{ bearerAuth: [] }]
      parameters:
        - { name: orderId, in: path, required: true, schema: { type: integer } }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/OrderStatusUpdate' }
      responses:
        '200': { description: Updated, content: { application/json: { schema: { $ref: '#/components/schemas/OrderOut' } } } }
        '404': { description: Order not found }
        '409': { description: Transition not allowed }
        '422': { description: Validation error }
components:
  schemas:
    OrderStatusUpdate:
      type: object
      required: [status]
      properties:
        status: { type: string, enum: [NEW, PAID, SHIPPED, CANCELLED] }
```
Always include: path, method, auth, every request field with type and required flag, every response code the change introduces, and the error body shape the repo already uses.

### Database - SQL DDL plus migration notes
```sql
ALTER TABLE orders ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'NEW';
CREATE INDEX ix_orders_status ON orders (status);
```
Migration notes (required for changes to existing tables):
- Migration tool and file naming (from the repo context).
- Expand / contract: add new structures first; remove old ones only in a later release.
- Defaults and backfill for existing rows.
- Lock risk on large tables (prefer nullable or defaulted columns, create indexes concurrently where the tool allows).
- Rollback: the downgrade step.

### Frontend - TypeScript interfaces mirroring the API
```ts
export type OrderStatus = 'NEW' | 'PAID' | 'SHIPPED' | 'CANCELLED';
export interface OrderStatusUpdate { status: OrderStatus }
```
Names and fields must match the OpenAPI schema exactly.

## Rules
- Follow the repo's existing naming, error format, pagination and auth patterns. Name the file you copied the pattern from.
- Mark each contract `new`, `backward compatible` or `breaking`. A breaking change needs a question to the user unless the request explicitly asks for it.
- One contract per interface, with an ID (`C1`, …), a producing task and its consuming tasks.
- If an external API is involved and its contract is not known, put it in `research_needed`. Never invent it.
