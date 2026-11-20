# Harbor Supply Co | FY2023 gross-margin review

**For the controller / finance manager** · Fictional ERP case · Draft for review  
Calendar years ended December 31, 2023 and 2022 · CAD, excluding tax · Posting-date basis

## Margin fell despite higher gross profit

Gross margin fell **3.60 percentage points (pp), from 38.46% to 34.86%**. Net sales rose **$809,878.14 (+15.5%)** to **$6,040,119.44**, but net cost of goods sold (COGS) rose faster: **$715,694.74 (+22.2%)** to **$3,934,570.83**. Gross profit still increased **$94,183.40 (+4.7%)** to **$2,105,548.61**.

**Start with Electrical supplies.** Its margin fell **8.00 pp** (35.09% to 27.08%), contributing **−1.82 pp** to company margin—about half the decline. Category sales rose **$251,010.09**, but COGS rose **$288,849.48**, reducing gross profit by **$37,839.39**. Across all five categories, lower margins within categories accounted for **−3.45 pp** and the change in sales mix for **−0.15 pp**. All five category margins fell.

## What the ERP supports

- **Electrical unit costs grew faster than sales per unit.** Net COGS per net unit rose **22.6%** ($50.23 to $61.59), versus **9.2%** for net sales per net unit ($77.38 to $84.46). Weighted receipt value per unit rose **26.1%** ($50.34 to $63.48); the eight individual Electrical SKUs each rose **19.8%–22.8%**. These observations support a purchase-cost review, but receipt values do not tie directly to issued COGS. Product mix, timing and warehouse cost layers can affect the comparisons; the ERP does not establish why costs or realized prices changed.
- **Discounts and credits add context, but do not explain the size of the decline.** Invoice discounts were **2.510%** of list-price sales in FY2022 and **2.489%** in FY2023. Posted credits rose **$6,287.24**; after cost reversals, their reduction of gross profit increased **$2,489.66**. The 27 FY2023 notes labelled “Electrical supplier quality campaign” recorded **$6,772.66** in credits and **$4,897.59** in cost reversals. Their lines span all five categories; the label does not establish a quality cause or supplier recovery status.

## Ledger tie and next actions

**CAD $0.00 difference in both years:** GL 4000 tied to invoice headers and lines; GL 4100 tied to posted credit-note headers and lines; GL 5000 tied to issued costs less returned costs. List-price sales are before invoice discounts; GL 4000 reflects invoiced sales **after discounts but before credit notes**. Net sales deduct those credits. The P&L excludes year-end closes. GL 5100 inventory count adjustments are separate ($1,746.93 in FY2022; $2,360.20 in FY2023); including them would not change the direction of the margin decline.

| Suggested owner | Follow-up |
| --- | --- |
| Procurement + Inventory | Trace Electrical receipt price changes to supplier bills by SKU and check issue-cost layers by warehouse. |
| Sales / Pricing | Compare Electrical price-update dates, contract exceptions and discounts with realized sales per unit. |
| Credit / Quality | Confirm the campaign credit coding across categories and establish whether supplier claims are open or recovered. |
| Controller | Confirm whether GL 5100 belongs in management gross margin. |

**Review trail:** `harbor_margin_review.xlsx` (Summary, GL Reconciliation, Category Bridge, SKU Detail and Credits); `harbor_margin_queries.sql` (Q01–Q08), rerun against the read-only SQLite extract from `erp-agent-inputs.zip`.
