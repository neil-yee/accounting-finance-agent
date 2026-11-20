-- Harbor Supply Co FY2022 vs FY2023 gross margin investigation
-- READ-ONLY SELECT queries; source connection uses SQLite URI mode=ro.
-- All amounts are integer CAD cents. Periods use posting_date in FY calendar years.

-- @Q00 Source identity and metadata
SELECT key, value
FROM dataset_metadata
ORDER BY key;

-- @Q01 General-ledger P&L accounts (year-end close excluded per source README)
SELECT substr(j.posting_date,1,4) AS fiscal_year,
       a.account_code, a.account_name,
       SUM(l.debit_cents) AS debit_cents,
       SUM(l.credit_cents) AS credit_cents,
       SUM(l.debit_cents-l.credit_cents) AS debit_net_cents,
       COUNT(DISTINCT j.journal_entry_id) AS journal_count,
       COUNT(l.journal_line_id) AS journal_line_count
FROM journal_lines l
JOIN journal_entries j USING (journal_entry_id)
JOIN gl_accounts a USING (account_id)
WHERE j.posting_date >= '2022-01-01'
  AND j.posting_date <  '2024-01-01'
  AND j.entry_type <> 'year_end_close'
  AND a.account_code IN ('4000','4100','5000','5100')
GROUP BY fiscal_year, a.account_code, a.account_name
ORDER BY fiscal_year, a.account_code;

-- @Q02 Sales invoices: header-to-line tie and source totals by posting year
WITH ih AS (
    SELECT substr(posting_date,1,4) AS fiscal_year,
           COUNT(*) AS invoice_count,
           SUM(net_cents) AS invoice_header_net_cents
    FROM sales_invoices
    WHERE posting_date >= '2022-01-01' AND posting_date < '2024-01-01'
    GROUP BY substr(posting_date,1,4)
), il AS (
    SELECT substr(i.posting_date,1,4) AS fiscal_year,
           COUNT(l.invoice_line_id) AS invoice_line_count,
           SUM(l.net_cents) AS invoice_line_net_cents,
           SUM(l.quantity*l.unit_price_cents) AS list_value_cents,
           SUM(l.discount_cents) AS discount_cents,
           SUM(l.cost_cents) AS issued_cost_cents,
           SUM(l.quantity) AS invoiced_units
    FROM sales_invoices i
    JOIN sales_invoice_lines l USING (invoice_id)
    WHERE i.posting_date >= '2022-01-01' AND i.posting_date < '2024-01-01'
    GROUP BY substr(i.posting_date,1,4)
)
SELECT ih.fiscal_year, ih.invoice_count, il.invoice_line_count,
       ih.invoice_header_net_cents, il.invoice_line_net_cents,
       il.list_value_cents, il.discount_cents, il.issued_cost_cents,
       il.invoiced_units
FROM ih JOIN il USING (fiscal_year)
ORDER BY ih.fiscal_year;

-- @Q03 Credit notes by year/type/reason; header totals are not multiplied by line joins
WITH ch AS (
    SELECT credit_note_id, substr(posting_date,1,4) AS fiscal_year,
           credit_type, reason, net_cents AS header_net_cents
    FROM credit_notes
    WHERE posting_date >= '2022-01-01' AND posting_date < '2024-01-01'
), cl AS (
    SELECT credit_note_id, COUNT(*) AS credit_line_count,
           SUM(net_cents) AS credit_line_net_cents,
           SUM(CASE WHEN quantity_returned > 0 THEN quantity_returned ELSE 0 END) AS returned_units,
           SUM(cost_reversed_cents) AS cost_reversed_cents
    FROM credit_note_lines
    GROUP BY credit_note_id
)
SELECT ch.fiscal_year, ch.credit_type, ch.reason,
       COUNT(*) AS credit_note_count,
       SUM(ch.header_net_cents) AS credit_header_net_cents,
       SUM(cl.credit_line_net_cents) AS credit_line_net_cents,
       SUM(cl.credit_line_count) AS credit_line_count,
       SUM(cl.returned_units) AS returned_units,
       SUM(cl.cost_reversed_cents) AS cost_reversed_cents
FROM ch JOIN cl USING (credit_note_id)
GROUP BY ch.fiscal_year, ch.credit_type, ch.reason
ORDER BY ch.fiscal_year, ch.credit_type, ch.reason;

-- @Q04 Category-level revenue, COGS, quantity, and discounts net of credit notes
WITH inv AS (
    SELECT substr(i.posting_date,1,4) AS fiscal_year,
           pc.name AS category,
           SUM(l.net_cents) AS invoice_net_cents,
           SUM(l.cost_cents) AS issued_cost_cents,
           SUM(l.quantity) AS invoiced_units,
           SUM(l.quantity*l.unit_price_cents) AS list_value_cents,
           SUM(l.discount_cents) AS discount_cents,
           COUNT(*) AS invoice_line_count
    FROM sales_invoices i
    JOIN sales_invoice_lines l USING (invoice_id)
    JOIN products p USING (product_id)
    JOIN product_categories pc USING (category_id)
    WHERE i.posting_date >= '2022-01-01' AND i.posting_date < '2024-01-01'
    GROUP BY substr(i.posting_date,1,4), pc.name
), cr AS (
    SELECT substr(c.posting_date,1,4) AS fiscal_year,
           pc.name AS category,
           SUM(cl.net_cents) AS credit_net_cents,
           SUM(cl.cost_reversed_cents) AS cost_reversed_cents,
           SUM(CASE WHEN c.credit_type='return' THEN cl.quantity_returned ELSE 0 END) AS returned_units,
           SUM(CASE WHEN c.credit_type='return' THEN cl.net_cents ELSE 0 END) AS return_net_cents,
           SUM(CASE WHEN c.credit_type='price_allowance' THEN cl.net_cents ELSE 0 END) AS allowance_net_cents
    FROM credit_notes c
    JOIN credit_note_lines cl USING (credit_note_id)
    JOIN sales_invoice_lines il USING (invoice_line_id)
    JOIN products p USING (product_id)
    JOIN product_categories pc USING (category_id)
    WHERE c.posting_date >= '2022-01-01' AND c.posting_date < '2024-01-01'
    GROUP BY substr(c.posting_date,1,4), pc.name
)
SELECT inv.fiscal_year, inv.category, inv.invoice_net_cents,
       COALESCE(cr.credit_net_cents,0) AS credit_net_cents,
       inv.invoice_net_cents-COALESCE(cr.credit_net_cents,0) AS net_sales_cents,
       inv.issued_cost_cents,
       COALESCE(cr.cost_reversed_cents,0) AS cost_reversed_cents,
       inv.issued_cost_cents-COALESCE(cr.cost_reversed_cents,0) AS net_cogs_cents,
       inv.invoiced_units-COALESCE(cr.returned_units,0) AS net_units,
       inv.list_value_cents, inv.discount_cents, inv.invoice_line_count,
       COALESCE(cr.return_net_cents,0) AS return_net_cents,
       COALESCE(cr.allowance_net_cents,0) AS allowance_net_cents
FROM inv LEFT JOIN cr USING (fiscal_year, category)
ORDER BY inv.category, inv.fiscal_year;

-- @Q05 Product/SKU-level revenue, COGS, units, and credit adjustments
WITH inv AS (
    SELECT substr(i.posting_date,1,4) AS fiscal_year,
           p.product_id, p.sku, p.name AS product, pc.name AS category,
           SUM(l.net_cents) AS invoice_net_cents,
           SUM(l.cost_cents) AS issued_cost_cents,
           SUM(l.quantity) AS invoiced_units,
           SUM(l.quantity*l.unit_price_cents) AS list_value_cents,
           SUM(l.discount_cents) AS discount_cents,
           COUNT(*) AS invoice_line_count
    FROM sales_invoices i
    JOIN sales_invoice_lines l USING (invoice_id)
    JOIN products p USING (product_id)
    JOIN product_categories pc USING (category_id)
    WHERE i.posting_date >= '2022-01-01' AND i.posting_date < '2024-01-01'
    GROUP BY substr(i.posting_date,1,4), p.product_id, p.sku, p.name, pc.name
), cr AS (
    SELECT substr(c.posting_date,1,4) AS fiscal_year,
           il.product_id,
           SUM(cl.net_cents) AS credit_net_cents,
           SUM(cl.cost_reversed_cents) AS cost_reversed_cents,
           SUM(CASE WHEN c.credit_type='return' THEN cl.quantity_returned ELSE 0 END) AS returned_units
    FROM credit_notes c
    JOIN credit_note_lines cl USING (credit_note_id)
    JOIN sales_invoice_lines il USING (invoice_line_id)
    WHERE c.posting_date >= '2022-01-01' AND c.posting_date < '2024-01-01'
    GROUP BY substr(c.posting_date,1,4), il.product_id
)
SELECT inv.fiscal_year, inv.product_id, inv.sku, inv.product, inv.category,
       inv.invoice_net_cents, COALESCE(cr.credit_net_cents,0) AS credit_net_cents,
       inv.invoice_net_cents-COALESCE(cr.credit_net_cents,0) AS net_sales_cents,
       inv.issued_cost_cents, COALESCE(cr.cost_reversed_cents,0) AS cost_reversed_cents,
       inv.issued_cost_cents-COALESCE(cr.cost_reversed_cents,0) AS net_cogs_cents,
       inv.invoiced_units-COALESCE(cr.returned_units,0) AS net_units,
       inv.list_value_cents, inv.discount_cents, inv.invoice_line_count
FROM inv LEFT JOIN cr USING (fiscal_year, product_id)
ORDER BY inv.category, inv.sku, inv.fiscal_year;

-- @Q06 Goods receipts: weighted average purchase cost per product and posting year
SELECT substr(gr.posting_date,1,4) AS fiscal_year,
       p.product_id, p.sku, p.name AS product, pc.name AS category,
       SUM(gl.quantity_received) AS received_units,
       SUM(gl.value_cents) AS receipt_value_cents,
       COUNT(*) AS receipt_line_count
FROM goods_receipts gr
JOIN goods_receipt_lines gl USING (goods_receipt_id)
JOIN products p USING (product_id)
JOIN product_categories pc USING (category_id)
WHERE gr.posting_date >= '2022-01-01' AND gr.posting_date < '2024-01-01'
GROUP BY substr(gr.posting_date,1,4), p.product_id, p.sku, p.name, pc.name
ORDER BY pc.name, p.sku, fiscal_year;

-- @Q07 Posted credit note register with line-level values aggregated by note
WITH cl AS (
    SELECT credit_note_id,
           COUNT(*) AS credit_line_count,
           SUM(c.net_cents) AS line_net_cents,
           SUM(c.tax_cents) AS line_tax_cents,
           SUM(c.quantity_returned) AS returned_units,
           SUM(c.cost_reversed_cents) AS cost_reversed_cents,
           GROUP_CONCAT(DISTINCT pc.name) AS affected_categories
    FROM credit_note_lines c JOIN sales_invoice_lines il USING (invoice_line_id)
    JOIN products p USING (product_id)
    JOIN product_categories pc USING (category_id)
    GROUP BY credit_note_id
)
SELECT c.credit_note_id, c.credit_number, c.posting_date, c.credit_type, c.reason,
       c.net_cents AS header_net_cents, c.tax_cents AS header_tax_cents,
       cl.credit_line_count, cl.line_net_cents, cl.line_tax_cents,
       cl.returned_units, cl.cost_reversed_cents, cl.affected_categories
FROM credit_notes c JOIN cl USING (credit_note_id)
WHERE c.posting_date >= '2022-01-01' AND c.posting_date < '2024-01-01'
ORDER BY c.posting_date, c.credit_number;

-- @Q08 Journal-entry balancing control by posting year (all posted entries, close included)
SELECT substr(j.posting_date,1,4) AS fiscal_year,
       COUNT(*) AS journal_entry_count,
       SUM(CASE WHEN x.debits_cents <> x.credits_cents THEN 1 ELSE 0 END) AS unbalanced_entry_count,
       SUM(ABS(x.debits_cents-x.credits_cents)) AS absolute_imbalance_cents
FROM journal_entries j
JOIN (
    SELECT journal_entry_id, SUM(debit_cents) AS debits_cents,
           SUM(credit_cents) AS credits_cents
    FROM journal_lines
    GROUP BY journal_entry_id
) x USING (journal_entry_id)
WHERE j.posting_date >= '2022-01-01' AND j.posting_date < '2024-01-01'
GROUP BY substr(j.posting_date,1,4)
ORDER BY fiscal_year;
