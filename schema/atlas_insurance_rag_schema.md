# Schema: `atlas.atlas_insurance_rag`

_Generated: 2026-07-08 03:30 UTC_

> 19 tables — CREATE TABLE DDL + 10 sample rows each.

---

## `account_intel`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.account_intel (
  insured_id STRING COLLATE UTF8_BINARY NOT NULL,
  authority_granted_date DATE COMMENT 'FMCSA operating authority grant date',
  prior_carrier STRING COLLATE UTF8_BINARY COMMENT 'Expiring / incumbent carrier',
  years_with_prior INT,
  reason_in_market STRING COLLATE UTF8_BINARY COMMENT 'Why the account is shopping',
  operating_radius STRING COLLATE UTF8_BINARY COMMENT 'Local, Intermediate, Long Haul radius band',
  mcs150_current BOOLEAN COMMENT 'MCS-150 biennial update current',
  mcs90_on_file BOOLEAN COMMENT 'BMC/MCS-90 financial responsibility endorsement',
  bmc91_on_file BOOLEAN COMMENT 'BMC-91/91X filing on file',
  oos_vehicle_pct DECIMAL(5,1) COMMENT 'Vehicle out-of-service rate %',
  oos_driver_pct DECIMAL(5,1) COMMENT 'Driver out-of-service rate %',
  national_oos_vehicle_avg DECIMAL(5,1) COMMENT 'National avg vehicle OOS %',
  national_oos_driver_avg DECIMAL(5,1) COMMENT 'National avg driver OOS %',
  crash_rate_per_100 DECIMAL(6,2) COMMENT 'DOT-recordable crashes per 100 power units / yr',
  csa_as_of DATE COMMENT 'FMCSA SMS snapshot date',
  loss_runs_valued DATE COMMENT 'As-of valuation date of loss runs on file',
  CONSTRAINT `pk_account_intel` PRIMARY KEY (`insured_id`))
USING delta
COMMENT 'Underwriting intelligence: authority, filings, market reason, FMCSA SMS posture.'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (6 of 6)

| insured_id | authority_granted_date | prior_carrier                    | years_with_prior | reason_in_market                                            | operating_radius      | mcs150_current | mcs90_on_file | bmc91_on_file | oos_vehicle_pct | oos_driver_pct | national_oos_vehicle_avg | national_oos_driver_avg | crash_rate_per_100 | csa_as_of  | loss_runs_valued |
| ---------- | ---------------------- | -------------------------------- | ---------------- | ----------------------------------------------------------- | --------------------- | -------------- | ------------- | ------------- | --------------- | -------------- | ------------------------ | ----------------------- | ------------------ | ---------- | ---------------- |
| INS-1002   | 2011-04-12             | Golden State Mutual              | 6                | Rate increase at renewal (>20%) — testing the market        | Long Haul (>500 mi)   | True           | True          | True          | 24.8            | 6.1            | 20.7                     | 5.5                     | 3.10               | 2026-06-01 | 2026-05-15       |
| INS-1005   | 2023-02-01             | First-time buyer / new authority | 1                | New venture seeking first commercial auto program           | Local (<100 mi)       | True           | True          | False         | 31.5            | 9.4            | 20.7                     | 5.5                     | 7.80               | 2026-06-01 | 2026-05-20       |
| INS-1006   | 2008-06-01             | Rocky Mountain Casualty          | 7                | Incumbent non-renewing the class — marketing for capacity   | Regional (100-500 mi) | True           | True          | True          | 15.2            | 4.1            | 20.7                     | 5.5                     | 1.90               | 2026-06-01 | 2026-06-01       |
| INS-1007   | 2019-08-15             | Eastern Mutual Group             | 3                | Adverse loss experience — carrier issued non-renewal notice | Regional (100-500 mi) | True           | True          | True          | 28.9            | 7.7            | 20.7                     | 5.5                     | 5.40               | 2026-05-01 | 2026-04-30       |
| INS-1013   | 2026-05-01             | First-time buyer / new authority | 0                | New authority — first commercial auto placement             | Regional (100-500 mi) | True           | True          | False         | 18.0            | 5.0            | 20.7                     | 5.5                     | 2.50               | 2026-06-20 | 2026-06-15       |
| INS-1014   | 2012-05-01             | Southeast Mutual Insurance       | 9                | Long-standing account testing market at renewal             | Long Haul (>500 mi)   | True           | True          | True          | 17.6            | 4.8            | 20.7                     | 5.5                     | 2.20               | 2026-06-01 | 2026-05-25       |

---

## `atlas_insurance_rag_endpoint_payload`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.atlas_insurance_rag_endpoint_payload (
  databricks_request_id STRING COLLATE UTF8_BINARY,
  request_date DATE COMMENT 'The UTC date on which the model serving request was received.',
  client_request_id STRING COLLATE UTF8_BINARY COMMENT 'The user-provided request identifier that can be specified in the model serving request body.',
  request_time TIMESTAMP COMMENT 'The timestamp at which the request is received.',
  status_code INT COMMENT 'The HTTP status code that was returned from the model.',
  sampling_fraction DOUBLE COMMENT 'The sampling fraction used in the event that the request was down-sampled. This value is between 0 and 1, where 1 represents that 100% of incoming requests were included.',
  execution_duration_ms BIGINT COMMENT 'The time in milliseconds for which the model performed inference. This does not include overhead network latencies and only represents the time it took for the model to generate predictions.',
  request STRING COLLATE UTF8_BINARY COMMENT 'The raw request JSON body that was sent to the model serving endpoint.',
  response STRING COLLATE UTF8_BINARY COMMENT 'The raw response JSON body that was returned by the model serving endpoint.',
  logging_error_codes ARRAY<STRING COLLATE UTF8_BINARY> COMMENT 'The errors that occurred when the data could not be logged. Error codes include MAX_REQUEST_SIZE_EXCEEDED and MAX_RESPONSE_SIZE_EXCEEDED.',
  served_entity_id STRING COLLATE UTF8_BINARY COMMENT 'The unique ID of the served entity.',
  requester STRING COLLATE UTF8_BINARY COMMENT 'The ID of the user or service principal whose permissions are used for the invocation request of the serving endpoint. This field returns NULL for route-optimized custom model endpoints.')
USING delta
CLUSTER BY (request_date)
TBLPROPERTIES (
  'delta.checkpointPolicy' = 'v2',
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.feature.v2Checkpoint' = 'supported')

```

### Sample rows (10 of 89)

| databricks_request_id                | request_date | client_request_id | request_time               | status_code | sampling_fraction | execution_duration_ms | request                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | response                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | logging_error_codes | served_entity_id                 | requester                            |
| ------------------------------------ | ------------ | ----------------- | -------------------------- | ----------- | ----------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- | -------------------------------- | ------------------------------------ |
| 58db0e4d-2fc8-4861-976c-bc1228a16642 | 2026-07-04   |                   | 2026-07-04 19:40:26.829000 | 200         | 1.0               | 5798                  | {"extra_params":{"user_role":"underwriter","session_id":"fa4d6ac5-2992-4d75-a578-00bd52a3e2d2"},"messages":[{"content":"Compare to similar accounts","role":"user"},{"content":"Compare to similar accounts","role":"user"}]}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | {"choices": [{"message": {"role": "assistant", "content": "Based on the retrieved submissions, I can provide a comparison with similar accounts that have been processed by Atlas Commercial Insurance:\n\n## Similar Account Comparison\n\n**Common Profile Characteristics:**\n- All three accounts (SUB-26-10826, SUB-25-10259, SUB-25-10357) received **\"Quote\"** recommendations\n- All classified as **\"Preferred/acceptable profile\"** \n- All routed to **Theresa Vandermeer (VP Underwriting, National Accounts)** indicating larger account size\n- All received **\"Satisfactory\"** ratings\n- All approved for **available credits**\n\n**Loss Ratio Performance:**\n- SUB-26-10826: **41% loss ratio**\n- SUB-25-10259: **61% loss ratio** \n- SUB-25-10357: **41% loss ratio**\n\n**Assessment Pattern:**\nAll accounts well below Atlas's 75% loss ratio appetite threshold, with two accounts at the excellent 41% level and one at the good 61% level.\n\n---\n\n## Analysis\n\n**Confidence Level:** 85% (based on available submission summaries)\n\n**Key Observations:**\n1. **Consistent approval pattern** for accounts with loss ratios 41-61%\n2. **National Accounts tier** routing suggests these are substantial fleet operations\n3. **Credit eligibility** indicates strong risk profiles across safety/operations metrics\n\n**Missing Context:**\nTo provide a more comprehensive comparison, I would need:\n- Fleet sizes and commodity types\n- Geographic territories\n- Specific credit types applied\n- Complete risk assessment details\n\nWould you like me to search for additional information about fleet characteristics, commodity types, or specific underwriting criteria for these account types?\n\n*Please verify this information against the source documents in your\ndocument management system.*"}, "index": 0, "finish_reason": "stop"}], "object": "chat.completion", "created": 1783194032}                                                                                                                        | []                  | 2c5e22cf20044862812dfb724749c87c | 36650389-1a56-4b80-be22-3ebcfe042150 |
| f75d644e-651b-424a-81bd-3d9dda6e9f73 | 2026-07-04   |                   | 2026-07-04 19:30:30.215000 | 200         | 1.0               | 6204                  | {"extra_params":{"user_role":"underwriter","session_id":"086eb75f-2b14-4008-add2-04e1060d1c9b"},"messages":[{"content":"What are the key risk drivers?","role":"user"},{"content":"What are the key risk drivers?","role":"user"}]}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | {"choices": [{"message": {"role": "assistant", "content": "Based on Atlas's underwriting philosophy, the key risk drivers are organized into three primary dimensions:\n\n## Primary Risk Drivers\n\n**1. Driver Quality** \u2014 The dominant predictor of trucking loss\n- Driver experience and qualifications\n- Violation and accident history distribution across the fleet\n- Fleet's hiring, monitoring, and coaching discipline\n- Driver retention rates vs. churning unqualified drivers\n\n**2. Risk Characteristics**\n- Geographic operating radius and venue exposure\n- Commodity type and hauling operations\n- Equipment condition and maintenance programs\n- Fleet size and operational complexity\n\n**3. Loss Control Posture**\n- Management commitment to safety programs\n- Verifiable telematics adoption and usage\n- Camera systems implementation\n- Documented safety training and monitoring\n\n[UW-0001 Commercial Auto Underwriting Manual, \u00a71.1]\n\n## Underwriting Hierarchy\n\nAtlas's core discipline is **\"Underwrite the driver, price the risk, control the loss\"** \u2014 reflecting empirical evidence that **operator behavior, not equipment alone, is the dominant predictor of trucking loss**.\n\nThe company weights these factors in order of importance:\n1. Driver quality assessment\n2. Management safety commitment \n3. Verifiable telematics adoption\n4. Price competitiveness (last consideration)\n\n[UW-0001 Commercial Auto Underwriting Manual, \u00a71.1]\n\n## Portfolio Assessment\n\nDrivers are evaluated as a **portfolio** rather than individually, examining:\n- Average experience across the driver roster\n- Distribution of violations and accidents\n- Fleet discipline in screening and retention\n\n[DQ-0001 Driver Qualification Manual, \u00a71]\n\nThis risk-first approach means Atlas will decline business that doesn't meet eligibility standards rather than compete solely on price."}, "index": 0, "finish_reason": "stop"}], "object": "chat.completion", "created": 1783193436} | []                  | 2c5e22cf20044862812dfb724749c87c | 36650389-1a56-4b80-be22-3ebcfe042150 |
| 32949801-fc18-4093-980d-11249326d3c9 | 2026-07-04   |                   | 2026-07-04 19:30:06.391000 | 200         | 1.0               | 4617                  | {"extra_params":{"user_role":"underwriter","session_id":"086eb75f-2b14-4008-add2-04e1060d1c9b"},"messages":[{"content":"Summarize the loss history","role":"user"},{"content":"Summarize the loss history","role":"user"}]}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | {"choices": [{"message": {"role": "assistant", "content": "I don't see any specific loss history data in the retrieved context to summarize. The context only shows references to loss run requirements from the Broker Submission Guide, but doesn't contain actual loss data.\n\n**What I found:**\n- References to loss run requirements in BSG-0001 \u00a73\n- Mention of self-insured arrangement documentation requirements\n- Cross-reference to UW-0001 \u00a716 Claims History and Section 8 Loss Runs\n\n**To provide a loss history summary, I would need:**\n- Actual loss run data showing claim dates, amounts, and descriptions\n- The specific time period being analyzed\n- Information about the insured's operations during the loss period\n\nCould you please provide the specific loss run documents or clarify which account's loss history you'd like me to analyze? According to our submission guidelines, complete loss runs are required for underwriting review.\n\n**Source:** [BSG-0001_broker_submission_guide.pdf, \u00a73 Loss Runs]"}, "index": 0, "finish_reason": "stop"}], "object": "chat.completion", "created": 1783193411}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | []                  | 2c5e22cf20044862812dfb724749c87c | 36650389-1a56-4b80-be22-3ebcfe042150 |
| 3722ccd4-d76e-4534-b816-ac44688d08d8 | 2026-07-04   |                   | 2026-07-04 19:25:01.748000 | 200         | 1.0               | 25851                 | {"extra_params":{"user_role":"underwriter","session_id":"309e1656-cc7c-4a3d-b313-139ddbf42141"},"messages":[{"content":"Summarize the loss history","role":"user"},{"content":"Summarize the loss history","role":"user"}]}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | {"choices": [{"message": {"role": "assistant", "content": "I cannot provide a summary of the loss history because the retrieved context only shows section headers and brief references to loss runs, but does not contain any actual loss data or claims information.\n\n**What I found in the retrieved documents:**\n- References to \"Loss Runs\" sections in BSG-0001_broker_submission_guide.pdf\n- A mention of self-insured arrangements and gap treatment rules\n- Cross-references to UW-0001 \u00a716 Claims History and Section 8 Loss Runs\n\n**To summarize loss history, I would need:**\n- Actual loss run data showing claim dates, amounts, and descriptions\n- Claims frequency and severity information\n- Loss ratios by coverage and time period\n- Details on any significant losses or trends\n\n**Suggested Next Steps:**\n- Please provide the complete loss run documents\n- Specify which account or time period you want summarized\n- Ensure loss run data includes the standard 5-year claims history required per Atlas guidelines\n\nWould you like me to help interpret specific loss run data if you can provide the complete documents?"}, "index": 0, "finish_reason": "stop"}], "object": "chat.completion", "created": 1783193127}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | []                  | 40c67e87b3ce450a911fd4d33b684361 | 36650389-1a56-4b80-be22-3ebcfe042150 |
| 945ba868-9fdc-4812-a9ff-172b3232f3d0 | 2026-07-04   |                   | 2026-07-04 20:01:47.114000 | 200         | 1.0               | 6483                  | {"extra_params":{"user_role":"underwriter","session_id":"68b8f931-7d0d-43a4-bbd4-78742b733a19"},"messages":[{"content":"Compare to similar accounts","role":"user"},{"content":"Compare to similar accounts","role":"user"}]}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | {"choices": [{"message": {"role": "assistant", "content": "Based on the retrieved submissions, I can provide a comparison of similar accounts that have been processed by Atlas Commercial Insurance:\n\n## Similar Account Comparison\n\n**Common Profile Characteristics:**\n- All three accounts (SUB-26-10826, SUB-25-10259, SUB-25-10357) received **\"Quote\"** recommendations\n- All classified as **Preferred/acceptable** risk profiles\n- All rated as **\"Satisfactory\"** overall\n- All routed to **Theresa Vandermeer (VP Underwriting, National Accounts)** indicating larger account size\n- All proceeded to pricing under **ACI-UW-300** guidelines\n\n**Loss Ratio Performance:**\n- SUB-26-10826: **41% loss ratio**\n- SUB-25-10259: **61% loss ratio** \n- SUB-25-10357: **41% loss ratio**\n\n**Risk Assessment:**\n\u2705 All accounts performed well below Atlas's 75% loss ratio appetite threshold\n\u2705 Loss ratios range from 41-61%, indicating strong to excellent performance\n\u2705 Consistent underwriting approach for similar risk profiles\n\n## Key Observations\n\n**Assessment:** These accounts represent Atlas's target market profile\n**Confidence:** High (based on consistent underwriting patterns)\n\n**Reasons:**\n1. Loss ratios significantly below appetite threshold [Multiple submissions, \u00a77]\n2. Consistent routing to VP level indicates substantial premium size\n3. All received available credits, suggesting strong risk characteristics\n\n**Note:** To provide a more detailed comparison for your specific account, I would need additional context about the account you're evaluating, such as:\n- Fleet size and operations\n- Geographic territory\n- Commodity hauled\n- Current loss experience\n\nWould you like me to analyze how a specific account compares to these benchmarks?"}, "index": 0, "finish_reason": "stop"}], "object": "chat.completion", "created": 1783195313}                                                                                                                | []                  | 2c5e22cf20044862812dfb724749c87c | 36650389-1a56-4b80-be22-3ebcfe042150 |
| 40375f77-578a-49aa-b6a4-e39277a940d0 | 2026-07-04   |                   | 2026-07-04 20:04:47.244000 | 200         | 1.0               | 5300                  | {"extra_params":{"user_role":"underwriter","session_id":"88939259-ad78-49dc-b96f-5b5792309b32"},"messages":[{"content":"Compare to similar accounts","role":"user"},{"content":"Compare to similar accounts","role":"user"}]}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | {"choices": [{"message": {"role": "assistant", "content": "Based on the retrieved submissions, I can provide a comparison with similar accounts that have been processed by Atlas Commercial Insurance:\n\n## Similar Account Comparison\n\n**Common Profile Characteristics:**\n- All three accounts (SUB-26-10826, SUB-25-10259, SUB-25-10357) received **\"Quote\"** recommendations\n- All classified as **Preferred/acceptable** risk profiles\n- All rated as **\"Satisfactory\"** overall\n- All routed to **Theresa Vandermeer (VP Underwriting, National Accounts)** indicating larger account size\n- All proceeded to pricing under guideline **ACI-UW-300**\n\n**Loss Ratio Performance:**\n- SUB-26-10826: **41% loss ratio**\n- SUB-25-10259: **61% loss ratio** \n- SUB-25-10357: **41% loss ratio**\n\n**Assessment:**\nThese accounts represent Atlas's target market profile - well-performing risks that meet our appetite for loss ratios below 75%. The 41% loss ratios are particularly strong, while the 61% ratio still falls well within acceptable parameters.\n\n**Confidence:** 85% (based on available submission summaries)\n\n**Missing Information:**\nTo provide a more comprehensive comparison, I would need:\n- Fleet sizes and commodity types\n- Geographic territories\n- Specific credit factors applied\n- Premium ranges\n- Driver qualification details\n\nWould you like me to search for additional information about any specific aspect of these accounts or similar risk profiles?\n\n*Please verify this information against the source documents in your\ndocument management system.*"}, "index": 0, "finish_reason": "stop"}], "object": "chat.completion", "created": 1783195492}                                                                                                                                                                                                                                                                                                                                           | []                  | 2c5e22cf20044862812dfb724749c87c | 36650389-1a56-4b80-be22-3ebcfe042150 |
| 904f828d-6fc8-4456-a488-b8873f52e5b8 | 2026-07-04   |                   | 2026-07-04 20:06:44.023000 | 200         | 1.0               | 5706                  | {"extra_params":{"user_role":"underwriter","session_id":"ec645a88-7392-4301-bd6f-1e2d8dab52f5"},"messages":[{"content":"Compare to similar accounts","role":"user"},{"content":"Compare to similar accounts","role":"user"}]}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | {"choices": [{"message": {"role": "assistant", "content": "Based on the retrieved submissions, I can provide a comparison of similar accounts that have been processed by Atlas Commercial Insurance:\n\n## Similar Account Comparison\n\n**Common Profile Characteristics:**\n- All three accounts (SUB-26-10826, SUB-25-10259, SUB-25-10357) received **\"Quote\"** recommendations\n- All classified as **Preferred/acceptable** risk profiles\n- All rated as **\"Satisfactory\"** overall\n- All routed to **Theresa Vandermeer (VP Underwriting, National Accounts)** indicating larger account size\n- All directed to standard pricing procedure **(ACI-UW-300)**\n\n**Loss Ratio Performance:**\n- SUB-26-10826: **41% loss ratio**\n- SUB-25-10259: **61% loss ratio** \n- SUB-25-10357: **41% loss ratio**\n\n**Assessment:**\nAll accounts fall well within Atlas's appetite (target loss ratios below 75%). The 61% loss ratio account still received preferred treatment, indicating strong performance in other risk factors.\n\n**Confidence:** 85% (based on available submission summaries)\n\n**Missing Context:**\nTo provide a more comprehensive comparison, I would need:\n- Fleet sizes and commodity types\n- Geographic territories\n- Specific credit factors applied\n- Premium ranges\n- Coverage limits requested\n\nWould you like me to search for additional details on any of these specific submissions or look for accounts with particular characteristics (fleet size, commodity, territory, etc.)?\n\n*Please verify this information against the source documents in your\ndocument management system.*"}, "index": 0, "finish_reason": "stop"}], "object": "chat.completion", "created": 1783195609}                                                                                                                                                                                                                                                                                                                                    | []                  | 2c5e22cf20044862812dfb724749c87c | 36650389-1a56-4b80-be22-3ebcfe042150 |
| c0f64644-acf3-4e2b-bd43-52fedfe8f8ae | 2026-07-04   |                   | 2026-07-04 20:10:01.780000 | 200         | 1.0               | 13174                 | {"extra_params":{"user_role":"underwriter","session_id":"4c3c4e3f-1d62-42f2-8583-c16539c04151"},"messages":[{"content":"Compare to similar accounts","role":"user"},{"content":"Compare to similar accounts","role":"user"}]}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | {"choices": [{"message": {"role": "assistant", "content": "Based on the retrieved submissions, I can provide a comparison with similar accounts that have been processed by Atlas Commercial Insurance:\n\n## Similar Account Comparison\n\n**Common Profile Characteristics:**\n- All three accounts (SUB-26-10826, SUB-25-10259, SUB-25-10357) received **\"Quote\"** recommendations\n- All classified as **\"Preferred/acceptable profile\"** \n- All routed to **Theresa Vandermeer (VP Underwriting, National Accounts)** indicating larger account size\n- All received **\"Satisfactory\"** ratings\n- All eligible for **available credits**\n\n**Loss Ratio Performance:**\n- SUB-26-10826: **41% loss ratio**\n- SUB-25-10259: **61% loss ratio** \n- SUB-25-10357: **41% loss ratio**\n\n**Assessment:** All three accounts performed well below Atlas's 75% loss ratio threshold for preferred appetite, with two accounts at the excellent 41% level.\n\n## Key Observations\n\n\u2705 **Consistent underwriting outcomes** \u2014 All similar profiles received quote recommendations\n\u2705 **Strong loss performance** \u2014 Loss ratios ranging from 41-61%, well within appetite\n\u2705 **National account tier** \u2014 All routed to VP level, suggesting significant premium size\n\n**Confidence:** 85% (based on available submission summaries)\n\n**Note:** To provide a more detailed comparison, I would need access to the complete submission details including fleet size, commodities hauled, geographic operations, and specific risk characteristics. The current data shows only final recommendations and key metrics.\n\n**Sources:** [SUB-26-10826.pdf, \u00a77], [SUB-25-10259.pdf, \u00a77], [SUB-25-10357.pdf, \u00a77]"}, "index": 0, "finish_reason": "stop"}], "object": "chat.completion", "created": 1783195814}                                                                                                                                                                                                                | []                  | 2c5e22cf20044862812dfb724749c87c | 36650389-1a56-4b80-be22-3ebcfe042150 |
| 1a103f25-705a-4218-9043-17d58f26f82f | 2026-07-04   |                   | 2026-07-04 20:10:41.565000 | 200         | 1.0               | 3106                  | {"extra_params":{"user_role":"underwriter","session_id":"4c3c4e3f-1d62-42f2-8583-c16539c04151"},"messages":[{"content":"Compare to similar accounts","role":"user"},{"content":"Based on the retrieved submissions, I can provide a comparison with similar accounts that have been processed by Atlas Commercial Insurance:\n\n## Similar Account Comparison\n\n**Common Profile Characteristics:**\n- All three accounts (SUB-26-10826, SUB-25-10259, SUB-25-10357) received **\"Quote\"** recommendations\n- All classified as **\"Preferred/acceptable profile\"** \n- All routed to **Theresa Vandermeer (VP Underwriting, National Accounts)** indicating larger account size\n- All received **\"Satisfactory\"** ratings\n- All eligible for **available credits**\n\n**Loss Ratio Performance:**\n- SUB-26-10826: **41% loss ratio**\n- SUB-25-10259: **61% loss ratio** \n- SUB-25-10357: **41% loss ratio**\n\n**Assessment:** All three accounts performed well below Atlas's 75% loss ratio threshold for preferred appetite, with two accounts at the excellent 41% level.\n\n## Key Observations\n\n✅ **Consistent underwriting outcomes** — All similar profiles received quote recommendations\n✅ **Strong loss performance** — Loss ratios ranging from 41-61%, well within appetite\n✅ **National account tier** — All routed to VP level, suggesting significant premium size\n\n**Confidence:** 85% (based on available submission summaries)\n\n**Note:** To provide a more detailed comparison, I would need access to the complete submission details including fleet size, commodities hauled, geographic operations, and specific risk characteristics. The current data shows only final recommendations and key metrics.\n\n**Sources:** [SUB-26-10826.pdf, §7], [SUB-25-10259.pdf, §7], [SUB-25-10357.pdf, §7]","role":"assistant"},{"content":"hi","role":"user"},{"content":"hi","role":"user"}]} | {"choices": [{"message": {"role": "assistant", "content": "Hello! I'm your Atlas Commercial Insurance underwriting assistant. I'm here to help you with:\n\n- **Underwriting questions** \u2014 guidelines, appetite, referral triggers\n- **Policy information** \u2014 coverages, terms, endorsements\n- **Loss analysis** \u2014 loss runs, ratios, trends\n- **Claims guidance** \u2014 procedures and requirements\n- **Submission reviews** \u2014 completeness checks and risk assessments\n- **Account comparisons** \u2014 similar risk performance data\n\nWhat can I help you with today? Feel free to ask about any underwriting matter, policy question, or specific submission you're working on.\n\n*Please verify this information against the source documents in your\ndocument management system.*"}, "index": 0, "finish_reason": "stop"}], "object": "chat.completion", "created": 1783195844}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | []                  | 2c5e22cf20044862812dfb724749c87c | 36650389-1a56-4b80-be22-3ebcfe042150 |
| de59d3bb-3059-4fa0-a8cb-4397b96d9bc1 | 2026-07-04   |                   | 2026-07-04 20:18:32.415000 | 200         | 1.0               | 6287                  | {"extra_params":{"user_role":"underwriter","session_id":"2f08194a-a5ff-4ca9-ab18-6da931524988"},"messages":[{"content":"Compare to similar accounts","role":"user"},{"content":"Compare to similar accounts","role":"user"}]}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | {"choices": [{"message": {"role": "assistant", "content": "Based on the retrieved submissions, I can provide a comparison analysis for similar accounts that have been processed by Atlas Commercial Insurance:\n\n## Similar Account Comparison Analysis\n\n### Account Performance Patterns\n**Loss Ratio Range:** 41% - 61%\n- Best performer: 41% loss ratio (appears in 2 accounts: SUB-26-10826, SUB-25-10357)\n- Moderate performer: 61% loss ratio (SUB-25-10259)\n- All accounts fall well below Atlas's 75% loss ratio threshold\n\n### Underwriting Outcomes\n**Consistent Results:** All three comparable accounts received:\n- \u2705 **Quote recommendation** \n- \u2705 **Preferred/acceptable profile** classification\n- \u2705 **Available credits applied**\n- \u2705 **Satisfactory** overall rating\n\n### Processing Patterns\n**Routing:** All accounts were routed to **Theresa Vandermeer (VP Underwriting, National Accounts)**, indicating these are likely larger or more complex accounts requiring senior-level review.\n\n**Next Steps:** Uniform progression to pricing phase (ACI-UW-300) with subjectivity confirmation required.\n\n---\n\n## Assessment\n**Confidence:** 85%\n\nThese accounts demonstrate Atlas's appetite for well-performing transportation risks. The consistent loss ratios below 75% and uniform \"Satisfactory\" ratings suggest these represent Atlas's target market profile.\n\n**Note:** To provide a more detailed comparison, I would need additional context about:\n- Fleet sizes and operations types\n- Geographic territories\n- Specific commodities hauled\n- Driver qualification metrics\n\nWould you like me to analyze any specific risk factors or performance metrics from these comparable accounts?\n\n[Sources: SUB-26-10826.pdf, SUB-25-10259.pdf, SUB-25-10357.pdf]"}, "index": 0, "finish_reason": "stop"}], "object": "chat.completion", "created": 1783196318}                                                                                                                             | []                  | 2c5e22cf20044862812dfb724749c87c | 36650389-1a56-4b80-be22-3ebcfe042150 |

---

## `claims`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.claims (
  claim_id STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'CLM-YY-NNNNNNN',
  policy_id STRING COLLATE UTF8_BINARY NOT NULL,
  insured_id STRING COLLATE UTF8_BINARY NOT NULL,
  loss_date DATE,
  report_date DATE,
  claim_status STRING COLLATE UTF8_BINARY COMMENT 'Open, Closed, Reopened, Subrogation',
  loss_type STRING COLLATE UTF8_BINARY,
  loss_description STRING COLLATE UTF8_BINARY,
  fault_percentage DECIMAL(5,2),
  claimant_name STRING COLLATE UTF8_BINARY,
  adjuster STRING COLLATE UTF8_BINARY,
  attorney_involved BOOLEAN,
  litigation_status STRING COLLATE UTF8_BINARY COMMENT 'None, Pre-Suit, Suit Filed, Trial Set, Settled',
  total_incurred DECIMAL(12,2),
  total_paid DECIMAL(12,2),
  case_reserves DECIMAL(12,2),
  expense_paid DECIMAL(12,2),
  subrogation_amount DECIMAL(12,2),
  siu_referral BOOLEAN,
  large_loss_flag BOOLEAN COMMENT '>=250K incurred',
  catastrophic_flag BOOLEAN COMMENT 'Fatality or permanent injury',
  closure_date DATE,
  CONSTRAINT `pk_claims` PRIMARY KEY (`claim_id`))
USING delta
COMMENT 'Claims master with reserves, payments, litigation status'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 18)

| claim_id       | policy_id        | insured_id | loss_date  | report_date | claim_status | loss_type       | loss_description                                                                                                   | fault_percentage | claimant_name            | adjuster                    | attorney_involved | litigation_status | total_incurred | total_paid | case_reserves | expense_paid | subrogation_amount | siu_referral | large_loss_flag | catastrophic_flag | closure_date |
| -------------- | ---------------- | ---------- | ---------- | ----------- | ------------ | --------------- | ------------------------------------------------------------------------------------------------------------------ | ---------------- | ------------------------ | --------------------------- | ----------------- | ----------------- | -------------- | ---------- | ------------- | ------------ | ------------------ | ------------ | --------------- | ----------------- | ------------ |
| CLM-25-2614672 | ACI-AL-25-732053 | INS-1001   | 2025-08-12 | 2025-08-12  | Open         | Bodily Injury   | Rear-end collision at intersection. Third-party soft tissue injury.                                                | 80.00            | Jennifer Adams           | Mike Patterson              | False             | None              | 45000.00       | 12000.00   | 33000.00      | 3200.00      | 0.00               | False        | False           | False             |              |
| CLM-25-2614890 | ACI-PD-25-732054 | INS-1001   | 2025-10-03 | 2025-10-04  | Closed       | Physical Damage | Tire blowout on I-55; guardrail contact. Vehicle damage only.                                                      | 100.00           |                          | Lisa Chang                  | False             | None              | 28500.00       | 28500.00   | 0.00          | 1500.00      | 0.00               | False        | False           | False             | 2025-12-15   |
| CLM-24-2389453 | ACI-AL-24-732050 | INS-1001   | 2024-11-20 | 2024-11-21  | Closed       | Property Damage | Side-swipe in loading dock. Minor third-party vehicle damage.                                                      | 60.00            | Bob Construction LLC     | Mike Patterson              | False             | None              | 8200.00        | 8200.00    | 0.00          | 800.00       | 3280.00            | False        | False           | False             | 2025-02-10   |
| CLM-25-3891045 | ACI-AL-25-845210 | INS-1002   | 2025-05-18 | 2025-05-19  | Open         | Bodily Injury   | Multi-vehicle highway accident on I-10 near Phoenix. Two claimants with moderate injuries. Litigation anticipated. | 45.00            | Marcus Rivera            | Senior Adjuster Tom Bradley | True              | Suit Filed        | 385000.00      | 125000.00  | 260000.00     | 45000.00     | 0.00               | False        | True            | False             |              |
| CLM-25-3891200 | ACI-AL-25-845210 | INS-1002   | 2025-09-22 | 2025-09-24  | Open         | Combined        | Jackknife on mountain grade. Reefer cargo spoilage plus third-party vehicle damage.                                | 100.00           | Valley Fresh Produce Inc | Tom Bradley                 | False             | Pre-Suit          | 142000.00      | 68000.00   | 74000.00      | 12000.00     | 0.00               | False        | False           | False             |              |
| CLM-24-3456789 | ACI-AL-24-845207 | INS-1002   | 2024-12-05 | 2024-12-06  | Closed       | Cargo           | Temperature control failure. Full reefer load spoiled. Shipper claim.                                              | 100.00           | FreshCo Distribution     | Lisa Chang                  | False             | Settled           | 89000.00       | 89000.00   | 0.00          | 5500.00      | 0.00               | False        | False           | False             | 2025-04-30   |
| CLM-25-1098234 | ACI-AL-25-553872 | INS-1005   | 2025-06-14 | 2025-06-16  | Open         | Bodily Injury   | Intersection collision. Third party claiming neck/back injury. Late report.                                        | 70.00            | Angela Torres            | Mike Patterson              | True              | Suit Filed        | 175000.00      | 35000.00   | 140000.00     | 22000.00     | 0.00               | True         | False           | False             |              |
| CLM-25-1098567 | ACI-AL-25-553872 | INS-1005   | 2025-07-30 | 2025-08-02  | Open         | Property Damage | Backing accident at construction site. Damaged equipment.                                                          | 100.00           | Texas Concrete Supply    | Lisa Chang                  | False             | None              | 52000.00       | 32000.00   | 20000.00      | 2800.00      | 0.00               | False        | False           | False             |              |
| CLM-25-1098891 | ACI-AL-25-553872 | INS-1005   | 2025-11-08 | 2025-11-12  | Open         | Bodily Injury   | Run-off-road incident. Driver fatigue suspected. Pedestrian struck.                                                | 90.00            | Robert Nguyen            | Senior Adjuster Tom Bradley | True              | Pre-Suit          | 650000.00      | 50000.00   | 600000.00     | 35000.00     | 0.00               | True         | True            | True              |              |
| CLM-25-4521890 | ACI-AL-25-778321 | INS-1007   | 2025-04-02 | 2025-04-03  | Open         | Bodily Injury   | Low-speed rear-end on NJ Turnpike. Claimant alleging disc herniation. Potential nuclear verdict venue.             | 50.00            | Maria Santangelo         | Senior Adjuster Tom Bradley | True              | Suit Filed        | 420000.00      | 95000.00   | 325000.00     | 58000.00     | 0.00               | False        | True            | False             |              |

---

## `conversation_sessions`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.conversation_sessions (
  session_id STRING COLLATE UTF8_BINARY NOT NULL,
  role STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'user, assistant, or system',
  content STRING COLLATE UTF8_BINARY NOT NULL,
  user_id STRING COLLATE UTF8_BINARY,
  created_at TIMESTAMP)
USING delta
COMMENT 'Conversation memory. Retained 90 days per data retention policy.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 49)

| session_id                           | role      | content                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | user_id    | created_at          |
| ------------------------------------ | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------- |
| a1a47a3e-82bd-46e3-a5ba-92489faef2bb | assistant | Based on Atlas Commercial Insurances underwriting guidelines, here is the role of an underwriter:

## Primary Responsibilities

**Risk Assessment & Selection:**
- Evaluate insurance applications against company underwriting guidelines
- Analyze loss exposures and determine insurability
- Review financial information, operations, and management quality
- Assess compliance with safety regulations and industry standards

**Decision Making:**
- Accept, modify, or decline risks within delegated authority limits
- Determine appropriate coverage terms, conditions, and exclusions
- Set deductibles and policy limits based on risk profile
- Refer complex or high-exposure risks to senior underwriters

**Documentation & Communication:**
- Document underwriting decisions with clear rationale
- Communicate requirements and conditions to brokers and insureds
- Maintain detailed underwriting files per company standards
- Prepare referral summaries for risks exceeding authority

## Key Skills Required

**Technical Knowledge:**
- Commercial auto insurance coverages and exclusions
- DOT regulations, CSA BASIC scores, and safety requirements
- Loss analysis and trend interpretation
- Policy forms, endorsements, and regulatory compliance

**Analytical Abilities:**
- Financial statement analysis
- Loss run evaluation and loss ratio calculations
- Risk factor identification and correlation
- Pricing adequacy assessment

*Source: [UW-0001_commercial_auto_underwriting_manual.pdf, §1 Underwriting Philosophy]*

**Authority Levels:**
Underwriters operate within specific monetary and coverage authority limits. See Authority & Limits documents for current delegation levels by underwriter classification.

Would you like me to explain any specific aspect of the underwriting role in more detail? | Sarah Chen | 2026-07-06 01:50:41 |
| da6a5022-23b1-440c-afed-3a591f87ae2e | assistant | I dont see any information about **Appalachian Coal Transport** in the retrieved documents. The available context includes:

- A claim file for Ridgeline Cartage Transportation LLC
- An underwriter note regarding Blue Ridge Distribution Transportation LLC (declined submission)

To provide you with relevant information about Appalachian Coal Transport, I would need access to documents such as:

**For existing accounts:**
- Current policy file and underwriting folder
- Loss runs and claims history
- Most recent renewal submission
- Any underwriter notes or correspondence

**For new submissions:**
- Application and supplemental forms
- Driver qualification files and MVRs
- Vehicle schedules and maintenance records
- Operating authority and commodity details
- Financial statements

**What specific information do you need about Appalachian Coal Transport?**
- Account status and coverage details?
- Claims history or loss experience?
- Underwriting assessment or renewal status?
- Submission requirements for new business?

Please clarify what youre looking for, and I can help guide you to the right information sources or explain what documentation would be needed for your inquiry.

*Please verify this information against the source documents in your
document management system.*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Sarah Chen | 2026-07-05 21:14:39 |
| 1191f1e5-7180-4c8a-ac66-889a63a37f0a | assistant | I dont have access to information about a specific companys vehicle count. To help you, I would need:

1. **Company name or NAIC number** - Which transportation company are you asking about?

2. **Context** - Are you reviewing:
   - A new submission for underwriting?
   - An existing policy for renewal?
   - A claims file investigation?
   - Loss control survey data?

**What I can help you find:**

If youre working on a submission, I can help you locate vehicle schedule requirements from our underwriting guidelines, including:
- Required vehicle information formats
- Fleet size thresholds that trigger additional review
- Vehicle age and type restrictions per our appetite guidelines

**To get vehicle count information:**
- Check the **Vehicle Schedule** section of the submission
- Review the **ACORD applications** for declared vehicle counts
- Look for **DOT registration data** if available in the file

Could you clarify which company youre asking about and provide more context about your request?

---
**[DEBUG SQL Context]:** I cannot answer that question from the operational data tables.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Sarah Chen | 2026-07-06 02:45:57 |
| cfdcb571-ccb5-4351-9ef2-d6685b36b7c0 | assistant | Ill search our system for insureds with fleet sizes over 50 vehicles.

Let me query the database to find this information for you.

I encountered a technical issue accessing the fleet data. This appears to be a database connectivity problem rather than missing information.

**Suggested Next Steps:**
- Contact IT support to resolve the database connection issue
- Alternatively, you may need to access this information through:
  - The underwriting management system directly
  - Fleet schedule reports from the policy administration system
  - Your regional underwriter who may have recent fleet size reports

**What I would typically provide:**
Once the technical issue is resolved, I can give you:
- Complete list of insureds with 50+ vehicles
- Fleet size breakdown by insured
- Geographic distribution of large fleets
- Risk characteristics of these accounts

Would you like me to help with any other questions while we work on resolving this database connectivity issue?

*Please verify this information against the source documents in your
document management system.*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Sarah Chen | 2026-07-05 16:02:36 |
| 638e9c33-1936-4d0d-b5c6-d7152fb82f2b | assistant | I searched for Appalachian Coal Transport in our system but did not find any records for this company name.

**Possible reasons:**
- The company name may be recorded differently in our system (e.g., "Appalachian Coal Transportation," "Appalachian Coal Hauling," etc.)
- The account may be under a parent company or DBA name
- This may be a prospect that hasnt been written yet

**To locate the correct records, I need:**
- The exact legal entity name as it appears on the policy
- Any DBA or trade names used
- The insured ID or policy number if available
- Approximate policy effective dates

**Alternative search approaches:**
- Search by partial company name (e.g., just "Appalachian" or "Coal Transport")
- Search by principals name if known
- Search by broker or agent if this is a specific submission

Would you like me to try a broader search, or can you provide additional identifying information for this account?

*Please verify this information against the source documents in your
document management system.*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Sarah Chen | 2026-07-06 04:30:52 |
| e1109bef-d50f-4be2-95b2-0fa85c240ba6 | user      | What was discussed in the most recent Reserve Committee meeting?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Sarah Chen | 2026-07-05 17:42:06 |
| e25acfa9-19bb-412c-8124-a8ca664de62b | user      | Which insureds have a fleet size over 50 vehicles?

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Sarah Chen | 2026-07-05 17:10:47 |
| e1109bef-d50f-4be2-95b2-0fa85c240ba6 | user      | Which insureds have a fleet size over 50 vehicles?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Sarah Chen | 2026-07-05 17:37:12 |
| cfdcb571-ccb5-4351-9ef2-d6685b36b7c0 | user      | Which insureds have a fleet size over 50 vehicles?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Sarah Chen | 2026-07-05 16:02:28 |
| 638e9c33-1936-4d0d-b5c6-d7152fb82f2b | user      | Appalachian Coal Transport loss ratio                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Sarah Chen | 2026-07-06 04:29:57 |

---

## `copilot_feedback`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.copilot_feedback (
  feedback_id STRING COLLATE UTF8_BINARY NOT NULL,
  session_id STRING COLLATE UTF8_BINARY NOT NULL,
  user_id STRING COLLATE UTF8_BINARY,
  question STRING COLLATE UTF8_BINARY NOT NULL,
  answer STRING COLLATE UTF8_BINARY NOT NULL,
  rating INT COMMENT '1 = thumbs up, -1 = thumbs down',
  comment STRING COLLATE UTF8_BINARY,
  created_at TIMESTAMP,
  CONSTRAINT `pk_copilot_feedback` PRIMARY KEY (`feedback_id`))
USING delta
COMMENT 'User feedback on CoPilot responses.'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 12)

| feedback_id                          | session_id                           | user_id     | question                                   | answer                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | rating | comment | created_at          |
| ------------------------------------ | ------------------------------------ | ----------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ | ------- | ------------------- |
| 4f3c8171-6451-4873-bf0a-aee58498a269 | b08f157f-5920-436c-b5e3-1710499f236c | Underwriter | What are the key risk drivers?             | Based on the retrieved context and submission details for Dixie Express Lines (SUB-26-11087), I can identify several key risk drivers, though I need to note that the specific underwriting guidelines (UW-0001) and referral authority standards (AUTH-0001) referenced in the notes are not fully available in my current context.

## Key Risk Drivers Identified:

### **Positive Risk Factors:**
✅ **Loss Ratio Performance** — 52% three-year loss ratio is well below Atlass 75% appetite threshold
✅ **Fleet Size** — 52 units represents substantial scale with manageable complexity
✅ **Commodity Type** — General freight aligns with Atlass core appetite (dry van operations)
✅ **Operation Type** — Long haul operations are within Atlass standard appetite

### **Risk Assessment Flags:**
⚠️ **Referral Trigger Present** — Despite "Low" risk classification, referral is required
⚠️ **Driver-to-Vehicle Ratio** — 58 drivers for 52 vehicles (1.12:1 ratio) suggests potential driver turnover or scheduling complexity

## **Missing Critical Information:**
Based on the referral patterns shown in the notes for Copper Creek Freight Lines and Keel Express Transportation, key risk drivers I cannot assess include:

- **CSA BASIC scores** — Critical safety metric referenced in AUTH-0001 §4
- **MVR quality** — Driver record standards per governing guidelines
- **Specific referral trigger** — The exact reason requiring referral to Senior/Home Office authority
- **Loss run details** — Frequency, severity, and claim types within the 52% loss ratio
- **Coverage limits** — May trigger authority thresholds per AUTH-0001

**Assessment:** PROCEED WITH REFERRAL
**Confidence:** 75%

**Suggested Next Steps:**
1. Review the specific referral trigger documented in the submission file
2. Verify CSA BASIC scores meet Atlas standards
3. Confirm MVR roster quality meets UW-0001 requirements
4. Validate coverage limits align with underwriter authority per AUTH-0001

*Note: Complete risk assessment requires access to the full underwriting guidelines (UW-0001) and authority standards (AUTH-0001, AUTH-0002) referenced in the case notes.*

**Sources:**
- NOTE-0291.pdf (Underwriter Notes)
- NOTE-0111.pdf (Underwriter Notes)
- BSG-0001_broker_submission_guide.pdf (Underwriting Guidelines) | 1      |         | 2026-07-08 00:06:47 |
| cd68dd8c-e7d4-4857-b572-6269d7241a34 | b08f157f-5920-436c-b5e3-1710499f236c | Underwriter | What are the key risk drivers?             | Based on the retrieved context and submission details for Dixie Express Lines (SUB-26-11087), I can identify several key risk drivers, though I need to note that the specific underwriting guidelines (UW-0001) and referral authority standards (AUTH-0001) referenced in the notes are not fully available in my current context.

## Key Risk Drivers Identified:

### **Positive Risk Factors:**
✅ **Loss Ratio Performance** — 52% three-year loss ratio is well below Atlass 75% appetite threshold
✅ **Fleet Size** — 52 units represents substantial scale with manageable complexity
✅ **Commodity Type** — General freight aligns with Atlass core appetite (dry van operations)
✅ **Operation Type** — Long haul operations are within Atlass standard appetite

### **Risk Assessment Flags:**
⚠️ **Referral Trigger Present** — Despite "Low" risk classification, referral is required
⚠️ **Driver-to-Vehicle Ratio** — 58 drivers for 52 vehicles (1.12:1 ratio) suggests potential driver turnover or scheduling complexity

## **Missing Critical Information:**
Based on the referral patterns shown in the notes for Copper Creek Freight Lines and Keel Express Transportation, key risk drivers I cannot assess include:

- **CSA BASIC scores** — Critical safety metric referenced in AUTH-0001 §4
- **MVR quality** — Driver record standards per governing guidelines
- **Specific referral trigger** — The exact reason requiring referral to Senior/Home Office authority
- **Loss run details** — Frequency, severity, and claim types within the 52% loss ratio
- **Coverage limits** — May trigger authority thresholds per AUTH-0001

**Assessment:** PROCEED WITH REFERRAL
**Confidence:** 75%

**Suggested Next Steps:**
1. Review the specific referral trigger documented in the submission file
2. Verify CSA BASIC scores meet Atlas standards
3. Confirm MVR roster quality meets UW-0001 requirements
4. Validate coverage limits align with underwriter authority per AUTH-0001

*Note: Complete risk assessment requires access to the full underwriting guidelines (UW-0001) and authority standards (AUTH-0001, AUTH-0002) referenced in the case notes.*

**Sources:**
- NOTE-0291.pdf (Underwriter Notes)
- NOTE-0111.pdf (Underwriter Notes)
- BSG-0001_broker_submission_guide.pdf (Underwriting Guidelines) | -1     |         | 2026-07-08 00:06:47 |
| a5168862-4f98-4aed-948a-22d4fbb9807a | c714710c-459a-4273-9e86-bed1aabde72d | Sarah Chen  | Blue Ridge Freight LLC  REF                | I see youre asking about **Blue Ridge Freight LLC** with a referral (REF) designation. However, I dont find any records for "Blue Ridge Freight LLC" specifically in the retrieved documents.

The documents do contain information about several similar Blue Ridge entities:

**Found in Atlas records:**
- **Blue Ridge Logistics Group LLC** — Heavy Equipment/OK segment (NOTE-0093.pdf)
- **Blue Ridge Express LLC** — Approved with conditions per SUB-26-11309 (MIN-0090.pdf)  
- **Blue Ridge Motor Freight Inc.** — Owner Operator/NJ, declined (NOTE-0194.pdf)
- **Blue Ridge Distribution Transportation LLC** — Intermodal/NE, declined (NOTE-0248.pdf)

**To assist with Blue Ridge Freight LLC:**

**Missing Information Needed:**
- Submission number
- State of operation
- Business segment (dry van, flatbed, etc.)
- Specific referral trigger (limits, CSA scores, loss history, etc.)

**Next Steps:**
1. Verify the exact legal entity name
2. Provide submission number if available
3. Specify which referral criteria triggered the review

**Assessment:** INSUFFICIENT INFORMATION
**Confidence:** N/A — Cannot assess without proper entity identification

Would you like me to review the underwriting approach used for the other Blue Ridge entities, or can you provide the submission details for Blue Ridge Freight LLC?

*Please verify this information against the source documents in your
document management system.*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | 1      |         | 2026-07-05 05:31:23 |
| 318e6774-c789-494c-bd09-934ff46328b0 | 870e36e3-ffd2-4074-8443-314f3aa6bdc4 | Sarah Chen  | Pacific Coast Carriers - what is the risk  | I dont see any information about **Pacific Coast Carriers** in the retrieved documents or Atlass knowledge base.

To assess the risk for Pacific Coast Carriers, I would need access to:

**Required Information:**
- Application or submission details
- Loss runs (minimum 5 years)
- Driver qualification files and MVR reports
- Fleet schedule with vehicle details
- Operating authority and commodity types
- Safety management documentation
- Any prior Atlas underwriting files

**Assessment Status:** INSUFFICIENT INFORMATION
**Confidence:** 0% - No data available

**Suggested Next Steps:**
1. **Search Atlas systems** for any prior submissions or policies under "Pacific Coast Carriers"
2. **Request complete submission package** per UW-0001 requirements
3. **Verify legal entity name** - may operate under different business names
4. **Check for related entities** - parent companies, subsidiaries, or affiliated carriers

Would you like me to help you identify what specific documentation is required for a new commercial trucking submission, or do you have additional information about Pacific Coast Carriers to analyze?

*Please verify this information against the source documents in your
document management system.*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | -1     |         | 2026-07-05 05:49:53 |
| 5709d5af-f693-4ef6-89bf-7dda979754a6 | e3422040-4114-4163-98c6-7eab978b5fe9 | Underwriter | Any referral triggers here?                | I dont see any submission details or risk information in your message to evaluate for referral triggers. 

To assess referral triggers, I would need information such as:

**Coverage Details:**
- Primary Auto Liability limits requested
- Any umbrella coverage
- Total Account Premium (TAP)

**Operations:**
- Cargo types (especially HAZMAT or high-value)
- DOT safety rating
- CSA BASIC scores

**Loss History:**
- 3-year loss ratio
- Any individual losses ≥ $250,000

**Business Profile:**
- Years in operation
- Fleet size and operations

Could you provide the submission details youd like me to review for mandatory referral triggers per [AUTH-0001_underwriting_authority_referral_manual.pdf, §4]?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | 1      |         | 2026-07-07 18:46:02 |
| ecdf8218-1ada-4c9a-b0f5-987b4e913018 | test_session_001                     | test_user   | What are the key risk drivers?             | Primary risk drivers are driver quality, risk characteristics...                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | -1     |         | 2026-07-04 19:58:57 |
| e2b51911-ca92-4c03-bd7b-49c4b4488a89 | test_session_001                     | test_user   | What are the key risk drivers?             | Primary risk drivers are driver quality, risk characteristics...                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | -1     |         | 2026-07-04 20:02:45 |
| 38ec53fe-ea83-4a3a-a2d8-f64a288698fc | debug_session                        | debug_user  | What are the key risk drivers?             | Driver quality, risk characteristics, loss control posture.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | -1     |         | 2026-07-04 20:19:43 |
| f2c1964b-2c02-4405-bf18-f768eafd2c0b | verify-session-001                   | verify_test | What are the key risk drivers?             | Driver quality is the dominant predictor.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | -1     |         | 2026-07-05 05:22:30 |
| 3181b7a8-b104-4b81-9330-28873deeb4b8 | s1                                   | live_test   | grant test q                               | resp                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | 1      |         | 2026-07-05 05:05:27 |

---

## `document_chunks`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.document_chunks (
  chunk_id STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'P-... for parent, C-... for child',
  parent_id STRING COLLATE UTF8_BINARY COMMENT 'NULL for parent chunks',
  chunk_type STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'parent or child',
  chunk_text STRING COLLATE UTF8_BINARY,
  doc_id STRING COLLATE UTF8_BINARY NOT NULL,
  category STRING COLLATE UTF8_BINARY,
  source_path STRING COLLATE UTF8_BINARY,
  char_start INT,
  char_end INT,
  created_at TIMESTAMP,
  CONSTRAINT `pk_document_chunks` PRIMARY KEY (`chunk_id`))
USING delta
COMMENT 'Hierarchical chunks. child chunks are VS retrieval targets.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 45866)

| chunk_id                                                                             | parent_id                                                                   | chunk_type | chunk_text                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | doc_id                                                           | category        | source_path                                                                                | char_start | char_end | created_at                 |
| ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | --------------- | ------------------------------------------------------------------------------------------ | ---------- | -------- | -------------------------- |
| P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-aaeb522f          |                                                                             | parent     | CONFIDENTIAL — COMMITTEE RECORD · Classification: Confidential — Internal Use Only · Uncontrolled when printed — minutes of record held by the Corporate Secretary (ATLAS360).
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Portfolio Management Committee
Portfolio Management Committee — Portfolio
Review Minutes
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>MIN-0085</td></tr><tr><td>Committee</td><td>Portfolio Management Committee</td></tr><tr><td>Meeting type</td><td>Portfolio Review</td></tr><tr><td>Date</td><td>2026-03-23</td></tr><tr><td>Chair</td><td>David Okafor, Chief Underwriting Officer</td></tr><tr><td>Classification</td><td>Confidential — Internal Use Only</td></tr><tr><td>References</td><td>(portfolio-level; no single-record reference)</td></tr><tr><td>Governing standards</td><td>REF-0001 §15; UW-0001; CLM/RA/AUTH as cited</td></tr></table> | 0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8 | Meeting Minutes | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0085.pdf | 0          | 937      | 2026-07-04 01:59:44.312123 |
| C-P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-aaeb522f-8a072c | P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-aaeb522f | child      | CONFIDENTIAL — COMMITTEE RECORD · Classification: Confidential — Internal Use Only · Uncontrolled when printed — minutes of record held by the Corporate Secretary (ATLAS360).
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Portfolio Management Committee
Portfolio Management Committee — Portfolio
Review Minutes
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>MIN-0085</td></tr><tr><td>Committee</td><td>Portfolio Management Committee</td></tr><tr><td>Meeting type</td><td>Portfolio Review</td></tr><tr><td>Date</td><td>2026-03                                                                                                                                                                                                                                                                                                                                                  | 0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8 | Meeting Minutes | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0085.pdf | 0          | 600      | 2026-07-04 01:59:44.312123 |
| C-P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-aaeb522f-14b1ad | P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-aaeb522f | child      | mmittee</td></tr><tr><td>Meeting type</td><td>Portfolio Review</td></tr><tr><td>Date</td><td>2026-03-23</td></tr><tr><td>Chair</td><td>David Okafor, Chief Underwriting Officer</td></tr><tr><td>Classification</td><td>Confidential — Internal Use Only</td></tr><tr><td>References</td><td>(portfolio-level; no single-record reference)</td></tr><tr><td>Governing standards</td><td>REF-0001 §15; UW-0001; CLM/RA/AUTH as cited</td></tr></table>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8 | Meeting Minutes | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0085.pdf | 500        | 937      | 2026-07-04 01:59:44.312123 |
| P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-5e980aba          |                                                                             | parent     | 1. Attendance
• David Okafor (CUO)
• Vikram Sethi (Chief Actuary)
• Theresa Vandermeer (VP UW National Accounts)
• Susan Brandt-Mireles (CFO)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | 0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8 | Meeting Minutes | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0085.pdf | 937        | 1078     | 2026-07-04 01:59:44.312123 |
| C-P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-5e980aba-c13d83 | P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-5e980aba | child      | 1. Attendance
• David Okafor (CUO)
• Vikram Sethi (Chief Actuary)
• Theresa Vandermeer (VP UW National Accounts)
• Susan Brandt-Mireles (CFO)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | 0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8 | Meeting Minutes | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0085.pdf | 937        | 1078     | 2026-07-04 01:59:44.312123 |
| P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-1912a9f6          |                                                                             | parent     | 2. Minutes / Discussion                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | 0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8 | Meeting Minutes | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0085.pdf | 1078       | 1101     | 2026-07-04 01:59:44.312123 |
| C-P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-1912a9f6-a3d02b | P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-1912a9f6 | child      | 2. Minutes / Discussion                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | 0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8 | Meeting Minutes | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0085.pdf | 1078       | 1101     | 2026-07-04 01:59:44.312123 |
| P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-5ebfa0f1          |                                                                             | parent     | 1. Book performance: trucking loss-and-LAE ratio 70%, combined ~103% vs. 94% target (UW-0001 §1.3). Frequency 1.09 claims/PU/yr.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | 0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8 | Meeting Minutes | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0085.pdf | 1101       | 1229     | 2026-07-04 01:59:44.312123 |
| C-P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-5ebfa0f1-ecabb0 | P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-5ebfa0f1 | child      | 1. Book performance: trucking loss-and-LAE ratio 70%, combined ~103% vs. 94% target (UW-0001 §1.3). Frequency 1.09 claims/PU/yr.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | 0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8 | Meeting Minutes | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0085.pdf | 1101       | 1229     | 2026-07-04 01:59:44.312123 |
| P-0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8-b3f3edf1          |                                                                             | parent     | 2. Mix/concentration review: no single cargo class above 18% of GWP; no state above 20% (UW-0001 §2.3).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | 0031077e2f3247979a9a580792f9ddad5fbabe4da0d268410495cd5eaf30faf8 | Meeting Minutes | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0085.pdf | 1229       | 1332     | 2026-07-04 01:59:44.312123 |

---

## `drivers`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.drivers (
  driver_id STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'DRV-NNNN',
  insured_id STRING COLLATE UTF8_BINARY NOT NULL,
  first_name STRING COLLATE UTF8_BINARY,
  last_name STRING COLLATE UTF8_BINARY,
  cdl_number STRING COLLATE UTF8_BINARY,
  cdl_state STRING COLLATE UTF8_BINARY,
  cdl_class STRING COLLATE UTF8_BINARY COMMENT 'A, B, or C',
  date_of_birth DATE,
  hire_date DATE,
  years_cdl_experience INT,
  mvr_points INT,
  mvr_date DATE,
  driver_status STRING COLLATE UTF8_BINARY COMMENT 'Active, Excluded, Terminated, Leave',
  disqualifying_offense BOOLEAN,
  hazmat_endorsement BOOLEAN,
  tanker_endorsement BOOLEAN,
  accidents_3yr INT,
  violations_3yr INT,
  telematics_score DECIMAL(5,1),
  CONSTRAINT `pk_drivers` PRIMARY KEY (`driver_id`))
USING delta
COMMENT 'Driver roster with qualification and MVR data'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 42)

| driver_id | insured_id | first_name | last_name | cdl_number      | cdl_state | cdl_class | date_of_birth | hire_date  | years_cdl_experience | mvr_points | mvr_date   | driver_status | disqualifying_offense | hazmat_endorsement | tanker_endorsement | accidents_3yr | violations_3yr | telematics_score |
| --------- | ---------- | ---------- | --------- | --------------- | --------- | --------- | ------------- | ---------- | -------------------- | ---------- | ---------- | ------------- | --------------------- | ------------------ | ------------------ | ------------- | -------------- | ---------------- |
| DRV-2001  | INS-1001   | Robert     | Thompson  | IL-CDL-88432156 | IL        | A         | 1978-05-12    | 2019-06-01 | 18                   | 0          | 2026-01-15 | Active        | False                 | False              | False              | 0             | 0              | 92.4             |
| DRV-2002  | INS-1001   | Maria      | Gonzalez  | IL-CDL-77321045 | IL        | A         | 1985-11-23    | 2020-02-15 | 12                   | 1          | 2026-01-15 | Active        | False                 | False              | False              | 0             | 1              | 87.8             |
| DRV-2003  | INS-1001   | James      | Williams  | MO-CDL-99654321 | MO        | A         | 1972-08-30    | 2019-03-20 | 24                   | 0          | 2026-01-15 | Active        | False                 | True               | False              | 0             | 0              | 95.1             |
| DRV-2004  | INS-1001   | David      | Brown     | IL-CDL-55789432 | IL        | A         | 1990-03-17    | 2022-08-10 | 7                    | 2          | 2026-01-15 | Active        | False                 | False              | False              | 1             | 2              | 78.3             |
| DRV-2005  | INS-1001   | Patricia   | Davis     | IN-CDL-44876543 | IN        | A         | 1982-12-05    | 2021-01-05 | 15                   | 0          | 2026-01-15 | Active        | False                 | False              | True               | 0             | 0              | 91.7             |
| DRV-2010  | INS-1002   | Michael    | Chen      | CA-CDL-33987654 | CA        | A         | 1980-07-22    | 2020-08-01 | 16                   | 1          | 2025-12-20 | Active        | False                 | False              | False              | 0             | 1              | 84.2             |
| DRV-2011  | INS-1002   | Carlos     | Ramirez   | CA-CDL-22109876 | CA        | A         | 1988-04-15    | 2021-03-15 | 9                    | 3          | 2025-12-20 | Active        | False                 | False              | False              | 1             | 3              | 68.5             |
| DRV-2012  | INS-1002   | Kevin      | OBrien    | AZ-CDL-11234567 | AZ        | A         | 1975-09-08    | 2020-07-15 | 22                   | 0          | 2025-12-20 | Active        | False                 | True               | True               | 0             | 0              | 93.8             |
| DRV-2013  | INS-1002   | Thomas     | Jackson   | CA-CDL-66543210 | CA        | A         | 1992-01-30    | 2023-11-01 | 4                    | 5          | 2025-12-20 | Active        | False                 | False              | False              | 2             | 4              | 55.2             |
| DRV-2014  | INS-1002   | Anthony    | Morales   | NV-CDL-88765432 | NV        | A         | 1983-06-19    | 2022-05-01 | 14                   | 7          | 2025-12-20 | Excluded      | True                  | False              | False              | 1             | 2              | 42.0             |

---

## `eval_results`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.eval_results (
  category STRING COLLATE UTF8_BINARY,
  difficulty STRING COLLATE UTF8_BINARY,
  failed_checks STRING COLLATE UTF8_BINARY,
  intent STRING COLLATE UTF8_BINARY,
  passed BOOLEAN,
  question STRING COLLATE UTF8_BINARY,
  question_id STRING COLLATE UTF8_BINARY,
  response_length BIGINT,
  response_preview STRING COLLATE UTF8_BINARY,
  response_time_s DOUBLE,
  role STRING COLLATE UTF8_BINARY,
  run_id STRING COLLATE UTF8_BINARY,
  run_timestamp STRING COLLATE UTF8_BINARY)
USING delta
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 139)

| category                | difficulty | failed_checks                                                              | intent | passed | question                                                                 | question_id | response_length | response_preview                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | response_time_s | role            | run_id          | run_timestamp              |
| ----------------------- | ---------- | -------------------------------------------------------------------------- | ------ | ------ | ------------------------------------------------------------------------ | ----------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | --------------- | --------------- | -------------------------- |
| Underwriting Guidelines | medium     | []                                                                         | hybrid | True   | What are the acceptable loss ratio ranges for renewal business?          | UW-004      | 1160            | I don't have access to Atlas Commercial Insurance's specific underwriting guidelines that would contain the acceptable loss ratio ranges for renewal business. To provide you with accurate information, I would need to retrieve this from Atlas's underwriting manual or renewal guidelines document.

**What I need to find:**
- Renewal underwriting guidelines
- Loss ratio thresholds by line of business
- Any variations by account size, territory, or commodity type
- Timeframe for loss ratio calculatio | 3.56            | underwriter     | 20260704_063542 | 2026-07-04T06:35:42.193427 |
| Underwriting Guidelines | medium     | [{"check": "has_keyword:long haul", "passed": false, "detail": "MISSING"}] | hybrid | False  | What is the minimum fleet size we will insure for long-haul operations?  | UW-002      | 1217            | I don't have access to Atlas Commercial Insurance's specific underwriting guidelines regarding minimum fleet size requirements for long-haul operations in my current knowledge base.

To provide you with the accurate minimum fleet size threshold, I would need to retrieve this information from Atlas's underwriting guidelines, specifically from documents that would contain:

- Fleet size requirements by operation type
- Long-haul vs. local delivery distinctions
- Minimum vehicle count thresholds
-  | 4.14            | underwriter     | 20260704_063542 | 2026-07-04T06:35:42.193460 |
| Underwriting Guidelines | easy       | []                                                                         | hybrid | True   | What driver MVR point thresholds lead to driver exclusion?               | UW-005      | 1309            | I apologize, but I'm currently experiencing a technical issue retrieving information from Atlas's underwriting guidelines database. The system is showing a retrieval error that prevents me from accessing the specific MVR point thresholds for driver exclusions.

**What I need to provide you:**
- Specific point thresholds that trigger automatic driver exclusion
- Point thresholds that require underwriter review/referral
- Time periods over which points are evaluated
- Any state-specific variations | 4.41            | underwriter     | 20260704_063542 | 2026-07-04T06:35:42.193480 |
| Underwriting Guidelines | easy       | []                                                                         | hybrid | True   | What are the referral triggers for HAZMAT fleets?                        | UW-001      | 1218            | I apologize, but I'm experiencing a technical issue retrieving information from Atlas's underwriting guidelines database. The system is currently unable to access the specific referral triggers for HAZMAT fleets.

**What I can tell you from the general company context:**
- HAZMAT operations require referral to Senior Underwriter regardless of other risk factors
- This is a blanket referral requirement for all hazardous materials transportation

**What I cannot provide right now:**
- Specific HAZ | 6.6             | underwriter     | 20260704_063542 | 2026-07-04T06:35:42.193499 |
| Underwriting Guidelines | medium     | []                                                                         | hybrid | True   | What CSA score thresholds trigger automatic referral to VP Underwriting? | UW-003      | 1309            | I apologize, but I'm currently experiencing a technical issue retrieving information from Atlas's underwriting guidelines database. The system is showing a retrieval error that prevents me from accessing the specific CSA BASIC score thresholds for VP Underwriting referrals.

**What I need to provide you:**
- Specific CSA BASIC score thresholds by category (Unsafe Driving, Crash Indicator, HOS Compliance, etc.)
- Which combinations of scores trigger automatic VP referral
- Any exceptions or addit | 7.9             | underwriter     | 20260704_063542 | 2026-07-04T06:35:42.193515 |
| Underwriting Guidelines | easy       | []                                                                         | hybrid | True   | What deductible options are available for auto liability?                | UW-007      | 1166            | I apologize, but I'm currently experiencing a technical issue retrieving information from Atlas's underwriting guidelines and policy documents. The system is showing a retrieval error that prevents me from accessing the specific deductible options for auto liability coverage.

**What I need to provide you with:**
- Available deductible amounts for auto liability
- Any restrictions or conditions on deductible selection
- How deductibles vary by coverage type or risk profile
- Relevant policy form | 3.8             | underwriter     | 20260704_063542 | 2026-07-04T06:35:42.193532 |
| Underwriting Guidelines | hard       | []                                                                         | hybrid | True   | What are the territory restrictions for new business in Texas?           | UW-006      | 1284            | I apologize, but I'm currently experiencing a technical issue retrieving information from Atlas's underwriting guidelines database. The system is showing a retrieval error that prevents me from accessing the specific territory restrictions for Texas new business.

**What I need to provide you:**
- Specific Texas territory restrictions or exclusions
- Any county-level limitations
- Urban vs. rural operational restrictions
- Relevant guideline citations

**Immediate next steps:**
1. Please check t | 4.56            | underwriter     | 20260704_063542 | 2026-07-04T06:35:42.193547 |
| Claims Procedures       | easy       | []                                                                         | hybrid | True   | What is the threshold for a large loss designation?                      | CLM-004     | 1039            | I apologize, but I'm unable to retrieve the specific threshold for large loss designation from Atlas's guidelines due to a technical issue with the document search system.

**What I need to provide you:**
- The specific dollar amount that triggers large loss designation
- Any additional criteria (e.g., severity type, coverage involved)
- Reporting and handling procedures for large losses
- Source citation from Atlas's claims or underwriting guidelines

**Suggested next steps:**
1. Check the Clai | 3.37            | claims_adjuster | 20260704_063542 | 2026-07-04T06:35:42.193563 |
| Claims Procedures       | easy       | []                                                                         | hybrid | True   | What is the process for reporting a new bodily injury claim?             | CLM-001     | 1614            | I apologize, but I'm currently experiencing a technical issue retrieving information from Atlas's claims procedures documentation. The system is showing a retrieval error that prevents me from accessing the specific claims reporting guidelines.

**What I need to provide you with:**
- Step-by-step claims reporting process for bodily injury claims
- Required documentation and forms
- Reporting timeframes and deadlines
- Contact information for claims intake
- Initial reserve setting procedures
- R | 7.19            | claims_adjuster | 20260704_063542 | 2026-07-04T06:35:42.193578 |
| Claims Procedures       | medium     | []                                                                         | hybrid | True   | When should a claim be referred to SIU for investigation?                | CLM-002     | 1299            | I apologize, but I'm currently experiencing a technical issue retrieving information from Atlas's knowledge base. The system is showing a retrieval error that prevents me from accessing our SIU referral guidelines and procedures.

**What I cannot provide right now:**
- Specific SIU referral triggers and thresholds
- Documentation requirements for SIU referrals
- Timeline requirements for making referrals
- Authority levels for SIU referral decisions

**Immediate recommendation:**
Please consult  | 5.54            | claims_adjuster | 20260704_063542 | 2026-07-04T06:35:42.193594 |

---

## `eval_results_latest`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.eval_results_latest (
  request STRING COLLATE UTF8_BINARY,
  response STRING COLLATE UTF8_BINARY)
USING delta
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 15)

| request                                                                 | response                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| What are the referral triggers for HAZMAT fleet operations?             | Based on Atlas's underwriting guidelines, here are the referral triggers for HAZMAT fleet operations:

## Mandatory Referral Requirements

**All HAZMAT operations require referral** regardless of other factors:
- Any hazmat requires **Regional Director minimum** approval [RA-0001_risk_appetite_guide.pdf, §14]
- Missing H/X/N endorsements move an otherwise-acceptable hazmat risk to **referral/decline** until corrected [RA-0001_risk_appetite_guide.pdf, §17]

## Specific HAZMAT Referral Triggers

**Documentation Requirements:**
- **Missing verified H/X/N endorsements** — Any hazmat requires verified hazmat endorsements per UW-0001 §12 [RA-0001_risk_appetite_guide.pdf, §17]

**Authority Levels:**
- **Hazmat referral classes** require **Regional Director minimum** authority
- **Decline-band waivers** (for prohibited hazmat types) require **CUO approval** and Risk Committee review for aggregations [RA-0001_risk_appetite_guide.pdf, §14]

## Additional Considerations

**Routing Requirements:**
- Referral routing follows **UW-0001 §23–§24** procedures [RA-0001_risk_appetite_guide.pdf, §14]

**Mixed Operations:**
- For fleets with incidental hazmat (<5% of loads), may be handled by endorsement and referral rather than re-rating the entire fleet [UW-0001_commercial_auto_underwriting_manual.pdf, §18.3]

**Assessment:** All HAZMAT operations are **MANDATORY REFERRAL** to Regional Director level or higher.

**Confidence:** 95% — This is clearly stated across multiple guideline sections.

**Note:** The specific hazmat classes and any that fall into "Decline-band" categories would require the complete cargo appetite matrix from RA-0001 to identify, but the referral requirement applies universally to hazmat operations.

**Sources:**
- RA-0001_risk_appetite_guide.pdf (Underwriting Guidelines)
- UW-0001_commercial_auto_underwriting_manual.pdf (Underwriting Guidelines) |
| What is the maximum fleet size eligible for standard rate filing?       | I cannot find information about the maximum fleet size eligible for standard rate filing in the available documents. This type of underwriting guideline would typically be found in:

- Underwriting Guidelines manual
- Rate Filing Standards document
- Fleet Size Classification guidelines

To get this information, you would need to:
1. Check the current Underwriting Guidelines document, specifically the fleet classification section
2. Review any Rate Filing Standards or Classification documents
3. Contact the Underwriting Department directly for current fleet size thresholds

**Missing Information:** Maximum fleet size threshold for standard vs. large fleet rate filing classification

This is important operational information that should be readily available in Atlas's underwriting guidelines. If you have access to these documents, please share them so I can provide the specific fleet size limits.

*Please verify this information against the source documents in your
document management system.*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| What CSA BASIC percentile thresholds require senior UW referral?        | Based on Atlas's underwriting guidelines, the following CSA BASIC percentile thresholds require senior underwriter referral:

## Atlas CSA BASIC Referral Thresholds

| BASIC Category | Referral Threshold |
|---|---|
| **Unsafe Driving** | 65th percentile |
| **Hours-of-Service Compliance** | 65th percentile |
| **Driver Fitness** | 80th percentile |
| **Controlled Substances/Alcohol** | **Any alert = refer** |
| **Vehicle Maintenance** | 75th percentile |
| **Hazmat Compliance** | 75th percentile |
| **Crash Indicator** | 65th percentile |

**Source:** [UW-0001_commercial_auto_underwriting_manual.pdf, §13.2]

## Additional Referral Rules

- **Multiple elevated BASICs:** Two or more elevated BASIC categories trigger referral regardless of individual percentiles [REG-0005_safety_audits_csa_intervention_manual.pdf, §7.2]

- **Single elevated BASIC:** One elevated BASIC with an improving trend and corrective action plan is generally manageable and may not require referral [REG-0005_safety_audits_csa_intervention_manual.pdf, §7.2]

**Important Note:** These are Atlas's internal underwriting thresholds, not federal intervention thresholds. Atlas uses these percentiles as leading indicators for risk assessment.

**Sources:**
- UW-0001_commercial_auto_underwriting_manual.pdf (Underwriting Guidelines)
- REG-0005_safety_audits_csa_intervention_manual.pdf (Regulatory & Compliance)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| What are the driver qualification requirements for new operators?       | Based on Atlas's driver qualification guidelines, here are the requirements for new operators:

## Driver Qualification File Requirements

Each driver must have a complete qualification file containing:
- Driver application
- Motor Vehicle Records (MVRs)
- Medical certificate
- Road-test certificate
- Clearinghouse query
- Drug-screen result
- Annual review of driving record

[DQ-0001_driver_qualification_manual.pdf, §2.2]

## Atlas's Driver Assessment Philosophy

Atlas evaluates drivers as "the single most credible indicator of expected loss." The underwriting approach focuses on:

**Portfolio Assessment:** Underwriters review the entire driver roster, examining:
- Average experience level
- Violation/accident distribution across the fleet
- Fleet's discipline in hiring, monitoring, and coaching practices

**Performance Standards:** Fleets that demonstrate rigorous screening, driver retention, and measurable coaching programs earn driver credits, while fleets with high turnover of unqualified drivers face debits or decline.

[DQ-0001_driver_qualification_manual.pdf, §1]

## Missing Information

The retrieved documents reference "underwriting minimums for scheduled" drivers but the specific qualification thresholds (experience requirements, violation limits, etc.) are cut off in the available text. 

**Suggested Next Steps:**
- Request complete DQ-0001 document sections covering minimum qualification standards
- Verify if there are different requirements for owner-operators vs. company drivers
- Confirm if new operators have different standards than established fleets

**Confidence:** 75% - Complete documentation requirements are clear, but specific qualification thresholds need additional retrieval.

**Sources:**
- DQ-0001_driver_qualification_manual.pdf (Underwriting Guidelines)
- FE-0001_fleet_eligibility_guide.pdf (Underwriting Guidelines)       |
| What is the claims handling process for losses over $250,000?           | Based on Atlas's Large Loss Guide, here is the claims handling process for losses over $250,000:

## Large Loss Definition & Triggers

A large loss is defined as any individual claim with probable ultimate incurred **at or above $250,000**, or any claim involving:
- Fatality
- Serious/permanent injury (brain, spine, amputation, severe burns)
- Clear potential to exceed primary limits and reach umbrella coverage

[CLM-0003_large_loss_guide.pdf, §1, Purpose and Definition]

## Key Process Requirements

**Senior Handling:** Large losses require assignment to senior claims professionals rather than standard adjusters.

**Early Roundtable:** Immediate case review involving multiple stakeholders to assess exposure and strategy.

**Disciplined Reserving:** Structured reserve-setting process with regular cadence reviews.

**Proactive Litigation Strategy:** Early development of defense approach given high severity potential.

## Critical Success Factors

The guide emphasizes that **"the cost of a serious-injury trucking claim is set early"** through:
- Speed of investigation
- Quality of evidence preservation (telematics, dual-camera footage)
- Realistic first reserve setting

**Key Warning:** "Late recognition is the most expensive mistake in claims."

[CLM-0003_large_loss_guide.pdf, §1, Callout]

## Cross-Referenced Procedures

The large loss process connects to:
- CLM-0002 (Catastrophe Events)
- CLM-0006 (Litigation procedures)
- CLM-0008 (Reserve management)

**Note:** The retrieved content shows the definition and overview principles. For complete step-by-step procedures, staffing requirements, and reporting timelines, I would need access to the full sections of CLM-0003 that detail the operational workflow.

**Sources:**
- CLM-0003_large_loss_guide.pdf (Claims Procedures)
- CLM-0001_claims_handling_manual.pdf (Claims Procedures)                         |
| How long does the insured have to report a new claim?                   | I don't see specific claim reporting timeframes in the retrieved documents. The sources provided contain meeting minutes with action items for claims staff, but don't include the policy language or claims procedures that would specify reporting requirements.

To answer your question about claim reporting timeframes, I would need access to:

- **Policy forms** — The "Conditions" section typically contains reporting requirements
- **Claims procedures manual** — Internal guidelines on notification timeframes
- **Underwriting guidelines** — May reference standard reporting provisions

**What I cannot determine from current sources:**
- Required notification timeframe (e.g., "as soon as practicable," 30 days, etc.)
- Whether timeframes differ by coverage type (liability vs. physical damage)
- Any state-specific variations in reporting requirements
- Consequences for late reporting

**Confidence:** 0% — No relevant information available in retrieved documents

**Suggested Next Steps:**
- Retrieve the current policy forms to review the "Conditions" section
- Check the Claims Procedures Manual for notification requirements
- Consult with Claims department (R. Achebe based on the meeting minutes) for current practices

Would you like me to search for specific policy forms or claims procedure documents?

**Sources:**
- MIN-0005.pdf (Meeting Minutes)
- MIN-0092.pdf (Meeting Minutes)
- MIN-0008.pdf (Meeting Minutes)
- MIN-0033.pdf (Meeting Minutes)
- MIN-0075.pdf (Meeting Minutes)

*Please verify this information against the source documents in your
document management system.*                                                                                                                                                                                                                                                                                                  |
| What triggers a large-loss review by the claims director?               | Based on the retrieved documents, a large loss is defined as an individual claim that meets any of these criteria [CLM-0003_large_loss_guide.pdf, §1]:

**Automatic Large Loss Triggers:**
- Probable ultimate incurred at or above **$250,000**
- Any claim involving a **fatality**
- Any claim involving **serious/permanent injury** (specifically: brain injury, spine injury, amputation, severe burns)
- Any claim with **clear potential to exceed primary limits and reach the umbrella**

**Additional Review Trigger:**
When reserves cross **$1 million**, the claim is routed to the **Reserve Committee** with a reserve memo and reinsurance is notified [CLM-0008_reserve_guidelines.pdf, §7.3].

**Key Point:** The documents emphasize that "the cost of a serious-injury trucking claim is set early — by the speed of investigation, the quality of evidence preserved (telematics, dual-camera footage), and the realism of the first reserve. Late recognition is the most expensive mistake in claims" [CLM-0003_large_loss_guide.pdf, §1].

**Confidence:** 95% - This information is clearly stated in Atlas's large loss procedures.

**Note:** While the documents reference senior handling and committee review processes, the specific role of the Claims Director in the review workflow is not detailed in the retrieved sections. You may need to reference CLM-0002, CLM-0006, or CLM-0009 for the complete organizational hierarchy and approval authorities.

**Sources:**
- CLM-0003_large_loss_guide.pdf (Claims Procedures)
- CLM-0008_reserve_guidelines.pdf (Claims Procedures)                                                                                                                                                                                                                                                                                                                                  |
| What is the SIU referral threshold for suspicious claims?               | Based on Atlas's fraud detection guidelines, the SIU referral threshold is:

**A single strong indicator, or a combination of moderate indicators, warrants an SIU referral.**

[CLM-0005_fraud_detection_guide.pdf, §3 SIU Referral Workflow]

## SIU Referral Process:

1. **Adjuster identifies red flag(s)**
2. **Document indicators in ACS + SIU referral**
3. **SIU triage: accept / monitor / return with guidance**
4. **SIU investigation plan** (statements, scene, records, experts, surveillance if warranted)
5. **Findings determination:**
   - Fraud not supported → resume handling
   - Fraud supported → coverage/denial analysis (CLM-0007) + fraud-bureau report
6. **Outcome documented; referral to Legal/authorities as required**

## Important Note:
The adjuster continues handling the claim within fair-claims timeframes while SIU investigates, unless advised otherwise by SIU.

**Confidence:** High (95%) - This is explicitly stated in the fraud detection guide.

**Cross-references:** The document references §4 Investigation, CLM-0007, and REG for additional guidance on the investigation and coverage analysis processes.

To provide more specific guidance on what constitutes "strong" vs. "moderate" indicators, I would need access to the red flag criteria section of CLM-0005.

**Sources:**
- CLM-0005_fraud_detection_guide.pdf (Claims Procedures)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| What lines of business are available under the commercial auto program? | Based on Atlas Commercial Insurance's underwriting guidelines, the following lines of business are available under the commercial auto program:

## Available Lines of Business

**Primary Coverage:**
- **Auto Liability (AL)** — Standard coverage with $1,000,000 CSL limit; higher limits available by referral [PG-0001_commercial_auto_liability.pdf, §7]

**Additional Coverages:**
- **Physical Damage** — Available for units up to 12 model years old (older units require current inspection and stated-value support) [UW-0001_commercial_auto_underwriting_manual.pdf, §5.2]
- **Motor Truck Cargo** — Covers freight being hauled; refrigerated and high-theft commodities require specified controls per RA-0001 [UW-0001_commercial_auto_underwriting_manual.pdf, §5.2; PG-0001, §7]
- **Non-Trucking Liability (NTL)** — Available only when AL is written by Atlas or an approved carrier [UW-0001_commercial_auto_underwriting_manual.pdf, §5.2]
- **Workers Compensation** — Written only in approved states and must be bundled with a trucking AL account [UW-0001_commercial_auto_underwriting_manual.pdf, §5.2]

**Enhanced Coverage:**
- **Umbrella coverage** — Often paired with higher AL limits by referral [PG-0001_commercial_auto_liability.pdf, §7]

## Important Notes

- **Physical Damage restrictions:** Salvage/rebuilt titles are ineligible for PD coverage
- **Workers Compensation:** Monoline WC for trucking requires referral to Senior Underwriter
- **Motor Truck Cargo:** May require referral depending on commodity type and risk controls

For specific product details, refer to the individual Product Guide documents (PG-0003 for Motor Truck Cargo, PG-0006 for Umbrella).

**Sources:**
- PG-0001_commercial_auto_liability.pdf (Product Guides)
- UW-0001_commercial_auto_underwriting_manual.pdf (Underwriting Guidelines)                                                                     |
| What is the minimum liability limit for long-haul fleets?               | Based on the retrieved documents, the standard liability limit is **$1,000,000 CSL (Combined Single Limit)** [PG-0001_commercial_auto_liability.pdf, §7].

However, the documents don't specify a different minimum limit specifically for long-haul fleets versus other fleet types. The $1,000,000 CSL appears to be the standard across Atlas's commercial auto liability coverage.

**Important notes:**
- Higher limits are available by referral and are often paired with umbrella coverage [PG-0001_commercial_auto_liability.pdf, §7, PG-0006]
- Long-haul operations may have additional considerations that could influence limit requirements, but the specific minimum for this fleet type isn't detailed in the available sections

**Confidence:** 75% - I can confirm the standard limit but don't have complete information about long-haul specific requirements.

**Suggested Next Steps:**
- Review the complete Product Guide PG-0001 for any long-haul specific limit requirements
- Check if there are separate underwriting guidelines that address minimum limits by fleet operation type
- Verify if regulatory requirements (like FMCSA minimums) influence Atlas's minimum limits for interstate long-haul operations

**Sources:**
- FE-0001_fleet_eligibility_guide.pdf (Underwriting Guidelines)
- PG-0001_commercial_auto_liability.pdf (Product Guides)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

---

## `feedback_overrides`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.feedback_overrides (
  override_id STRING COLLATE UTF8_BINARY NOT NULL,
  session_id STRING COLLATE UTF8_BINARY,
  user_id STRING COLLATE UTF8_BINARY NOT NULL,
  submission_id STRING COLLATE UTF8_BINARY,
  ai_recommendation STRING COLLATE UTF8_BINARY,
  uw_decision STRING COLLATE UTF8_BINARY NOT NULL,
  override_reason STRING COLLATE UTF8_BINARY COMMENT 'Established Relationship, Risk Characteristic, etc.',
  override_detail STRING COLLATE UTF8_BINARY,
  created_at TIMESTAMP,
  CONSTRAINT `pk_feedback_overrides` PRIMARY KEY (`override_id`))
USING delta
COMMENT 'Underwriter decisions that diverge from AI recommendations.'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (1 of 1)

| override_id                          | session_id | user_id     | submission_id | ai_recommendation | uw_decision | override_reason          | override_detail | created_at          |
| ------------------------------------ | ---------- | ----------- | ------------- | ----------------- | ----------- | ------------------------ | --------------- | ------------------- |
| a6c5f94d-54f6-45c3-b08d-38dc75fb43cb |            | Underwriter | SUB-26-11099  |                   | Approved    | Approved by Krish Kilaru |                 | 2026-07-07 22:29:37 |

---

## `insureds`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.insureds (
  insured_id STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'Unique insured identifier (INS-XXXX)',
  company_name STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'Legal entity name',
  dba_name STRING COLLATE UTF8_BINARY COMMENT 'Doing business as',
  dot_number STRING COLLATE UTF8_BINARY COMMENT 'USDOT number',
  mc_number STRING COLLATE UTF8_BINARY COMMENT 'Motor Carrier number',
  state_domicile STRING COLLATE UTF8_BINARY COMMENT 'State of domicile (2-letter)',
  city STRING COLLATE UTF8_BINARY,
  years_in_business INT COMMENT 'Years under current authority',
  fleet_size INT COMMENT 'Total power units',
  driver_count INT COMMENT 'Active scheduled drivers',
  primary_operation STRING COLLATE UTF8_BINARY COMMENT 'Long Haul, Regional, Local, Intermodal, Dedicated',
  primary_commodity STRING COLLATE UTF8_BINARY COMMENT 'Primary cargo type',
  safety_rating STRING COLLATE UTF8_BINARY COMMENT 'Satisfactory, Conditional, Unsatisfactory, None',
  csa_unsafe_driving DECIMAL(5,1),
  csa_hos DECIMAL(5,1),
  csa_vehicle_maint DECIMAL(5,1),
  csa_driver_fitness DECIMAL(5,1),
  annual_revenue DECIMAL(15,2),
  annual_mileage BIGINT,
  telematics_provider STRING COLLATE UTF8_BINARY,
  dashcam_coverage_pct DECIMAL(5,2),
  risk_tier STRING COLLATE UTF8_BINARY COMMENT 'Preferred, Acceptable, Borderline, Decline',
  account_manager STRING COLLATE UTF8_BINARY,
  effective_date DATE,
  CONSTRAINT `pk_insureds` PRIMARY KEY (`insured_id`))
USING delta
COMMENT 'Fleet customers and policyholders'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 14)

| insured_id | company_name                   | dba_name          | dot_number | mc_number | state_domicile | city        | years_in_business | fleet_size | driver_count | primary_operation | primary_commodity      | safety_rating | csa_unsafe_driving | csa_hos | csa_vehicle_maint | csa_driver_fitness | annual_revenue | annual_mileage | telematics_provider | dashcam_coverage_pct | risk_tier  | account_manager | effective_date |
| ---------- | ------------------------------ | ----------------- | ---------- | --------- | -------------- | ----------- | ----------------- | ---------- | ------------ | ----------------- | ---------------------- | ------------- | ------------------ | ------- | ----------------- | ------------------ | -------------- | -------------- | ------------------- | -------------------- | ---------- | --------------- | -------------- |
| INS-1001   | Heartland Express Logistics    | Heartland Express | 1234567    | MC-432156 | IL             | Springfield | 18                | 85         | 102          | Regional          | General Freight        | Satisfactory  | 22.4               | 31.1    | 18.7              | 12.3               | 28500000.00    | 8925000        | Samsara             | 92.00                | Preferred  | Sarah Mitchell  | 2019-03-15     |
| INS-1002   | Pacific Coast Carriers Inc     | PCC               | 2345678    | MC-567890 | CA             | Fontana     | 12                | 42         | 48           | Long Haul         | Refrigerated           | Satisfactory  | 38.2               | 45.6    | 28.3              | 15.1               | 15200000.00    | 5460000        | KeepTruckin         | 78.00                | Acceptable | James Rodriguez | 2020-07-01     |
| INS-1003   | Summit Petroleum Transport LLC |                   | 3456789    | MC-678901 | TX             | Houston     | 22                | 35         | 40           | Regional          | Petroleum/Chemicals    | Satisfactory  | 15.8               | 22.4    | 20.1              | 8.9                | 42000000.00    | 3850000        | Omnitracs           | 100.00               | Preferred  | Sarah Mitchell  | 2017-11-20     |
| INS-1004   | Great Lakes Intermodal Corp    | GLI               | 4567890    | MC-789012 | OH             | Columbus    | 8                 | 120        | 135          | Intermodal        | Containers             | Satisfactory  | 28.9               | 35.2    | 42.1              | 19.8               | 52000000.00    | 12600000       | Samsara             | 85.00                | Acceptable | David Chen      | 2021-01-10     |
| INS-1005   | Lone Star Hauling Partners     |                   | 5678901    | MC-890123 | TX             | Dallas      | 5                 | 18         | 20           | Local             | Construction Materials | Satisfactory  | 42.7               | 55.3    | 38.9              | 25.4               | 4800000.00     | 1260000        |                     | 45.00                | Borderline | James Rodriguez | 2023-04-01     |
| INS-1006   | Mountain West Freight Systems  | MW Freight        | 6789012    | MC-901234 | CO             | Denver      | 15                | 65         | 72           | Regional          | General Freight        | Satisfactory  | 19.3               | 28.7    | 15.2              | 11.6               | 22800000.00    | 7150000        | Samsara             | 88.00                | Preferred  | David Chen      | 2018-06-15     |
| INS-1007   | Eastern Seaboard Logistics LLC | ESL               | 7890123    | MC-012345 | NJ             | Newark      | 10                | 55         | 60           | Regional          | General Freight        | Conditional   | 52.1               | 48.9    | 55.3              | 32.7               | 18500000.00    | 5720000        | KeepTruckin         | 65.00                | Borderline | Sarah Mitchell  | 2022-09-01     |
| INS-1008   | Cascade Timber Transport       |                   | 8901234    | MC-123456 | OR             | Portland    | 20                | 28         | 30           | Local             | Lumber/Forest Products | Satisfactory  | 25.6               | 18.9    | 22.4              | 14.2               | 9200000.00     | 2100000        | Samsara             | 95.00                | Preferred  | David Chen      | 2016-02-28     |
| INS-1009   | Gulf States Auto Carriers      | GSAC              | 9012345    | MC-234567 | AL             | Mobile      | 7                 | 32         | 36           | Long Haul         | Automobiles            | Satisfactory  | 33.4               | 40.2    | 35.8              | 20.1               | 12400000.00    | 4680000        | Omnitracs           | 72.00                | Acceptable | James Rodriguez | 2021-08-15     |
| INS-1010   | Tri-State Tanker Corp          |                   | 1123456    | MC-345678 | PA             | Allentown   | 25                | 22         | 24           | Intermediate      | Fuel/Petroleum         | Satisfactory  | 12.1               | 15.8    | 10.4              | 7.2                | 18900000.00    | 2860000        | Omnitracs           | 100.00               | Preferred  | Sarah Mitchell  | 2015-05-10     |

---

## `loss_runs`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.loss_runs (
  loss_run_id STRING COLLATE UTF8_BINARY NOT NULL,
  insured_id STRING COLLATE UTF8_BINARY NOT NULL,
  policy_id STRING COLLATE UTF8_BINARY,
  policy_period STRING COLLATE UTF8_BINARY COMMENT 'e.g. 2024-2025',
  valuation_date DATE,
  num_claims INT,
  total_incurred DECIMAL(12,2),
  total_paid DECIMAL(12,2),
  total_reserves DECIMAL(12,2),
  earned_premium DECIMAL(12,2),
  loss_ratio DECIMAL(7,2) COMMENT 'Can exceed 100%',
  large_losses INT,
  frequency DECIMAL(5,2) COMMENT 'Claims per power unit',
  severity DECIMAL(12,2) COMMENT 'Avg claim cost',
  CONSTRAINT `pk_loss_runs` PRIMARY KEY (`loss_run_id`))
USING delta
COMMENT 'Historical loss experience by policy period'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 21)

| loss_run_id  | insured_id | policy_id        | policy_period | valuation_date | num_claims | total_incurred | total_paid | total_reserves | earned_premium | loss_ratio | large_losses | frequency | severity  |
| ------------ | ---------- | ---------------- | ------------- | -------------- | ---------- | -------------- | ---------- | -------------- | -------------- | ---------- | ------------ | --------- | --------- |
| LR-1001-2325 | INS-1001   | ACI-AL-23-732047 | 2023-2024     | 2024-03-15     | 4          | 108200.00      | 98200.00   | 10000.00       | 372000.00      | 29.10      | 0            | 0.05      | 27050.00  |
| LR-1001-2425 | INS-1001   | ACI-AL-24-732050 | 2024-2025     | 2025-03-15     | 3          | 142600.00      | 127800.00  | 14800.00       | 398000.00      | 35.80      | 0            | 0.04      | 47533.33  |
| LR-1001-2526 | INS-1001   | ACI-AL-25-732053 | 2025-2026     | 2026-06-15     | 2          | 73500.00       | 40500.00   | 33000.00       | 318750.00      | 23.06      | 0            | 0.02      | 36750.00  |
| LR-1002-2324 | INS-1002   | ACI-AL-24-845207 | 2023-2024     | 2024-07-01     | 2          | 95000.00       | 82000.00   | 13000.00       | 248000.00      | 38.30      | 0            | 0.05      | 47500.00  |
| LR-1002-2425 | INS-1002   | ACI-AL-24-845207 | 2024-2025     | 2025-07-01     | 3          | 134500.00      | 89000.00   | 45500.00       | 275000.00      | 48.90      | 0            | 0.07      | 44833.33  |
| LR-1002-2526 | INS-1002   | ACI-AL-25-845210 | 2025-2026     | 2026-06-15     | 3          | 527000.00      | 193000.00  | 334000.00      | 223500.00      | 235.79     | 1            | 0.07      | 175666.67 |
| LR-1003-2324 | INS-1003   |                  | 2023-2024     | 2024-11-20     | 1          | 310000.00      | 310000.00  | 0.00           | 480000.00      | 64.58      | 1            | 0.03      | 310000.00 |
| LR-1003-2425 | INS-1003   | ACI-AL-25-690117 | 2024-2025     | 2025-11-20     | 0          | 0.00           | 0.00       | 0.00           | 505000.00      | 0.00       | 0            | 0.00      | 0.00      |
| LR-1003-2526 | INS-1003   | ACI-AL-25-690117 | 2025-2026     | 2026-06-15     | 0          | 0.00           | 0.00       | 0.00           | 378750.00      | 0.00       | 0            | 0.00      | 0.00      |
| LR-1005-2425 | INS-1005   | ACI-AL-25-553872 | 2024-2025     | 2025-04-01     | 4          | 185000.00      | 145000.00  | 40000.00       | 72000.00       | 256.94     | 0            | 0.22      | 46250.00  |

---

## `parsed_documents`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.parsed_documents (
  doc_id STRING COLLATE UTF8_BINARY NOT NULL,
  source_path STRING COLLATE UTF8_BINARY NOT NULL,
  file_name STRING COLLATE UTF8_BINARY,
  category STRING COLLATE UTF8_BINARY COMMENT 'Matches doc_categories[].label in company_config.yaml',
  category_id STRING COLLATE UTF8_BINARY COMMENT 'Matches doc_categories[].id (S3 subfolder name)',
  parsed_text STRING COLLATE UTF8_BINARY COMMENT 'Full extracted text',
  page_count INT,
  file_size_bytes BIGINT,
  parsed_at TIMESTAMP,
  content_hash STRING COLLATE UTF8_BINARY COMMENT 'SHA-256 for dedup',
  CONSTRAINT `pk_parsed_documents` PRIMARY KEY (`doc_id`))
USING delta
COMMENT 'All parsed PDF documents. Source table for Vector Search chunking.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 1500)

| doc_id                                                           | source_path                                                                                                                   | file_name                                            | category                | category_id        | parsed_text                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | page_count | file_size_bytes | parsed_at                  | content_hash                                                     |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ----------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | --------------- | -------------------------- | ---------------------------------------------------------------- |
| 4941d46f550901851d83e85133bfba419aa704c914e858fe84558f81b0eb9003 | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/15_regulatory/REG-0007_regulatory_checklists.pdf                   | REG-0007_regulatory_checklists.pdf                   | Regulatory & Compliance | 15_regulatory      | CONFIDENTIAL — INTERNAL USE ONLY · Classification: Confidential · Uncontrolled when printed — verify the current version in the Atlas Document Register (ATLAS360) before reliance.
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Regulatory & Compliance
Regulatory Checklists
Document Control
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>REG-0007</td></tr><tr><td>Version</td><td>1.0</td></tr><tr><td>Status</td><td>Approved — In Force</td></tr><tr><td>Classification</td><td>Confidential — Internal Use Only (insured guidance extracts issued separately)</td></tr><tr><td>Document owner</td><td>VP Regulatory & Compliance</td></tr><tr><td>Approved by</td><td>Gerald Mphande, VP Regulatory & Compliance (2026-01-15); David Okafor, Chief Underwriting Officer (2026-01-15)</td></tr><tr><td>Effective date</td><td>2026-01-01</td></tr><tr><td>Next scheduled review</td><td>2027-01-01</td></tr><tr><td>Supersedes</td><td>None</td></tr><tr><td>Distribution</td><td>Compliance; Underwriting; Loss Control; insured guidance extracts (redacted)</td></tr><tr><td>Related documents</td><td>REG-0002 through REG-0006; LC-0004; UW-0001 §5; REF-0001</td></tr><tr><td>Governing standard</td><td>REF-0003 Document Control & House Style</td></tr><tr><td>Supporting systems / forms</td><td>ATLAS360; Loss Control Portal (LCP)</td></tr></table>
NOTICE. Controlled document. These checklists consolidate the compliance points in REG-0002 through REG-0006 for field use by underwriters and loss-control engineers, and for insured audit-readiness guidance. They are summaries; the source manuals and the underlying regulations control.
1. Purpose and Use
This document consolidates the Section 15 compliance points into ready-to-use checklists for: (1) underwriting eligibility screening (UW-0001 §5), (2) loss-control surveys (LC-0004), and (3) insured audit-readiness. Each checklist cross-references its source manual.
CALLOUT. Use these as a field aid, not a substitute for the full manuals. A "no" on any safety-critical item triggers the source manual's referral/decline guidance.
Cross-references: REG-0002-0006; LC-0004; UW-0001 §5.
2. Operating Authority & Filings (from REG-0002)
• [ ] Active USDOT number; correct entity/name
• [ ] Appropriate MC operating authority
• [ ] BOC-3 process agents on file
• [ ] MCS-150 biennial update current
• [ ] UCR current (where applicable)
• [ ] Vehicle marking compliant
• [ ] Financial-responsibility filings (BMC-91 / MCS-90) in place
• [ ] Safety rating acceptable; no OOS order on authority
3. Hours of Service (from REG-0003)
[ ] ELD compliant/in use (or valid exemption verified)
[ ] RODS accurate and retained; supporting docs kept
[ ] No pattern of limit/break violations
[ ] Edits/unassigned driving within normal bounds
[ ] HOS Compliance BASIC below watch threshold
[ ] Dispatch scheduling supports compliant operation
4. Driver Qualification (from REG-0004)
• [ ] Complete DQ file per item list
• [ ] MVR at hire + annual review
• [ ] CDL class/endorsements verified (N/H/X/T as needed)
• [ ] Current medical certificate; expirations tracked
• [ ] Road test/equivalent documented
• [ ] D&A program + clearinghouse queries current
• [ ] Hazmat security assessments current (if applicable)
• [ ] No disqualified drivers in safety-sensitive roles
5. Vehicle / Inspection / Maintenance (from REG-0002/0005; LC-0004/0012)
• [ ] Annual DOT periodic inspection current
• [ ] Driver pre/post-trip (DVIR) + defect workflow
• [ ] Brakes/steer tires within standard; no open safety-critical defects
• [ ] PM program documented with per-unit records
• [ ] Roadside OOS rates below national average
• [ ] Vehicle Maintenance BASIC below watch threshold
6. CSA / Safety (from REG-0005)
• [ ] CSA/SMS snapshot reviewed; BASIC percentiles noted
• [ ] No Controlled Substances/Alcohol alert
• [ ] ≤ 1 elevated BASIC with improving trend + plan
• [ ] New-entrant audit passed (if applicable)
• [ ] Corrective-action plan for any deficiency
7. Cargo & Hazmat (from REG-0006)
• [ ] Securement meets WLL/tie-down/commodity rules; en-route re-check
• [ ] Hazmat classification/packaging/marking/placarding correct
• [ ] Shipping papers + emergency info present
• [ ] Hazmat training + H/X endorsements current
• [ ] Security plan for applicable materials
• [ ] Oversize/overweight permits + escorts as required
• [ ] Cargo within RA-0001 appetite (not decline-band)
8. Master Audit-Readiness Summary
<table><tr><th>Domain</th><th>Source</th><th>Pass condition</th></tr><tr><td>Authority & filings</td><td>REG-0002</td><td>All active/current; rating acceptable</td></tr><tr><td>Hours of service</td><td>REG-0003</td><td>ELD compliant; BASIC below threshold</td></tr><tr><td>Driver qualification</td><td>REG-0004</td><td>Complete files; valid CDL/medical/D&A</td></tr><tr><td>Vehicle/maintenance</td><td>REG-0002/0005</td><td>Inspections + PM current; low OOS</td></tr><tr><td>CSA/safety</td><td>REG-0005</td><td>≤1 elevated BASIC; no D&A alert</td></tr><tr><td>Cargo/hazmat</td><td>REG-0006</td><td>Securement + hazmat compliant; in appetite</td></tr></table>
EXAMPLE. A loss-control engineer runs the §2–§7 checklists during a survey (LC-0004); two "no" items (DQ files incomplete; cameras < 80%) generate Important recommendations tracked to closure, and a clean authority/CSA result supports eligibility (UW-0001 §5, §13).
9. Revision History
<table><tr><th>Version</th><th>Date</th><th>Author</th><th>Change</th></tr><tr><td>1.0</td><td>2026-01-01</td><td>Regulatory & Compliance</td><td>Initial consolidated Regulatory Checklists.</td></tr></table>
DOCUMENT CONTROL. REG-0007 v1.0 · Classification: Confidential — Internal Use Only · Effective
2026-01-01 · Owner: VP Regulatory & Compliance · Authoritative copy: Atlas Document Register
(ATLAS360). Uncontrolled when printed. © Atlas Commercial Insurance Company. Internal proprietary
material — do not distribute externally without authorization.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | 3          | 27810           | 2026-07-04 01:34:49.984554 | 4941d46f550901851d83e85133bfba419aa704c914e858fe84558f81b0eb9003 |
| a9cf442ed7a5f7de7a733b22d8c3de892728453efe5e86fa2c26ce528b3558f2 | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/15_regulatory/REG-0002_dot_fmcsa_compliance_manual.pdf             | REG-0002_dot_fmcsa_compliance_manual.pdf             | Regulatory & Compliance | 15_regulatory      | CONFIDENTIAL — INTERNAL USE ONLY · Classification: Confidential · Uncontrolled when printed — verify the current version in the Atlas Document Register (ATLAS360) before reliance.
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Regulatory & Compliance
DOT / FMCSA Compliance Manual
Document Control
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>REG-0002</td></tr><tr><td>Version</td><td>1.0</td></tr><tr><td>Status</td><td>Approved — In Force</td></tr><tr><td>Classification</td><td>Confidential — Internal Use Only (insured guidance extracts issued separately)</td></tr><tr><td>Document owner</td><td>VP Regulatory & Compliance</td></tr><tr><td>Approved by</td><td>Gerald Mphande, VP Regulatory & Compliance (2026-01-15); David Okafor, Chief Underwriting Officer (2026-01-15)</td></tr><tr><td>Effective date</td><td>2026-01-01</td></tr><tr><td>Next scheduled review</td><td>2027-01-01</td></tr><tr><td>Supersedes</td><td>None</td></tr><tr><td>Distribution</td><td>Compliance; Underwriting; Loss Control; insured guidance extracts (redacted)</td></tr><tr><td>Related documents</td><td>REG-0001; REG-0003/0004/0005; UW-0001 §5, §13, §35; REF-0001</td></tr><tr><td>Governing standard</td><td>REF-0003 Document Control & House Style</td></tr><tr><td>Supporting systems / forms</td><td>ATLAS360; ClearPath (authority verification)</td></tr></table>
NOTICE. Controlled document. This manual summarizes federal motor-carrier requirements (administered by the FMCSA/DOT) so Atlas can assess an insured's compliance posture. The federal regulations and the carrier's own filings control; this is guidance, not legal advice. Atlas verifies authority via ClearPath at clearance (UW-0001 §4.2).
1. Purpose
This manual describes the core DOT/FMCSA requirements that define a for-hire motor carrier's legal ability to operate. An insured's standing against these requirements — active authority, valid registration, financial responsibility, and safety rating — is a baseline eligibility input for Atlas underwriting (UW-0001 §5) and a continuous monitoring signal.
CALLOUT. "Can this carrier legally operate?" is the first compliance question. Revoked, suspended, or out-of-service authority is a mandatory decline (UW-0001 §6.1, D-01).
Cross-references: UW-0001 §5, §6.1; REG-0001.
2. Operating Authority and Registration
<table><tr><th>Element</th><th>Requirement (summary)</th></tr><tr><td>USDOT Number</td><td>Identifies the carrier; required for interstate (and many intrastate) operations</td></tr><tr><td>Operating Authority (MC)</td><td>Required for for-hire interstate transport of regulated commodities</td></tr><tr><td>Process agents (BOC-3)</td><td>Designation of agents for service of process</td></tr><tr><td>Biennial update (MCS-150)</td><td>Periodic update of carrier census data</td></tr><tr><td>Vehicle marking</td><td>USDOT number and legal name displayed on power units</td></tr><tr><td>UCR registration</td><td>Annual Unified Carrier Registration where applicable</td></tr></table>
Atlas confirms active USDOT/MC status and appropriate authority for the operation at clearance and renewal (UW-0001 §4.2, §26).
Cross-references: UW-0001 §4.2, §26; REF-0001 §7 (DOT/MC fictional ranges).
3. Financial Responsibility and Insurance Filings
Federal rules require minimum levels of financial responsibility for motor carriers, evidenced by insurance filings. Key items Atlas handles or references:
<table><tr><th>Filing / endorsement</th><th>Purpose</th></tr><tr><td>Form MCS-90 (ACI-AL-MCS90)</td><td>Federal public financial-responsibility guarantee endorsed to the auto-liability policy</td></tr><tr><td>BMC-91 / BMC-91X</td><td>Proof of bodily-injury/property-damage financial responsibility filed with FMCSA</td></tr><tr><td>BMC-34 / cargo (where applicable)</td><td>Cargo financial-responsibility evidence for certain carriers</td></tr><tr><td>Cancellation notice (BMC-35)</td><td>Notice to FMCSA when coverage is cancelled</td></tr></table>
WARNING. The MCS-90 is a guarantee to the public, not coverage for the insured (PG-0001 §1; CLM-0007 §2.2). Filing and cancellation are time-sensitive and regulated; coordinate filings/cancellations through Compliance to avoid lapses in proof of financial responsibility.
Cross-references: PG-0001; CLM-0007 §2.2; REG-0008 (filing process).
4. Safety Ratings
The FMCSA assigns safety ratings based on compliance reviews: Satisfactory, Conditional, Unsatisfactory, or Unrated. Atlas maps these to underwriting posture (UW-0001 §13.1).
<table><tr><th>Rating</th><th>Meaning (summary)</th><th>Atlas posture</th></tr><tr><td>Satisfactory</td><td>Meets safety standards</td><td>Eligible</td></tr><tr><td>Unrated</td><td>Not yet rated</td><td>Eligible; lean on CSA + losses</td></tr><tr><td>Conditional</td><td>Deficiencies found</td><td>Refer; remediation required</td></tr><tr><td>Unsatisfactory</td><td>Serious deficiencies</td><td>Decline (D-01)</td></tr></table>
Cross-references: UW-0001 §13.1; REG-0005 (audits/CSA).
5. Compliance Checklist (Authority & Filings)
• [ ] Active USDOT number; correct entity/name
• [ ] Appropriate operating authority (MC) for operations
• [ ] BOC-3 process agents on file
• [ ] MCS-150 biennial update current
• [ ] UCR current (where applicable)
• [ ] Vehicle marking (USDOT + legal name) compliant
• [ ] Financial-responsibility filings in place (BMC-91/MCS-90)
• [ ] Safety rating acceptable (or remediation plan)
• [ ] No out-of-service order on authority
Cross-references: REG-0007 (consolidated checklists); UW-0001 §5.
6. Examples
EXAMPLE 1. At clearance, ClearPath shows an insured's MC authority is in "revoked" status for an insurance lapse; the submission is declined (D-01) until authority is reinstated (UW-0001 §6.1).
EXAMPLE 2. A Conditional-rated carrier submits with a documented corrective-action plan; Compliance confirms the rating status; Underwriting refers and may write with controls (UW-0001 §13.1).
7. Definitions and FAQ
7.1 Definitions
• USDOT Number: Federal carrier identifier.
• Operating Authority (MC): FMCSA grant to operate for-hire.
• MCS-90: Federal public financial-responsibility endorsement.
• BMC-91/91X: Insurance financial-responsibility filing with FMCSA.
• Out-of-Service Order: A prohibition on operating until deficiencies are cured.
7.2 FAQ
Q: Does Atlas file the MCS-90 and BMC-91? A: Atlas issues the MCS-90 endorsement and makes required FMCSA filings through Compliance (REG-0008); cancellations require timely BMC-35 notice.
Q: Is an Unrated carrier ineligible? A: No — Unrated is eligible; Atlas leans on CSA and loss data (UW-0001 §13.1).
8. Revision History
<table><tr><th>Version</th><th>Date</th><th>Author</th><th>Change</th></tr><tr><td>1.0</td><td>2026-01-01</td><td>Regulatory & Compliance</td><td>Initial DOT/FMCSA Compliance Manual.</td></tr></table>
DOCUMENT CONTROL. REG-0002 v1.0 · Classification: Confidential — Internal Use Only · Effective
2026-01-01 · Owner: VP Regulatory & Compliance · Authoritative copy: Atlas Document Register
(ATLAS360). Uncontrolled when printed. © Atlas Commercial Insurance Company. Internal proprietary
material — do not distribute externally without authorization.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | 3          | 29561           | 2026-07-04 01:34:49.984554 | a9cf442ed7a5f7de7a733b22d8c3de892728453efe5e86fa2c26ce528b3558f2 |
| c9b4fa6eb2d53ae67ae0b0f8e8fbf284d24ffa271908541ddd4ab475756cbb76 | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/15_regulatory/REG-0006_cargo_hazmat_rules_manual.pdf               | REG-0006_cargo_hazmat_rules_manual.pdf               | Regulatory & Compliance | 15_regulatory      | CONFIDENTIAL — INTERNAL USE ONLY · Classification: Confidential · Uncontrolled when printed — verify the current version in the Atlas Document Register (ATLAS360) before reliance.
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Regulatory & Compliance
Cargo and Hazardous Materials Rules Manual
Document Control
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>REG-0006</td></tr><tr><td>Version</td><td>1.0</td></tr><tr><td>Status</td><td>Approved — In Force</td></tr><tr><td>Classification</td><td>Confidential — Internal Use Only (insured guidance extracts issued separately)</td></tr><tr><td>Document owner</td><td>VP Regulatory & Compliance</td></tr><tr><td>Approved by</td><td>Gerald Mphande, VP Regulatory & Compliance (2026-01-15); Karen Whitlock, VP Loss Control & Safety (2026-01-15)</td></tr><tr><td>Effective date</td><td>2026-01-01</td></tr><tr><td>Next scheduled review</td><td>2027-01-01</td></tr><tr><td>Supersedes</td><td>None</td></tr><tr><td>Distribution</td><td>Compliance; Underwriting; Loss Control; insured guidance extracts (redacted)</td></tr><tr><td>Related documents</td><td>REG-0001; LC-0003; RA-0001 §6; DQ-0001 §5; PG-0003; REF-0001</td></tr><tr><td>Governing standard</td><td>REF-0003 Document Control & House Style</td></tr><tr><td>Supporting systems / forms</td><td>ATLAS360; ACI-SUPP-111 Hazmat Supplement</td></tr></table>
NOTICE. Controlled document. Cargo-securement and hazardous-materials rules are federal (FMCSA cargo-securement; PHMSA/DOT hazmat) and summarized here for risk assessment. The regulations control. Atlas does not write the decline-band hazmat classes in RA-0001 §6 regardless of compliance.
1. Purpose
This manual summarizes the federal cargo-securement, hazardous-materials, and weight/size rules that govern how freight is carried. Compliance posture in these areas is both a legal obligation for insureds and a loss-control/underwriting signal (LC-0003 securement; RA-0001 cargo appetite/controls).
CALLOUT. Regulatory compliance is necessary but not sufficient for Atlas appetite. A hazmat operation can be fully compliant and still be in the RA-0001 decline band (e.g., explosives, radioactive) — Atlas declines on appetite (RA-0001 §6).
Cross-references: LC-0003; RA-0001 §6; PG-0003.
2. Cargo Securement Rules (Summary)
Federal cargo-securement rules require adequate aggregate working load limit, minimum tie-down counts by article length/weight, and commodity-specific methods (metal coils, logs, vehicles, large
boulders, concrete pipe, etc.). Atlas's securement program standards (LC-0003) implement these for flatbed/heavy operations.
<table><tr><th>Element</th><th>Summary</th></tr><tr><td>Aggregate WLL</td><td>At least half the article weight (baseline)</td></tr><tr><td>Tie-down counts</td><td>By article length/weight</td></tr><tr><td>Commodity-specific</td><td>Dedicated methods for designated commodities</td></tr><tr><td>Inspection / re-check</td><td>Securement verified and re-checked en route</td></tr></table>
Cross-references: LC-0003 §2–§3; RA-0001 §3.
3. Hazardous Materials Rules (Summary)
Hazmat transport is regulated by hazard class, packaging, marking, labeling, placarding, shipping papers, emergency response information, driver training/endorsement (H/X), and security planning.
Atlas references these against the RA-0001 hazmat appetite.
<table><tr><th>Hazmat element</th><th>Summary</th></tr><tr><td>Classification</td><td>DOT hazard classes (1-9)</td></tr><tr><td>Packaging</td><td>Authorized packaging by class</td></tr><tr><td>Marking/labeling</td><td>Identification on packages</td></tr><tr><td>Placarding</td><td>Vehicle placards by class/quantity</td></tr><tr><td>Shipping papers</td><td>Proper documentation + emergency info</td></tr><tr><td>Training/endorsement</td><td>Hazmat training; H/X CDL endorsement (DQ-0001 §5)</td></tr><tr><td>Security plan</td><td>For certain higher-risk materials</td></tr></table>
WARNING. Endorsement and placarding gaps are the most common hazmat defects. An otherwise-acceptable hazmat risk moves to referral/decline until corrected (DQ-0001 §5; RA-0001 §14).
Cross-references: RA-0001 §6; DQ-0001 §5; PG-0003.
4. Weight, Size, and Oversize/Overweight
Federal and state limits govern axle weights, gross vehicle weight, and dimensions; oversize/overweight loads require permits and often escorts and route surveys (LC-0003 C12). Atlas references permit/escort compliance for heavy-haul and oversize operations (RA-0001 §10 Specialized).
<table><tr><th>Item</th><th>Summary</th></tr><tr><td>Axle/gross weight</td><td>Within legal limits or permitted</td></tr><tr><td>Dimensions</td><td>Within limits or permitted (oversize)</td></tr><tr><td>Permits/escorts</td><td>Required for oversize/overweight; route survey</td></tr><tr><td>Bridge/route restrictions</td><td>Observed per permit</td></tr></table>
Cross-references: RA-0001 §10; LC-0003 (C12).
5. Cargo & Hazmat Compliance Checklist
• [ ] Securement meets WLL/tie-down/commodity rules (LC-0003)
• [ ] En-route re-check practice documented
• [ ] Hazmat classification/packaging/marking correct
• [ ] Placarding compliant for class/quantity
• [ ] Shipping papers + emergency info present
• [ ] Hazmat training + H/X endorsements current
• [ ] Security plan for applicable materials
• [ ] Oversize/overweight permits + escorts as required
• [ ] Cargo within RA-0001 appetite (not decline-band)
Cross-references: REG-0007; LC-0003; RA-0001 §6.
6. Examples
EXAMPLE 1. Pioneer Flatbed's steel-coil loads use coil racks, rated chains, and edge protection with en-route re-checks — compliant securement and an Atlas securement credit (LC-0003; RA-0001 C5).
EXAMPLE 2. A carrier seeks bulk Class 1 explosives; though it holds hazmat endorsements and placards correctly, Atlas declines on appetite (RA-0001 §6 decline band) regardless of compliance.
7. Definitions and FAQ
7.1 Definitions
• Working Load Limit (WLL): Rated securing capacity of a tie-down/component.
• Placard: Vehicle hazard sign required for certain hazmat.
• Shipping Paper: Hazmat transport documentation with emergency info.
• Oversize/Overweight (OS/OW): Loads exceeding legal limits, requiring permits.
7.2 FAQ
Q: If a hazmat carrier is fully compliant, will Atlas write it? A: Only if the class is in RA-0001 appetite; decline-band hazmat is declined regardless of compliance ($1; RA-0001 §6).
Q: Who verifies securement compliance? A: The carrier (compliance) and Atlas Loss Control at survey (LC-0003).
8. Revision History
<table><tr><th>Version</th><th>Date</th><th>Author</th><th>Change</th></tr><tr><td>1.0</td><td>2026-01-01</td><td>Regulatory & Compliance</td><td>Initial Cargo and Hazardous Materials Rules Manual.</td></tr></table>
DOCUMENT CONTROL. REG-0006 v1.0 · Classification: Confidential — Internal Use Only · Effective
2026-01-01 · Owner: VP Regulatory & Compliance · Authoritative copy: Atlas Document Register
(ATLAS360). Uncontrolled when printed. © Atlas Commercial Insurance Company. Internal proprietary
material — do not distribute externally without authorization.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | 3          | 29180           | 2026-07-04 01:34:49.984554 | c9b4fa6eb2d53ae67ae0b0f8e8fbf284d24ffa271908541ddd4ab475756cbb76 |
| 7774f26d5627c839e5f23a208b0c38c52e94945517f350db43f7607163e7028c | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/15_regulatory/REG-0008_insurance_market_conduct_filings_manual.pdf | REG-0008_insurance_market_conduct_filings_manual.pdf | Regulatory & Compliance | 15_regulatory      | RESTRICTED — COMPLIANCE · Classification: Restricted · Uncontrolled when printed — verify the current version in the Atlas Document Register (ATLAS360) before reliance.
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Regulatory & Compliance
Insurance Market Conduct and Filings Manual
Document Control
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>REG-0008</td></tr><tr><td>Version</td><td>1.0</td></tr><tr><td>Status</td><td>Approved — In Force</td></tr><tr><td>Classification</td><td>Restricted — Compliance</td></tr><tr><td>Document owner</td><td>VP Regulatory & Compliance</td></tr><tr><td>Approved by</td><td>Gerald Mphande, VP Regulatory & Compliance (2026-01-15); Patricia Lindqvist, Chief Claims Officer (2026-01-15); Susan Brandt-Mireles, CFO (2026-01-15)</td></tr><tr><td>Effective date</td><td>2026-01-01</td></tr><tr><td>Next scheduled review</td><td>2027-01-01</td></tr><tr><td>Supersedes</td><td>None</td></tr><tr><td>Distribution</td><td>Compliance; Claims; Underwriting; Finance; Legal; Internal Audit</td></tr><tr><td>Related documents</td><td>REG-0001; CLM-0005; CLM-0007; LC-0009; UW-0001 §6, §26; REF-0001</td></tr><tr><td>Governing standard</td><td>REF-0003 Document Control & House Style</td></tr><tr><td>Supporting systems / forms</td><td>ATLAS360; filings register; complaint register</td></tr></table>
NOTICE. Restricted document. This manual governs Atlas's conduct as a regulated insurer — filings, claims practices, licensing, privacy, and complaints. State insurance laws and filed items control. This is the authoritative reference for the "REG" cross-references in Claims (CLM-0005/0007) and Loss Control (LC-0009).
1. Purpose
This manual states Atlas's obligations and controls as a regulated insurer across the states in which it operates: rate and form filings, unfair claims-settlement practices, producer licensing and appointments, privacy and data use, fraud reporting, and complaint handling. It complements the motor-carrier manuals (REG-0002-0006), which address insureds' obligations.
CALLOUT. Atlas is regulated too. Adverse-action notices on declines (UW-0001 §6), unfair-claims timeframes (CLM-0007), telematics privacy (LC-0009), and fraud-bureau reporting (CLM-0005) are all governed here.
Cross-references: REG-0001; CLM-0005/0007; LC-0009; UW-0001 §6, §26.
2. Rate and Form Filings
Atlas files rates, rules, and forms with state regulators as required (prior-approval, file-and-use, or use-and-file by state). The Product & Compliance Committee (PCC) governs filing content and timing; underwriting and pricing must operate within filed rates and rules (AUTH-0002 §1).
<table><tr><th>Item</th><th>Control</th></tr><tr><td>Rate/rule filings</td><td>Filed and approved/effective before use as required</td></tr><tr><td>Form filings</td><td>Policy forms and endorsements filed by state</td></tr><tr><td>Filing timeliness</td><td>100% on time (REG-0001 KPI)</td></tr><tr><td>Within-filing operation</td><td>UW/pricing stays within filed rules (AUTH-0002)</td></tr></table>
WARNING. Deviating from filed rates/rules — even a "small" off-filing accommodation — is a regulatory violation, distinct from internal pricing authority. Pricing flexibility exists only within the filing (AUTH-0002 §1).
Cross-references: AUTH-0002 §1; REG-0001 §3.
3. Unfair Claims-Settlement Practices
Each state regulates claims handling under unfair-claims-practices rules: prompt acknowledgement, timely investigation and decisions, good-faith settlement, and clear communication. Claims operates to these standards (CLM-0001 §7.3; CLM-0007), and Compliance monitors adherence.
<table><tr><th>Requirement (summary)</th><th>Claims control</th></tr><tr><td>Prompt acknowledgement</td><td>Per state timeframe (CLM-0001 §7.3)</td></tr><tr><td>Timely investigation/decision</td><td>Documented; within timeframes</td></tr><tr><td>Good-faith settlement</td><td>Fair evaluation; no lowballing (CLM-0006/0007)</td></tr><tr><td>ROR/declaration language</td><td>Approved, specific (CLM-0007 §3)</td></tr><tr><td>No misrepresentation of policy/facts</td><td>Compliance-monitored</td></tr></table>
WARNING. Unfair-claims violations create regulatory exposure and support bad-faith claims that can exceed policy limits (CLM-0007 §4). Follow timeframes and use approved language.
Cross-references: CLM-0001 §7.3; CLM-0006; CLM-0007.
4. Licensing, Appointments, and Producers
Atlas maintains company licenses by state and line and appoints producers as required before they transact. Producer appointments require a valid license, E&O coverage, and a signed agreement (UW-0001 §2.2, §26). Compliance tracks license/appointment status and terminations (including any required regulator notice).
<table><tr><th>Item</th><th>Control</th></tr><tr><td>Company licensing</td><td>Active by state/line</td></tr><tr><td>Producer license</td><td>Verified before appointment/transaction</td></tr><tr><td>Appointment</td><td>Recorded; maintained</td></tr><tr><td>Termination</td><td>Processed with required notices</td></tr></table>
Cross-references: UW-0001 §2.2, §26.
5. Privacy and Data Use
Atlas handles personal and telematics data under applicable privacy laws and its data-use standard: collection with notice/consent, use limited to insurance/loss-control purposes, access controls, retention schedules, and safeguards. Telematics/location data is used for underwriting and loss control, not sold or shared externally without authorization (LC-0009 §4).
WARNING. Using telematics/location or personal data beyond the consented purpose creates privacy and legal exposure (LC-0009 §4). Keep use within purpose and within consent.
Cross-references: LC-0009 §4; REF-0003 §3 (classification).
6. Fraud Reporting and Complaint Handling
6.1 Fraud Reporting
Confirmed or suspected insurance fraud is reported to the appropriate state fraud bureau as required, coordinated by Compliance with SIU and Legal (CLM-0005 §4–§5). Anti-fraud plans/notices are maintained where mandated.
6.2 Complaint Handling
Consumer/regulator complaints are logged in the complaint register, investigated, and responded to within state timeframes, with root-cause analysis feeding process improvement. Complaint trends are reported to the PCC and Board Audit Committee.
<table><tr><th>Process</th><th>Control</th></tr><tr><td>Fraud-bureau reporting</td><td>Per statute (CLM-0005)</td></tr><tr><td>Complaint logging</td><td>Complaint register (ATLAS360)</td></tr><tr><td>Complaint response</td><td>Within state timeframes</td></tr><tr><td>Trend analysis</td><td>Reported to PCC/Board</td></tr></table>
Cross-references: CLM-0005; REG-0001 §5.
7. Market-Conduct Compliance Checklist
• [ ] Rates/rules/forms filed and effective by state
• [ ] UW/pricing operating within filings (AUTH-0002)
• [ ] Unfair-claims timeframes met; approved language used
• [ ] Company licensed; producers licensed/appointed
• [ ] Privacy/data-use controls in place (incl. telematics)
• [ ] Fraud reporting per statute
• [ ] Complaints logged, responded, trended
• [ ] Records retained per schedule (REG-0001 §4)
8. Examples
EXAMPLE 1. A declination must follow state adverse-action and unfair-trade-practice rules; Underwriting uses approved language and a reason code internally, coordinated with Compliance (UW-0001 §6.3).
EXAMPLE 2. A telematics data request from a third party is declined as outside the consented purpose; Compliance confirms the data-use limits (LC-0009 §4).
EXAMPLE 3. A market-conduct exam reviews claims timeliness; the complaint register and documented timeframes (CLM-0001 §7.3) demonstrate compliance.
9. Definitions and FAQ
9.1 Definitions
• Market Conduct: An insurer's behavior in sales, underwriting, and claims.
• Filing: Submission of rates/rules/forms to a state regulator.
• Unfair Claims Practices: State-regulated standards for claim handling.
• Adverse Action: A decline/non-renewal/adverse change requiring notice.
9.2 FAQ
Q: Can underwriting price below a filed rate to win business? A: No — pricing flexibility exists only within the filing; off-filing pricing is a regulatory violation ($2; AUTH-0002 §1).
Q: Where are unfair-claims rules operationalized? A: In Claims (CLM-0001 §7.3; CLM-0007), monitored by Compliance ($3).
10. Revision History
<table><tr><th>Version</th><th>Date</th><th>Author</th><th>Change</th></tr><tr><td>1.0</td><td>2026-01-01</td><td>Regulatory & Compliance</td><td>Initial Insurance Market Conduct and Filings Manual.</td></tr></table>
DOCUMENT CONTROL. REG-0008 v1.0 · Classification: Restricted — Compliance · Effective 2026-01-01 ·
Owner: VP Regulatory & Compliance · Authoritative copy: Atlas Document Register (ATLAS360).
Uncontrolled when printed. © Atlas Commercial Insurance Company. Internal proprietary material —
do not distribute externally without authorization. | 4          | 31715           | 2026-07-04 01:34:49.984554 | 7774f26d5627c839e5f23a208b0c38c52e94945517f350db43f7607163e7028c |
| 24bc401feb5ca249e9b2a8fb0bdde4a4195457b3929ffa1c3cb5e0e207313ae3 | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/15_regulatory/REG-0003_hours_of_service_compliance_manual.pdf      | REG-0003_hours_of_service_compliance_manual.pdf      | Regulatory & Compliance | 15_regulatory      | CONFIDENTIAL — INTERNAL USE ONLY · Classification: Confidential · Uncontrolled when printed — verify the current version in the Atlas Document Register (ATLAS360) before reliance.
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Regulatory & Compliance
Hours of Service Compliance Manual
Document Control
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>REG-0003</td></tr><tr><td>Version</td><td>1.0</td></tr><tr><td>Status</td><td>Approved — In Force</td></tr><tr><td>Classification</td><td>Confidential — Internal Use Only (insured guidance extracts issued separately)</td></tr><tr><td>Document owner</td><td>VP Regulatory & Compliance</td></tr><tr><td>Approved by</td><td>Gerald Mphande, VP Regulatory & Compliance (2026-01-15); Karen Whitlock, VP Loss Control & Safety (2026-01-15)</td></tr><tr><td>Effective date</td><td>2026-01-01</td></tr><tr><td>Next scheduled review</td><td>2027-01-01</td></tr><tr><td>Supersedes</td><td>None</td></tr><tr><td>Distribution</td><td>Compliance; Underwriting; Loss Control; insured guidance extracts (redacted)</td></tr><tr><td>Related documents</td><td>REG-0001; LC-0011; DQ-0001 §19; UW-0001 §13; FE-0001 §4; REF-0001</td></tr><tr><td>Governing standard</td><td>REF-0003 Document Control & House Style</td></tr><tr><td>Supporting systems / forms</td><td>ATLAS360; ELD/telematics reports</td></tr></table>
NOTICE. Controlled document. Hours-of-Service (HOS) rules are federal (FMCSA) and summarized here for risk-assessment purposes. The federal regulations control; figures are general references and exceptions vary. This is guidance, not legal advice.
1. Purpose
This manual summarizes federal HOS limits and the ELD mandate so Atlas can assess an insured's HOS compliance — a leading indicator of fatigue risk and crash frequency (UW-0001 §13; LC-0011). HOS posture (violation patterns, log integrity, the HOS Compliance BASIC) is a core underwriting and loss-control signal.
CALLOUT. HOS compliance is the regulatory floor; fatigue risk management (LC-0011) goes beyond it. A compliant log can still reflect a fatiguing schedule.
Cross-references: UW-0001 §13; LC-0011; DQ-0001 §19.
2. Property-Carrying HOS Limits (Summary)
<table><tr><th>Limit</th><th>Summary (property-carrying CMV drivers)</th></tr><tr><td>11-hour driving</td><td>Up to 11 hours driving after 10 consecutive hours off duty</td></tr><tr><td>14-hour window</td><td>Driving not permitted beyond the 14th consecutive hour after coming on duty</td></tr><tr><td>30-minute break</td><td>Required break after 8 cumulative hours of driving</td></tr><tr><td>60/70-hour limit</td><td>60 hours/7 days or 70 hours/8 days on duty</td></tr><tr><td>34-hour restart</td><td>Optional restart of the weekly clock with 34+ consecutive hours off</td></tr><tr><td>Sleeper-berth provision</td><td>Qualifying splits of off-duty/sleeper time</td></tr><tr><td>Adverse-conditions / short-haul</td><td>Limited exceptions under defined conditions</td></tr></table>
These are general summaries; specific rules, exceptions, and any agricultural/short-haul provisions are governed by the federal regulation.
Cross-references: LC-0011 §1; REG-0001.
3. ELD Mandate and Logging
Most drivers subject to HOS must record duty status with a compliant Electronic Logging Device
(ELD). ELDs reduce log falsification and produce the data Atlas uses to validate radius (UW-0001 §14)
and assess fatigue (LC-0011). Limited exemptions exist (e.g., certain short-haul, pre-2000 engines,
driveaway-towaway, low-frequency use).
<table><tr><th>Item</th><th>Requirement (summary)</th></tr><tr><td>ELD use</td><td>Required for HOS-regulated drivers unless exempt</td></tr><tr><td>Records of duty status</td><td>Accurate, retained, transferable on request</td></tr><tr><td>Supporting documents</td><td>Retained to verify HOS</td></tr><tr><td>Exemptions</td><td>Verify legitimacy (FE-0001 §4)</td></tr></table>
WARNING. Log falsification and unassigned-driving manipulation are serious violations and, at Atlas, a disqualifying driver-integrity issue (DQ-0001 §10). A fleet tolerating falsification has a culture problem, not a paperwork problem.
Cross-references: FE-0001 §4; DQ-0001 §10; UW-0001 §14.
4. Violations and Underwriting Signals
<table><tr><th>Signal</th><th>Risk interpretation</th></tr><tr><td>HOS Compliance BASIC elevated</td><td>Scheduling pressure / fatigue exposure (UW-0001 §13)</td></tr><tr><td>Frequent form-and-manner / limit violations</td><td>Weak controls</td></tr><tr><td>Excessive log edits / unassigned driving</td><td>Data-integrity concern; possible falsification</td></tr><tr><td>Personal-conveyance misuse</td><td>Hidden driving time</td></tr></table>
Patterns drive referral (UW-0001 §23), debits, and loss-control engagement (LC-0011).
Cross-references: UW-0001 §13, §23; LC-0011 §4.
5. HOS Compliance Checklist
• [ ] ELD compliant and in use (or valid exemption verified)
• [ ] Records of duty status accurate and retained
• [ ] Supporting documents retained
• [ ] No pattern of limit/break violations
• [ ] Edits/unassigned driving within normal bounds
• [ ] HOS Compliance BASIC below watch threshold
• [ ] Driver HOS/fatigue training current (DQ-0001 §21)
• [ ] Dispatch scheduling supports compliant operation (LC-0011)
Cross-references: REG-0007; LC-0011.
6. Examples
EXAMPLE 1. A fleet's HOS Compliance BASIC is elevated with frequent 14-hour-window violations; underwriting refers and Loss Control engages on scheduling (LC-0011); the file documents the corrective plan (UW-0001 §13, §31 Case B).
EXAMPLE 2. An insured claims short-haul exemption from ELDs; Compliance/Loss Control verifies the operation genuinely qualifies; a non-qualifying operation running paper logs is treated as a compliance and fatigue exposure (FE-0001 §4).
7. Definitions and FAQ
7.1 Definitions
• HOS: Hours-of-Service limits on driving/on-duty time.
• ELD: Electronic Logging Device.
• Records of Duty Status (RODS): The driver's logged duty time.
• 34-Hour Restart: Optional reset of the weekly on-duty clock.
7.2 FAQ
Q: Does Atlas enforce HOS? A: No — the FMCSA does. Atlas assesses HOS compliance as a fatigue/frequency risk signal (UW-0001 §13).
Q: Are paper logs ever acceptable? A: Only for genuinely exempt operations; non-exempt paper-log operations are a compliance and fatigue concern (§3; FE-0001 §4).
8. Revision History
<table><tr><th>Version</th><th>Date</th><th>Author</th><th>Change</th></tr><tr><td>1.0</td><td>2026-01-01</td><td>Regulatory & Compliance</td><td>Initial Hours of Service Compliance Manual.</td></tr></table>
DOCUMENT CONTROL. REG-0003 v1.0 · Classification: Confidential — Internal Use Only · Effective
2026-01-01 · Owner: VP Regulatory & Compliance · Authoritative copy: Atlas Document Register
(ATLAS360). Uncontrolled when printed. © Atlas Commercial Insurance Company. Internal proprietary
material — do not distribute externally without authorization.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 3          | 28682           | 2026-07-04 01:34:49.984554 | 24bc401feb5ca249e9b2a8fb0bdde4a4195457b3929ffa1c3cb5e0e207313ae3 |
| 7270448c12bc47fae6ca4045ec39597ba625526de35b8ec939a733602f4803d1 | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/15_regulatory/REG-0004_driver_qualification_compliance_manual.pdf  | REG-0004_driver_qualification_compliance_manual.pdf  | Regulatory & Compliance | 15_regulatory      | CONFIDENTIAL — INTERNAL USE ONLY · Classification: Confidential · Uncontrolled when printed — verify the current version in the Atlas Document Register (ATLAS360) before reliance.
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Regulatory & Compliance
Driver Qualification Compliance Manual
Document Control
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>REG-0004</td></tr><tr><td>Version</td><td>1.0</td></tr><tr><td>Status</td><td>Approved — In Force</td></tr><tr><td>Classification</td><td>Confidential — Internal Use Only (insured guidance extracts issued separately)</td></tr><tr><td>Document owner</td><td>VP Regulatory & Compliance</td></tr><tr><td>Approved by</td><td>Gerald Mphande, VP Regulatory & Compliance (2026-01-15); David Okafor, Chief Underwriting Officer (2026-01-15)</td></tr><tr><td>Effective date</td><td>2026-01-01</td></tr><tr><td>Next scheduled review</td><td>2027-01-01</td></tr><tr><td>Supersedes</td><td>None</td></tr><tr><td>Distribution</td><td>Compliance; Underwriting; Loss Control; insured guidance extracts (redacted)</td></tr><tr><td>Related documents</td><td>REG-0001; DQ-0001; UW-0001 §9-$12; REF-0001</td></tr><tr><td>Governing standard</td><td>REF-0003 Document Control & House Style</td></tr><tr><td>Supporting systems / forms</td><td>ATLAS360; clearinghouse query references</td></tr></table>
NOTICE. Controlled document. This manual summarizes federal driver-qualification requirements so Atlas can assess an insured's DQ-file compliance. The federal regulations control; Atlas's underwriting driver standards are in DQ-0001 (which may be stricter). This is guidance, not legal advice.
1. Purpose
This manual summarizes the federal driver qualification (DQ) file requirements and related driver-fitness rules. An insured's DQ-file discipline is both a regulatory obligation and a strong risk signal sampled by Loss Control (LC-0004; DQ-0001 §23). It complements Atlas's underwriting driver standards (DQ-0001) and Atlas's review of CDL/endorsements and medical certification (UW-0001 §12).
CALLOUT. Regulatory DQ files (this manual) and Atlas underwriting standards (DQ-0001) overlap but differ: the federal file is the legal minimum; DQ-0001 may require more for an Atlas-acceptable driver.
Cross-references: DQ-0001; UW-0001 §9–§12; LC-0004.
2. Driver Qualification File Contents (Summary)
<table><tr><th>Item</th><th>Requirement (summary)</th></tr><tr><td>Employment application</td><td>Required content incl. employment history</td></tr><tr><td>Inquiry to previous employers</td><td>Safety-performance/D&A history inquiry</td></tr><tr><td>MVR at hire + annual review</td><td>Driving record obtained and reviewed annually</td></tr><tr><td>CDL verification</td><td>Correct class and endorsements for operation</td></tr><tr><td>Medical examiner's certificate</td><td>Current; tracked for expiration</td></tr><tr><td>Road test or equivalent</td><td>Demonstrated ability for the equipment</td></tr><tr><td>Annual list of violations</td><td>Driver's certification of violations</td></tr><tr><td>Drug & alcohol records</td><td>Testing results; clearinghouse queries</td></tr></table>
Atlas samples DQ files at survey for medium and larger fleets (DQ-0001 §23).
Cross-references: DQ-0001 §2, §23; LC-0004.
3. CDL, Endorsements, and Medical Certification
Drivers must hold the correct CDL class and endorsements for the equipment and cargo (e.g., N tank, H/X hazmat, T doubles/triples), maintain a current medical examiner's certificate, and not be subject to disqualification. Atlas verifies these at underwriting (UW-0001 §12; DQ-0001 §5).
<table><tr><th>Item</th><th>Compliance point</th></tr><tr><td>CDL class</td><td>Matches vehicle/operation</td></tr><tr><td>Endorsements</td><td>N/H/X/T as required</td></tr><tr><td>Medical certificate</td><td>Current; status reflected on CDL where required</td></tr><tr><td>Disqualification</td><td>No active interstate disqualification</td></tr></table>
WARNING. A hazmat (H/X) endorsement requires a current security threat assessment; an expired assessment invalidates the endorsement for hazmat operation even if the CDL is valid (DQ-0001 §22).
Cross-references: UW-0001 §12; DQ-0001 §5, §22.
4. Drug & Alcohol Program and Clearinghouse
Federally-regulated motor carriers must operate a drug-and-alcohol testing program (pre-employment, random, post-accident, reasonable-suspicion, return-to-duty/follow-up) and query/report to the federal drug-and-alcohol clearinghouse. Atlas assesses program adequacy as a control (DQ-0001 §7).
<table><tr><th>Element</th><th>Summary</th></tr><tr><td>Pre-employment test</td><td>Negative result before safety-sensitive duty</td></tr><tr><td>Random testing</td><td>At/above required rates</td></tr><tr><td>Post-accident / reasonable-suspicion</td><td>As triggered</td></tr><tr><td>Clearinghouse</td><td>Pre-employment + annual queries; violation reporting</td></tr><tr><td>Return-to-duty</td><td>Required before resuming safety-sensitive functions</td></tr></table>
Cross-references: DQ-0001 §7; REG-0005 (CSA Controlled-Substances BASIC).
5. DQ Compliance Checklist
• [ ] Complete DQ file per item list ($2)
• [ ] MVR at hire + annual review on file
• [ ] CDL class/endorsements verified for operation
• [ ] Current medical examiner's certificate; expiration tracked
• [ ] Road test/equivalent documented
• [ ] D&A program compliant; clearinghouse queries done
• [ ] No disqualified drivers in safety-sensitive roles
• [ ] Hazmat security assessments current (if applicable)
Cross-references: REG-0007; DQ-0001 §23.
6. Examples
EXAMPLE 1. A Loss Control survey samples 8 driver files; all contain the required items (DQ-0001 §23) – supporting both regulatory compliance and the driver schedule credit (UW-0001 §17).
EXAMPLE 2. A tanker fleet has drivers without the N endorsement; this is both a regulatory gap and an Atlas eligibility issue — drivers must be endorsed or excluded (UW-0001 §12; DQ-0001 §5).
7. Definitions and FAQ
7.1 Definitions
• DQ File: Federally-required driver qualification file.
• Clearinghouse: Federal drug-and-alcohol violation database.
• Medical Examiner's Certificate: Proof of medical fitness to drive.
• Disqualification: Loss of eligibility to operate a CMV.
7.2 FAQ
Q: Is the federal DQ file the same as Atlas's driver standards? A: No — the DQ file is the legal minimum; Atlas underwriting (DQ-0001) may require more.
Q: Who verifies endorsements? A: The carrier (compliance) and Atlas at underwriting (UW-0001 §12).
8. Revision History
<table><tr><th>Version</th><th>Date</th><th>Author</th><th>Change</th></tr><tr><td>1.0</td><td>2026-01-01</td><td>Regulatory & Compliance</td><td>Initial Driver Qualification Compliance Manual.</td></tr></table>
DOCUMENT CONTROL. REG-0004 v1.0 · Classification: Confidential — Internal Use Only · Effective
2026-01-01 · Owner: VP Regulatory & Compliance · Authoritative copy: Atlas Document Register
(ATLAS360). Uncontrolled when printed. © Atlas Commercial Insurance Company. Internal proprietary
material — do not distribute externally without authorization.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | 3          | 28974           | 2026-07-04 01:34:49.984554 | 7270448c12bc47fae6ca4045ec39597ba625526de35b8ec939a733602f4803d1 |
| 7b228a2307e3f806f8c5716920cec32a21bd36c440dc69ab6e7b399691b77f90 | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/15_regulatory/REG-0001_regulatory_compliance_framework.pdf         | REG-0001_regulatory_compliance_framework.pdf         | Regulatory & Compliance | 15_regulatory      | CONFIDENTIAL — INTERNAL USE ONLY · Classification: Confidential · Uncontrolled when printed — verify the current version in the Atlas Document Register (ATLAS360) before reliance.
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Regulatory & Compliance
Regulatory Compliance Framework
Document Control
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>REG-0001</td></tr><tr><td>Version</td><td>1.0</td></tr><tr><td>Status</td><td>Approved — In Force</td></tr><tr><td>Classification</td><td>Confidential — Internal Use Only</td></tr><tr><td>Document owner</td><td>VP Regulatory & Compliance</td></tr><tr><td>Approved by</td><td>Gerald Mphande, VP Regulatory & Compliance (2026-01-15); Margaret Holloway, President & CEO (2026-01-15)</td></tr><tr><td>Effective date</td><td>2026-01-01</td></tr><tr><td>Next scheduled review</td><td>2027-01-01</td></tr><tr><td>Supersedes</td><td>None</td></tr><tr><td>Distribution</td><td>All staff; Compliance; Underwriting; Claims; Loss Control; Internal Audit; Board Audit Committee</td></tr><tr><td>Related documents</td><td>REG-0002 through REG-0008; REF-0001 §15; REF-0003</td></tr><tr><td>Governing standard</td><td>REF-0003 Document Control & House Style</td></tr><tr><td>Supporting systems / forms</td><td>ATLAS360; Compliance register; regulatory-change log</td></tr></table>
NOTICE. Controlled document. This framework states Atlas's internal compliance program. It does not substitute for statutes, regulations, or filings; the law and filed items control. Two regulatory domains apply: (1) the insurance regulation of Atlas itself (REG-0008), and (2) the motor-carrier (FMCSA/DOT) regulation of Atlas's insureds, which Atlas references for underwriting, loss control, and claims (REG-0002 through REG-0006).
1. Purpose and Scope
This framework governs how Atlas identifies, interprets, implements, and monitors regulatory obligations across the enterprise. It coordinates two domains: Atlas's obligations as a regulated insurer (licensing, filings, market conduct, privacy — REG-0008) and the motor-carrier safety regulations that define Atlas's insureds' obligations and inform underwriting and loss control (DOT/FMCSS — REG-0002 to REG-0006).
Compliance is independent: the VP Regulatory & Compliance (Gerald Mphande) reports to the CEO and the Board Audit Committee (REF-0001 §14), preserving the ability to escalate without conflict.
CALLOUT. Atlas does not regulate its insureds. The motor-carrier manuals (REG-0002 to REG-0006) describe the federal framework so underwriters, loss-control engineers, and adjusters can assess an insured's compliance posture — a key risk signal — and help insureds improve.
Cross-references: REF-0001 §14, §15; REG-0008; REG-0002.
2. Governance and Roles
<table><tr><th>Body / role</th><th>Compliance responsibility</th></tr><tr><td>Board Audit Committee</td><td>Independent oversight of compliance</td></tr><tr><td>President & CEO</td><td>Accountable for compliance culture</td></tr><tr><td>VP Regulatory & Compliance (Mphande)</td><td>Owns the program; regulatory interpretation</td></tr><tr><td>Product & Compliance Committee (PCC)</td><td>Filings, forms, regulatory-change adoption</td></tr><tr><td>Compliance Analyst (Helen Ostrowski)</td><td>Monitoring, registers, training support</td></tr><tr><td>Business units (UW/Claims/LC)</td><td>Execute controls; report issues</td></tr><tr><td>Internal Audit</td><td>Independent testing</td></tr></table>
The Product & Compliance Committee (PCC, REF-0001 §15) is the operational forum for filings, form changes, and regulatory-change adoption.
Cross-references: REF-0001 §15; §3 Change Management.
3. Regulatory-Change Management
Monitor sources (federal/state regulators, bulletins, case law)
-> log change in regulatory-change register
-> assess impact (which docs/processes/filings affected)
-> PCC adopts: update filings/forms/manuals + set effective date
-> communicate + train affected staff
-> verify implementation; Internal Audit tests
Material changes trigger updates to the affected controlled documents (versioned per REF-0003) and, where needed, new rate/form filings (REG-0008).
Cross-references: REG-0008; REF-0003 §2.
4. Training and Recordkeeping
Compliance training is assigned by role (e.g., unfair-claims for adjusters, filings for product, privacy for all). Completion is tracked. Records — filings, complaints, audit findings, training, regulatory correspondence — are retained per the records-retention schedule (minimum 7 years; longer under legal hold). The Compliance register in ATLAS360 is the system of record.
Cross-references: REG-0008; REF-0001 §16.
5. Monitoring, Reporting, and Escalation
Compliance monitors KPIs (filing timeliness, complaint trends, unfair-claims adherence, training completion) and reports to the PCC, EXCO, and the Board Audit Committee. Issues are escalated promptly: potential violations are investigated, remediated, and self-reported to regulators where required, coordinated with Legal.
<table><tr><th>KPI</th><th>Target</th></tr><tr><td>Rate/form filing timeliness</td><td>100% on time</td></tr><tr><td>Regulatory-change adoption</td><td>Within required window</td></tr><tr><td>Complaint response timeliness</td><td>Within state timeframes</td></tr></table>
<table><tr><th>KPI</th><th>Target</th></tr><tr><td>Compliance training completion</td><td>≥ 98%</td></tr><tr><td>Open material findings</td><td>Remediated on schedule</td></tr></table>
Cross-references: REG-0008; §6 FAQ.
6. Definitions and FAQ
6.1 Definitions
• Compliance Register: ATLAS360 record of obligations, filings, complaints, findings.
• PCC: Product & Compliance Committee.
• Regulatory-Change Management: The process of adopting new/changed requirements.
• Market Conduct: Insurer behavior in sales, underwriting, and claims (REG-0008).
6.2 FAQ
Q: Why do underwriters need motor-carrier regulatory manuals? A: An insured's DOT/FMCSA compliance posture (ratings, CSA, HOS, DQ files) is a core risk signal used in underwriting and loss control (REG-0002 to REG-0006; UW-0001 §13).
Q: Who interprets a new regulation? A: Compliance, via the PCC, with Legal as needed; the change is logged, adopted, and communicated ($3).
Q: Where do unfair-claims and privacy rules live? A: In REG-0008 (insurance market conduct), referenced by Claims (CLM-0005/0007) and Loss Control (LC-0009).
7. Revision History
<table><tr><th>Version</th><th>Date</th><th>Author</th><th>Change</th></tr><tr><td>1.0</td><td>2026-01-01</td><td>Regulatory & Compliance</td><td>Initial Regulatory Compliance Framework; anchor for Section 15.</td></tr></table>
DOCUMENT CONTROL. REG-0001 v1.0 · Classification: Confidential — Internal Use Only · Effective
2026-01-01 · Owner: VP Regulatory & Compliance · Authoritative copy: Atlas Document Register
(ATLAS360). Uncontrolled when printed. © Atlas Commercial Insurance Company. Internal proprietary
material — do not distribute externally without authorization.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 3          | 31597           | 2026-07-04 01:34:49.984554 | 7b228a2307e3f806f8c5716920cec32a21bd36c440dc69ab6e7b399691b77f90 |
| 5875969667dc887ec54113bd646ab49a872f79794491ed29cbc6fc95755fe46a | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/15_regulatory/REG-0005_safety_audits_csa_intervention_manual.pdf   | REG-0005_safety_audits_csa_intervention_manual.pdf   | Regulatory & Compliance | 15_regulatory      | CONFIDENTIAL — INTERNAL USE ONLY · Classification: Confidential · Uncontrolled when printed — verify the current version in the Atlas Document Register (ATLAS360) before reliance.
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Regulatory & Compliance
Safety Audits and CSA Intervention Manual
Document Control
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>REG-0005</td></tr><tr><td>Version</td><td>1.0</td></tr><tr><td>Status</td><td>Approved — In Force</td></tr><tr><td>Classification</td><td>Confidential — Internal Use Only (insured guidance extracts issued separately)</td></tr><tr><td>Document owner</td><td>VP Regulatory & Compliance</td></tr><tr><td>Approved by</td><td>Gerald Mphande, VP Regulatory & Compliance (2026-01-15); Karen Whitlock, VP Loss Control & Safety (2026-01-15)</td></tr><tr><td>Effective date</td><td>2026-01-01</td></tr><tr><td>Next scheduled review</td><td>2027-01-01</td></tr><tr><td>Supersedes</td><td>None</td></tr><tr><td>Distribution</td><td>Compliance; Underwriting; Loss Control; insured guidance extracts (redacted)</td></tr><tr><td>Related documents</td><td>REG-0001/0002; UW-0001 §13; LC-0013; REF-0001</td></tr><tr><td>Governing standard</td><td>REF-0003 Document Control & House Style</td></tr><tr><td>Supporting systems / forms</td><td>ATLAS360; CSA/SMS snapshot</td></tr></table>
NOTICE. Controlled document. CSA/SMS and FMCSA audit processes are federal; summarized here for risk assessment. Atlas's interpretation thresholds (UW-0001 §13) are internal underwriting guides, not federal intervention thresholds. The federal program controls.
1. Purpose
This manual summarizes the FMCSA's safety-oversight tools — new-entrant safety audits, compliance reviews/investigations, and the CSA (Compliance, Safety, Accountability) program with its SMS BASICS — so Atlas can interpret an insured's safety data. CSA percentiles are leading indicators central to Atlas underwriting (UW-0001 §13) and the Safety Audit (LC-0013).
CALLOUT. CSA does not assign a "score" Atlas can read literally; Atlas interprets BASIC percentiles and trends as risk signals against internal watch thresholds (UW-0001 §13.2).
Cross-references: UW-0001 §13; LC-0013; REG-0002 §4.
2. FMCSA Audits and Reviews
<table><tr><th>Oversight tool</th><th>Summary</th></tr><tr><td>New-entrant safety audit</td><td>Early-life audit of new carriers' safety management</td></tr><tr><td>Compliance review / investigation</td><td>On-site/off-site review of records and practices</td></tr><tr><td>Safety rating</td><td>Satisfactory / Conditional / Unsatisfactory (REG-0002 §4)</td></tr><tr><td>Out-of-service order</td><td>Prohibition pending correction of serious deficiencies</td></tr></table>
A carrier that fails a new-entrant audit or receives an adverse rating signals elevated risk (UW-0001 §13.1; REG-0002 §4).
Cross-references: REG-0002 §4; UW-0001 §13.1.
3. CSA / SMS BASIC Categories
The Safety Measurement System organizes roadside and crash data into seven Behavior Analysis and Safety Improvement Categories (BASICs). Atlas's internal watch thresholds (UW-0001 §13.2) are restated here for reference.
<table><tr><th>BASIC</th><th>Atlas watch threshold (refer if exceeded)</th></tr><tr><td>Unsafe Driving</td><td>65th percentile</td></tr><tr><td>Hours-of-Service Compliance</td><td>65th</td></tr><tr><td>Driver Fitness</td><td>80th</td></tr><tr><td>Controlled Substances/Alcohol</td><td>Any alert = refer</td></tr><tr><td>Vehicle Maintenance</td><td>75th</td></tr><tr><td>Hazmat Compliance</td><td>75th</td></tr><tr><td>Crash Indicator</td><td>65th</td></tr></table>
WARNING. Two or more elevated BASICs, or any Controlled Substances/Alcohol alert, requires referral and typically a pre-bind loss-control survey (UW-0001 §13.3, §23).
Cross-references: UW-0001 §13.2–§13.3, §23.
4. Interventions and Remediation
The FMCSA applies escalating interventions (warning letters, investigations, corrective-action requirements, and penalties) to carriers with elevated BASICS or violations. For underwriting, Atlas favors carriers that respond with documented remediation and improving trends; a single elevated BASIC with a corrective plan is generally manageable with a debit and engagement (UW-0001 §13.3).
Elevated BASIC / violation
-> FMCSA intervention (letter / investigation / CAP)
-> carrier remediation
-> Atlas view: improving trend + plan = manageable; worsening/no plan = refer/decline
Cross-references: UW-0001 §13.3; LC-0013 (audit scoring).
5. CSA / Audit Readiness Checklist
• [ ] CSA/SMS snapshot reviewed; BASIC percentiles noted
• [ ] No Controlled Substances/Alcohol alert (or fully remediated)
• [ ] ≤ 1 elevated BASIC, with improving trend + plan
• [ ] Safety rating acceptable (REG-0002 §4)
• [ ] New-entrant audit passed (if applicable)
• [ ] Roadside OOS rates below national average
• [ ] Documented corrective-action plan for any deficiency
• [ ] Loss Control survey where thresholds exceeded
Cross-references: REG-0007; LC-0013; UW-0001 §13.
6. Examples
EXAMPLE 1. Cardinal Long Haul shows Unsafe Driving at the 68th percentile but improving with full ELD and cameras; manageable with a debit, telematics-credit offset, and a 90-day loss-control check-in (UW-0001 §31 Case B).
EXAMPLE 2. A carrier with elevated Vehicle Maintenance and Unsafe Driving BASICs and no corrective plan is referred and surveyed; absent remediation, the risk is declined (UW-0001 §13.3).
7. Definitions and FAQ
7.1 Definitions
• CSA: Compliance, Safety, Accountability — FMCSA's safety-oversight program.
• SMS: Safety Measurement System.
• BASIC: Behavior Analysis and Safety Improvement Category (seven categories).
• Compliance Review: FMCSA examination of a carrier's safety management.
7.2 FAQ
Q: Can Atlas see a carrier's "CSA score"? A: Atlas reviews BASIC percentiles and trends, not a single score, and applies internal watch thresholds (UW-0001 §13.2).
Q: Does one elevated BASIC mean decline? A: No — one elevated BASIC with an improving trend and plan is generally manageable; two+ or a drug/alcohol alert triggers referral (UW-0001 §13.3).
8. Revision History
<table><tr><th>Version</th><th>Date</th><th>Author</th><th>Change</th></tr><tr><td>1.0</td><td>2026-01-01</td><td>Regulatory & Compliance</td><td>Initial Safety Audits and CSA Intervention Manual.</td></tr></table>
DOCUMENT CONTROL. REG-0005 v1.0 · Classification: Confidential — Internal Use Only · Effective
2026-01-01 · Owner: VP Regulatory & Compliance · Authoritative copy: Atlas Document Register
(ATLAS360). Uncontrolled when printed. © Atlas Commercial Insurance Company. Internal proprietary
material — do not distribute externally without authorization.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | 3          | 32207           | 2026-07-04 01:34:49.984554 | 5875969667dc887ec54113bd646ab49a872f79794491ed29cbc6fc95755fe46a |
| f37bbd529f54296c044b6eb9465bbc434d8703c341e2cd6354abfa42d6a8211a | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0100.pdf                                    | MIN-0100.pdf                                         | Meeting Minutes         | 14_meeting_minutes | CONFIDENTIAL — COMMITTEE RECORD · Classification: Confidential — Internal Use Only · Uncontrolled when printed — minutes of record held by the Corporate Secretary (ATLAS360).
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Portfolio Management Committee
Portfolio Management Committee — Renewals
Minutes
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>MIN-0100</td></tr><tr><td>Committee</td><td>Portfolio Management Committee</td></tr><tr><td>Meeting type</td><td>Renewals</td></tr><tr><td>Date</td><td>2025-08-10</td></tr><tr><td>Chair</td><td>David Okafor, Chief Underwriting Officer</td></tr><tr><td>Classification</td><td>Confidential — Internal Use Only</td></tr><tr><td>References</td><td>ACI-AL-25-605475, ACI-AL-26-398859, ACI-AL-26-752525</td></tr><tr><td>Governing standards</td><td>REF-0001 §15; UW-0001; CLM/RA/AUTH as cited</td></tr></table>
1. Attendance
• David Okafor (CUO)
• Vikram Sethi (Chief Actuary)
• Theresa Vandermeer (VP UW National Accounts)
• Susan Brandt-Mireles (CFO)
2. Minutes / Discussion
1. Renewal disposition ACI-AL-25-605475 (Yellowstone Transport Co., TAP $844,790) — non-renew (UW-0001 $26).
2. Renewal disposition ACI-AL-26-398859 (Ridgeline Trucking Corp., TAP $20,927) — renew with rate + controls (UW-0001 $26).
3. Renewal disposition ACI-AL-26-752525 (Rampart Logistics Co., TAP $745,677) — non-renew (UW-0001 $26).
3. Decisions
• Renewal pipeline on track; non-renewals to issue timely state notices (REG-0008).
4. Action Items
<table><tr><th>Owner</th><th>Action</th><th>Due</th></tr><tr><td>Regional UW Directors</td><td>Complete 60-day renewal handoffs; engage loss control on watch accounts</td><td>ongoing</td></tr></table>
5. Next Meeting
Scheduled 2025-08-17. Minutes approved as recorded; distributed to committee members.
DOCUMENT CONTROL. MIN-0100 v1.0 · Portfolio Management Committee · Classification: Confidential
— Internal Use Only · 2025-08-10 · Owner: Corporate Secretary · Authoritative copy: Atlas Document Register (ATLAS360). Uncontrolled when printed. © Atlas Commercial Insurance Company.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | 2          | 19710           | 2026-07-04 01:34:49.984554 | f37bbd529f54296c044b6eb9465bbc434d8703c341e2cd6354abfa42d6a8211a |
| bae95a40517e6bb254de1fab40c4d3dbae4a74ed1b0c8436fe6542beb4c588d6 | dbfs:/Volumes/atlas/commercial_insurance_rag/raw_documents/14_meeting_minutes/MIN-0097.pdf                                    | MIN-0097.pdf                                         | Meeting Minutes         | 14_meeting_minutes | RESTRICTED — COMMITTEE RECORD · Classification: Restricted · Uncontrolled when printed — minutes of record held by the Corporate Secretary (ATLAS360).
ATLAS COMMERCIAL INSURANCE COMPANY 401 North Wacker Drive, Suite 2200 · Chicago, Illinois
60606 Catastrophe & Accumulation Committee
Catastrophe & Accumulation Committee —
Catastrophe Review Minutes
<table><tr><th>Field</th><th>Detail</th></tr><tr><td>Document ID</td><td>MIN-0097</td></tr><tr><td>Committee</td><td>Catastrophe & Accumulation Committee</td></tr><tr><td>Meeting type</td><td>Catastrophe Review</td></tr><tr><td>Date</td><td>2025-07-22</td></tr><tr><td>Chair</td><td>Raymond Tessier, Chief Risk Officer</td></tr><tr><td>Classification</td><td>Restricted</td></tr><tr><td>References</td><td>CLM-25-2613755, CLM-24-2618602</td></tr><tr><td>Governing standards</td><td>REF-0001 §15; UW-0001; CLM/RA/AUTH as cited</td></tr></table>
1. Attendance
• Raymond Tessier (CRO)
• David Okafor (CUO)
• Vikram Sethi (Chief Actuary)
• Susan Brandt-Mireles (CFO)
• Karen Whitlock (VP Loss Control)
2. Minutes / Discussion
1. Event/severity review of CLM-25-2613755 (Big Sky Tankers LLC, Rollover with product release) — incurred $551,000. Accumulation against treaty assessed (CLM-0002; RA-0001 $20).
2. Event/severity review of CLM-24-2618602 (Foundry Trucking Co., Jackknife — adverse weather) — incurred $334,000. Accumulation against treaty assessed (CLM-0002; RA-0001 $20).
3. Reviewed concentration in Tier C/D freight corridors and Gulf/Plains seasonal exposure; no treaty breach this period.
3. Decisions
• Accumulation within treaty tolerance; continue monitoring hazmat/tanker corridors and coastal PD.
4. Action Items
<table><tr><th>Owner</th><th>Action</th><th>Due</th></tr><tr><td>CRO (R. Tessier)</td><td>Refresh accumulation dashboard; confirm reinsurance recoverables</td><td>monthly</td></tr></table>
5. Next Meeting
Scheduled 2025-07-29. Minutes approved as recorded; distributed to committee members.
DOCUMENT CONTROL. MIN-0097 v1.0 · Catastrophe & Accumulation Committee · Classification:
Restricted · 2025-07-22 · Owner: Corporate Secretary · Authoritative copy: Atlas Document Register (ATLAS360). Uncontrolled when printed. © Atlas Commercial Insurance Company.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | 2          | 20299           | 2026-07-04 01:34:49.984554 | bae95a40517e6bb254de1fab40c4d3dbae4a74ed1b0c8436fe6542beb4c588d6 |

---

## `policies`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.policies (
  policy_id STRING COLLATE UTF8_BINARY NOT NULL,
  insured_id STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'FK to insureds',
  line_of_business STRING COLLATE UTF8_BINARY,
  policy_status STRING COLLATE UTF8_BINARY COMMENT 'Active, Expired, Cancelled, Non-Renewed',
  effective_date DATE,
  expiration_date DATE,
  written_premium DECIMAL(12,2),
  liability_limit STRING COLLATE UTF8_BINARY,
  aggregate_limit STRING COLLATE UTF8_BINARY,
  deductible DECIMAL(10,2),
  vehicles_covered INT,
  territory STRING COLLATE UTF8_BINARY,
  broker_name STRING COLLATE UTF8_BINARY,
  underwriter STRING COLLATE UTF8_BINARY,
  renewal_status STRING COLLATE UTF8_BINARY COMMENT 'Auto-Renew, Review Required, Non-Renew',
  loss_ratio_current DECIMAL(5,2),
  CONSTRAINT `pk_policies` PRIMARY KEY (`policy_id`))
USING delta
COMMENT 'Insurance policies'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 15)

| policy_id        | insured_id | line_of_business  | policy_status | effective_date | expiration_date | written_premium | liability_limit | aggregate_limit | deductible | vehicles_covered | territory | broker_name                     | underwriter     | renewal_status  | loss_ratio_current |
| ---------------- | ---------- | ----------------- | ------------- | -------------- | --------------- | --------------- | --------------- | --------------- | ---------- | ---------------- | --------- | ------------------------------- | --------------- | --------------- | ------------------ |
| ACI-AL-25-732053 | INS-1001   | Auto Liability    | Active        | 2025-03-15     | 2026-03-15      | 425000.00       | 1,000,000 CSL   | 2,000,000       | 5000.00    | 85               | IL        | Midwest Transport Advisors      | Sarah Mitchell  | Auto-Renew      | 32.50              |
| ACI-PD-25-732054 | INS-1001   | Physical Damage   | Active        | 2025-03-15     | 2026-03-15      | 185000.00       | ACV             |                 | 2500.00    | 85               | IL        | Midwest Transport Advisors      | Sarah Mitchell  | Auto-Renew      | 28.10              |
| ACI-MC-25-732055 | INS-1001   | Motor Truck Cargo | Active        | 2025-03-15     | 2026-03-15      | 42000.00        | 250,000         | 500,000         | 1000.00    | 85               | IL        | Midwest Transport Advisors      | Sarah Mitchell  | Auto-Renew      | 15.20              |
| ACI-AL-25-845210 | INS-1002   | Auto Liability    | Active        | 2025-07-01     | 2026-07-01      | 298000.00       | 1,000,000 CSL   | 2,000,000       | 10000.00   | 42               | CA        | Golden State Insurance Partners | James Rodriguez | Review Required | 55.80              |
| ACI-PD-25-845211 | INS-1002   | Physical Damage   | Active        | 2025-07-01     | 2026-07-01      | 112000.00       | ACV             |                 | 5000.00    | 42               | CA        | Golden State Insurance Partners | James Rodriguez | Review Required | 42.30              |
| ACI-AL-25-690117 | INS-1003   | Auto Liability    | Active        | 2025-11-20     | 2026-11-20      | 520000.00       | 2,000,000 CSL   | 5,000,000       | 10000.00   | 35               | TX        | Energy Risk Brokers             | Sarah Mitchell  | Auto-Renew      | 22.40              |
| ACI-MC-25-690118 | INS-1003   | Motor Truck Cargo | Active        | 2025-11-20     | 2026-11-20      | 95000.00        | 1,000,000       | 2,000,000       | 5000.00    | 35               | TX        | Energy Risk Brokers             | Sarah Mitchell  | Auto-Renew      | 18.60              |
| ACI-AL-26-901445 | INS-1004   | Auto Liability    | Active        | 2026-01-10     | 2027-01-10      | 680000.00       | 1,000,000 CSL   | 2,000,000       | 5000.00    | 120              | OH        | National Fleet Insurance Group  | David Chen      | Auto-Renew      | 38.90              |
| ACI-AL-25-553872 | INS-1005   | Auto Liability    | Active        | 2025-04-01     | 2026-04-01      | 78000.00        | 1,000,000 CSL   | 1,000,000       | 10000.00   | 18               | TX        | Southwest Commercial Brokerage  | James Rodriguez | Review Required | 72.40              |
| ACI-AL-25-618934 | INS-1006   | Auto Liability    | Active        | 2025-06-15     | 2026-06-15      | 345000.00       | 1,000,000 CSL   | 2,000,000       | 5000.00    | 65               | CO        | Rocky Mountain Risk Partners    | David Chen      | Auto-Renew      | 28.70              |

---

## `subjectivity_status`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.subjectivity_status (
  status_id STRING COLLATE UTF8_BINARY NOT NULL,
  submission_id STRING COLLATE UTF8_BINARY NOT NULL,
  item STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'Subjectivity text',
  status STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'Open, Received, Waived',
  note STRING COLLATE UTF8_BINARY,
  cleared_by STRING COLLATE UTF8_BINARY,
  updated_at TIMESTAMP,
  CONSTRAINT `pk_subjectivity_status` PRIMARY KEY (`status_id`))
USING delta
COMMENT 'Append-only log of subjectivity clearing; latest row per (submission_id, item) wins.'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (0 of 0)

_No rows_

---

## `submissions`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.submissions (
  submission_id STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'SUB-YY-NNNNN',
  insured_id STRING COLLATE UTF8_BINARY,
  company_name STRING COLLATE UTF8_BINARY,
  broker_name STRING COLLATE UTF8_BINARY,
  broker_contact STRING COLLATE UTF8_BINARY,
  submission_date DATE,
  target_effective DATE,
  submission_status STRING COLLATE UTF8_BINARY COMMENT 'Received, In Review, Quoted, Bound, Declined, Lost',
  fleet_size INT,
  driver_count INT,
  primary_operation STRING COLLATE UTF8_BINARY,
  primary_commodity STRING COLLATE UTF8_BINARY,
  requested_limits STRING COLLATE UTF8_BINARY,
  expiring_premium DECIMAL(12,2),
  quoted_premium DECIMAL(12,2),
  loss_ratio_3yr DECIMAL(5,2),
  underwriter STRING COLLATE UTF8_BINARY,
  referral_required BOOLEAN,
  decline_reason STRING COLLATE UTF8_BINARY,
  days_to_quote INT,
  CONSTRAINT `pk_submissions` PRIMARY KEY (`submission_id`))
USING delta
COMMENT 'Broker submission pipeline'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (9 of 9)

| submission_id | insured_id | company_name                  | broker_name                             | broker_contact  | submission_date | target_effective | submission_status | fleet_size | driver_count | primary_operation | primary_commodity   | requested_limits | expiring_premium | quoted_premium | loss_ratio_3yr | underwriter     | referral_required | decline_reason                                                                                            | days_to_quote |
| ------------- | ---------- | ----------------------------- | --------------------------------------- | --------------- | --------------- | ---------------- | ----------------- | ---------- | ------------ | ----------------- | ------------------- | ---------------- | ---------------- | -------------- | -------------- | --------------- | ----------------- | --------------------------------------------------------------------------------------------------------- | ------------- |
| SUB-26-11099  |            | Rockford Grain Transport LLC  | Heartland Specialty Insurance           | Tom Berkowitz   | 2026-06-15      | 2026-08-01       | In Review         | 28         | 32           | Regional          | Dry Bulk/Grain      | 1,000,000 CSL    | 145000.00        |                | 38.20          | David Chen      | False             |                                                                                                           | nan           |
| SUB-26-11102  |            | Coastal Petroleum Haulers Inc | Energy Risk Brokers                     | Rachel Kim      | 2026-06-20      | 2026-09-01       | Received          | 15         | 18           | Intermediate      | Petroleum/Chemicals | 2,000,000 CSL    | 280000.00        |                | 25.80          |                 | True              |                                                                                                           | nan           |
| SUB-26-11087  | INS-1014   | Dixie Express Lines           | Southeast Transport Brokerage           | Bill Masters    | 2026-06-01      | 2026-08-15       | Quoted            | 52         | 58           | Long Haul         | General Freight     | 1,000,000 CSL    | 310000.00        | 345000.00      | 52.10          | James Rodriguez | False             |                                                                                                           | 8.0           |
| SUB-26-11078  |            | Metro Moving and Storage      | Atlantic Specialty Brokers              | Linda Garcia    | 2026-05-20      | 2026-07-01       | Declined          | 8          | 10           | Local             | Household Goods     | 1,000,000 CSL    | 42000.00         |                | 95.30          | Sarah Mitchell  | False             | Loss ratio exceeds 90% for 3 consecutive years. Fleet has 2 excluded drivers out of 10 total.             | nan           |
| SUB-26-11065  | INS-1002   | Pacific Coast Carriers Inc    | Golden State Insurance Partners         | Steve Yamamoto  | 2026-05-01      | 2026-07-01       | Quoted            | 42         | 48           | Long Haul         | Refrigerated        | 1,000,000 CSL    | 298000.00        | 325000.00      | 48.90          | James Rodriguez | True              |                                                                                                           | 12.0          |
| SUB-26-11045  |            | Appalachian Coal Transport    | Mountain State Risk                     | Jim Hartley     | 2026-04-15      | 2026-06-01       | Declined          | 30         | 35           | Regional          | Coal/Mining         | 1,000,000 CSL    | 195000.00        |                | 78.50          | David Chen      | True              | CSA Unsafe Driving above 75th percentile. Two DOT OOS inspections in past 6 months. Driver turnover >80%. | nan           |
| SUB-26-11110  |            | Precision LTL Carriers        | National Fleet Insurance Group          | Amy Patel       | 2026-06-25      | 2026-09-01       | Received          | 75         | 82           | Regional          | LTL Mixed           | 1,000,000 CSL    | 425000.00        |                | 35.40          |                 | False             |                                                                                                           | nan           |
| SUB-26-10998  | INS-1006   | Mountain West Freight Systems | Rocky Mountain Risk Partners            | Dan Kellogg     | 2026-03-15      | 2026-06-15       | Bound             | 65         | 72           | Regional          | General Freight     | 1,000,000 CSL    | 345000.00        | 355000.00      | 28.70          | David Chen      | False             |                                                                                                           | 5.0           |
| SUB-26-12077  | INS-1013   | Ironhorse Freight Systems LLC | Great Lakes Transport Insurance Brokers | Renata Kowalski | 2026-06-25      | 2026-08-15       | In Review         | 8          | 8            | Regional          | General Freight     | 1,000,000 CSL    |                  |                | 66.00          | David Chen      | False             |                                                                                                           | nan           |

---

## `underwriting_referrals`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.underwriting_referrals (
  referral_id STRING COLLATE UTF8_BINARY NOT NULL,
  submission_id STRING COLLATE UTF8_BINARY,
  policy_id STRING COLLATE UTF8_BINARY,
  insured_id STRING COLLATE UTF8_BINARY NOT NULL,
  referral_date DATE,
  referral_reason STRING COLLATE UTF8_BINARY,
  referral_tier STRING COLLATE UTF8_BINARY COMMENT 'Claims Director, VP UW, CCO, Reserve Committee',
  requesting_underwriter STRING COLLATE UTF8_BINARY,
  approving_authority STRING COLLATE UTF8_BINARY,
  decision STRING COLLATE UTF8_BINARY COMMENT 'Approved, Approved with Conditions, Declined',
  conditions STRING COLLATE UTF8_BINARY,
  decision_date DATE,
  notes STRING COLLATE UTF8_BINARY,
  CONSTRAINT `pk_referrals` PRIMARY KEY (`referral_id`))
USING delta
COMMENT 'Underwriting referrals requiring elevated authority'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (5 of 5)

| referral_id | submission_id | policy_id        | insured_id | referral_date | referral_reason | referral_tier     | requesting_underwriter | approving_authority | decision                 | conditions                                                                                                                       | decision_date | notes                                                                                                                                                                                             |
| ----------- | ------------- | ---------------- | ---------- | ------------- | --------------- | ----------------- | ---------------------- | ------------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| REF-26-001  | SUB-26-11065  |                  | INS-1002   | 2026-05-10    | Loss History    | VP UW             | James Rodriguez        | VP Karen Wallace    | Approved with Conditions | Rate increase minimum 15%. Add $15K deductible. Require driver DRV-2013 remediation plan within 60 days or exclusion at renewal. | 2026-05-14    | Three-year trend deteriorating. Large open BI claim CLM-25-3891045 at $385K. Fleet cooperating on safety improvements.                                                                            |
| REF-26-002  | SUB-26-11102  |                  | INS-1002   | 2026-06-22    | Risk Appetite   | CCO               | David Chen             |                     |                          |                                                                                                                                  |               | HAZMAT fleet, 15 units. Clean history but requires elevated authority per commodity class. Awaiting CCO review.                                                                                   |
| REF-26-003  |               | ACI-AL-25-778321 | INS-1007   | 2026-05-01    | CSA Scores      | VP UW             | Sarah Mitchell         | VP Karen Wallace    | Declined                 |                                                                                                                                  | 2026-05-05    | Non-renewal recommended. CSA Unsafe Driving 52.1 percentile, Vehicle Maintenance 55.3. Conditional DOT rating. 85% loss ratio current term with two large losses. SIU referral on CLM-25-4522103. |
| REF-25-015  | SUB-26-11045  |                  | INS-1005   | 2025-12-10    | Loss History    | VP UW             | David Chen             | VP Karen Wallace    | Declined                 |                                                                                                                                  | 2025-12-12    | Appalachian Coal: CSA Unsafe Driving above 75th percentile. Two DOT out-of-service inspections in past 6 months. Driver turnover exceeds 80%.                                                     |
| REF-26-004  |               | ACI-AL-25-553872 | INS-1005   | 2026-06-01    | Loss History    | Reserve Committee | James Rodriguez        |                     |                          |                                                                                                                                  |               | Catastrophic claim CLM-25-1098891 ($650K incurred, fatality). Referring for Reserve Committee review and potential non-renewal. Current-term loss ratio now exceeds 1100%.                        |

---

## `vehicles`

### CREATE TABLE

```sql
CREATE TABLE atlas.atlas_insurance_rag.vehicles (
  vehicle_id STRING COLLATE UTF8_BINARY NOT NULL COMMENT 'VEH-NNNN',
  insured_id STRING COLLATE UTF8_BINARY NOT NULL,
  policy_id STRING COLLATE UTF8_BINARY,
  vin STRING COLLATE UTF8_BINARY,
  year INT,
  make STRING COLLATE UTF8_BINARY,
  model STRING COLLATE UTF8_BINARY,
  vehicle_type STRING COLLATE UTF8_BINARY,
  gvw INT,
  stated_value DECIMAL(10,2),
  radius_class STRING COLLATE UTF8_BINARY,
  garage_state STRING COLLATE UTF8_BINARY,
  garage_zip STRING COLLATE UTF8_BINARY,
  has_dashcam BOOLEAN,
  has_eld BOOLEAN,
  last_inspection_date DATE,
  inspection_result STRING COLLATE UTF8_BINARY COMMENT 'Pass, Conditional, Fail',
  annual_mileage INT,
  CONSTRAINT `pk_vehicles` PRIMARY KEY (`vehicle_id`))
USING delta
COMMENT 'Fleet vehicle inventory'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.changeDataFeed' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')

```

### Sample rows (10 of 13)

| vehicle_id | insured_id | policy_id        | vin               | year | make          | model    | vehicle_type    | gvw   | stated_value | radius_class | garage_state | garage_zip | has_dashcam | has_eld | last_inspection_date | inspection_result | annual_mileage |
| ---------- | ---------- | ---------------- | ----------------- | ---- | ------------- | -------- | --------------- | ----- | ------------ | ------------ | ------------ | ---------- | ----------- | ------- | -------------------- | ----------------- | -------------- |
| VEH-3001   | INS-1001   | ACI-AL-25-732053 | 1XKYDP9X5RJ456789 | 2023 | Kenworth      | T680     | Sleeper Tractor | 80000 | 165000.00    | Regional     | IL           | 62704      | True        | True    | 2026-04-15           | Pass              | 115000         |
| VEH-3002   | INS-1001   | ACI-AL-25-732053 | 3AKJHHDR4NSAB1234 | 2022 | Freightliner  | Cascadia | Sleeper Tractor | 80000 | 148000.00    | Regional     | IL           | 62704      | True        | True    | 2026-04-15           | Pass              | 120000         |
| VEH-3003   | INS-1001   | ACI-AL-25-732053 | 1XPBDP9X8MD567890 | 2024 | Peterbilt     | 579      | Day Cab         | 80000 | 172000.00    | Intermediate | MO           | 63101      | True        | True    | 2026-04-15           | Pass              | 95000          |
| VEH-3004   | INS-1001   | ACI-AL-25-732053 | 5PVNJ8JT2H4S12345 | 2021 | Volvo         | VNL 860  | Sleeper Tractor | 80000 | 135000.00    | Regional     | IN           | 46201      | True        | True    | 2026-03-20           | Pass              | 130000         |
| VEH-3010   | INS-1002   | ACI-AL-25-845210 | 1XKYD49X9PJ789012 | 2020 | Kenworth      | T680     | Sleeper Tractor | 80000 | 118000.00    | Long Haul    | CA           | 92335      | True        | True    | 2025-11-10           | Pass              | 145000         |
| VEH-3011   | INS-1002   | ACI-AL-25-845210 | 3AKJGLDR7LSCD5678 | 2019 | Freightliner  | Cascadia | Sleeper Tractor | 80000 | 95000.00     | Long Haul    | CA           | 92335      | False       | True    | 2025-11-10           | Conditional       | 152000         |
| VEH-3012   | INS-1002   | ACI-AL-25-845210 | 4V4NC9EH5EN345678 | 2018 | Volvo         | VNR 300  | Reefer          | 54000 | 82000.00     | Long Haul    | AZ           | 85001      | False       | True    | 2025-09-22           | Conditional       | 138000         |
| VEH-3020   | INS-1003   | ACI-AL-25-690117 | 1XPYD49X2RJ901234 | 2024 | Peterbilt     | 567      | Day Cab         | 80000 | 185000.00    | Regional     | TX           | 77001      | True        | True    | 2026-05-01           | Pass              | 85000          |
| VEH-3021   | INS-1003   | ACI-AL-25-690117 | 1XKAD49X6SJ012345 | 2023 | Kenworth      | T880     | Day Cab         | 80000 | 195000.00    | Regional     | TX           | 77001      | True        | True    | 2026-05-01           | Pass              | 78000          |
| VEH-3030   | INS-1005   | ACI-AL-25-553872 | 3HSDJAPR8CN567890 | 2017 | International | LT       | Day Cab         | 73000 | 62000.00     | Local        | TX           | 75201      | False       | True    | 2025-08-12           | Conditional       | 68000          |

---
