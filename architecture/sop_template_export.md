# 📐 Standard Operating Procedure: Template Export Formatting

**SOP ID:** SOP-002  
**Layer:** Layer 1 (Architecture)  
**Target Tool:** `tools/test_plan_exporter.py`  
**Reference Files:** `Test Plan - Template.docx`, `Inbuilt_Test_Plan_Template.xlsx`

---

## 1. Goal & Objective
Convert the standardized Test Plan JSON payload into publication-ready, professional deliverables matching organizational templates:
1. Microsoft Word Document (`.docx`)
2. Microsoft Excel Workbook (`.xlsx`)
3. GitHub-flavored Markdown (`.md`)

---

## 2. Word Document Formatting Rules (`.docx`)
- **Typography:** Segoe UI or Calibri with distinct heading hierarchy.
- **Title & Metadata:** Title block with Product Name, Jira Project Key, Date, and Author.
- **Section Structure:**
  1. Executive Objective
  2. Scope (Inclusions vs Exclusions)
  3. Test Environments Table
  4. Test Strategy & Automation Approach
  5. Test Cases Table (ID, Jira Key, Title, Type, Priority, Preconditions, Steps, Expected Result)
  6. Entry & Exit Gates
  7. Risks & Mitigations Table
  8. Approvals & Sign-off Table
- **Styling:** Professional corporate styling (Primary accent `#1F4E79`, subtle zebra stripes for tables).

---

## 3. Excel Workbook Formatting Rules (`.xlsx`)
- **Tabs:**
  - `Test Plan Overview`: Metadata, objectives, environment specifications, sign-off blocks.
  - `Test Cases`: Filterable grid with styled header row, wrapped text columns, and color-coded priority.
  - `Risks & Mitigations`: Risk matrices with impact/probability rankings.
- **Template Compatibility:**
  - Inbuilt Mode: Uses pre-designed corporate structure.
  - Custom Mode: Maps generated fields to user-uploaded custom column headers.

---

## 4. Markdown Formatting Rules (`.md`)
- Complete self-contained markdown file for pasting directly into Jira, Confluence, GitHub issues, or Slack.
