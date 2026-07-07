# Underwriting Domain Knowledge — Commercial Trucking Insurance

> **Audience:** Anyone building, maintaining, or using the UW CoPilot. Written so, a non technical resource could understand it, with real-world analogies and examples drawn
> directly from the Atlas Commercial Insurance reference data.

---

## Table of Contents

1. [What Is Insurance (30-Second Version)](#1-what-is-insurance-30-second-version)
2. [What Is Underwriting](#2-what-is-underwriting)
3. [The Players — Who Does What](#3-the-players--who-does-what)
4. [The UW Lifecycle — End to End](#4-the-uw-lifecycle--end-to-end)
5. [Step 1: Submission — "We Want Insurance"](#step-1-submission)
6. [Step 2: Information Gathering — "Show Me the Receipts"](#step-2-information-gathering)
7. [Step 3: Risk Assessment — "How Likely Are They to Crash?"](#step-3-risk-assessment)
8. [Step 4: Pricing — "How Much to Charge?"](#step-4-pricing)
9. [Step 5: The Decision — "Yes, No, or Yes-But"](#step-5-the-decision)
10. [Step 6: Referrals — "I Need My Boss's Approval"](#step-6-referrals)
11. [Step 7: Binding — "Handshake Done"](#step-7-binding)
12. [Step 8: Claims — "The Accident Happened"](#step-8-claims)
13. [Step 9: Renewal — "Do We Keep This Customer?"](#step-9-renewal)
14. [Key Metrics Every UW Watches](#key-metrics-every-uw-watches)
15. [Document Types and What They Contain](#document-types-and-what-they-contain)
16. [Lines of Business (Coverage Types)](#lines-of-business-coverage-types)
17. [Risk Tiers — The Report Card](#risk-tiers--the-report-card)
18. [Regulatory Bodies — The Government Referees](#regulatory-bodies--the-government-referees)
19. [Glossary of Key Terms](#glossary-of-key-terms)
20. [How the CoPilot Fits In](#how-the-copilot-fits-in)

---

## 1. What Is Insurance (30-Second Version)

Insurance is a **trade of certainty for uncertainty**.

A trucking company faces a scary possibility: one of their trucks might crash tomorrow
and they'd owe someone $1,000,000. They can't budget for that — it's too unpredictable.

So they go to an insurance company (Atlas) and say:

> "We'll pay you $325,000 every year — guaranteed. In exchange, if we crash and owe
> someone up to $1,000,000, YOU pay it instead of us."

Atlas collects these guaranteed payments (premiums) from hundreds of trucking companies.
Most years, most companies don't crash. So Atlas collects more money than it pays out.
That difference is profit.

**Daily life analogy:** It's like a neighborhood potluck fund. Everyone puts in $50/month.
When someone's house floods, the fund pays for repairs. Most months nothing happens, so
the fund grows. The "underwriter" is the person who decides who gets to join the potluck
and how much they should contribute.

---

## 2. What Is Underwriting

Underwriting is the **decision-making process** of:

1. **Should we insure this company?** (Selection)
2. **How much should we charge?** (Pricing)
3. **Under what conditions?** (Terms & Conditions)

Think of the underwriter as a **bank loan officer** — but instead of asking "will they
pay us back?", they're asking "will they crash and cost us money?"

**Another analogy:** Imagine you're the captain of a basketball team picking players.
You look at their stats (scoring average, fouls, attendance) and decide:
- "Yes, I want them on my team" → Accept
- "No, they'll hurt us" → Decline
- "Maybe, but only if they promise to practice 3x/week" → Accept with conditions

That's underwriting. The "stats" are things like accident history, driver records, truck
conditions, and government safety scores.

---

## 3. The Players — Who Does What

### The Insured (Customer)
The trucking company seeking insurance. In Atlas:

| Company | Fleet | Hauls | Risk Tier |
| --- | --- | --- | --- |
| Heartland Express Logistics | 85 trucks | General Freight | Preferred |
| Pacific Coast Carriers | 42 trucks | Refrigerated Food | Acceptable |
| Summit Petroleum Transport | 35 trucks | Petroleum/Chemicals | Preferred |
| Great Lakes Intermodal | 120 trucks | Containers | Acceptable |
| Lone Star Hauling Partners | 18 trucks | Construction Materials | Borderline |

### The Broker (Middleman)
A licensed agent who represents the trucking company. They shop around to multiple
insurance companies to find the best deal. Think of them as a real estate agent — they
don't own the house, they just help find the best match.

Examples from Atlas data:
- "Midwest Transport Advisors" (represents Heartland Express)
- "Golden State Insurance Partners" (represents Pacific Coast Carriers)
- "Energy Risk Brokers" (represents petroleum haulers)

### The Underwriter (Decision Maker)
The Atlas employee who evaluates risk and makes the accept/decline/price decision.
Atlas has several underwriters with different specialties:
- **Sarah Mitchell** — handles preferred/complex accounts
- **James Rodriguez** — handles long-haul and borderline risks
- **David Chen** — handles intermodal and new submissions

### The Approving Authority (The Boss)
For risky decisions, the underwriter needs approval from a higher authority:
- **VP UW (Karen Wallace)** — approves moderately risky deals
- **CCO (Chief Claims Officer)** — approves high-risk categories (HAZMAT)
- **Reserve Committee** — handles catastrophic situations (fatalities, $650K+ claims)

### The Claims Adjuster (After the Accident)
When an accident happens, the adjuster investigates and determines how much to pay.
Examples: Mike Patterson, Lisa Chang, Tom Bradley.

---

## 4. The UW Lifecycle — End to End

```
┌─────────────────────────────────────────────────────────────────────┐
│                    THE UNDERWRITING LIFECYCLE                       │
│                                                                     │
│  SUBMISSION → GATHER INFO → ASSESS RISK → PRICE → DECIDE            │
│       │                                              │              │
│       │            (referral if needed)              │              │
│       │                   ↓                          ↓              │
│       │            BOSS APPROVAL              BIND POLICY           │
│       │                                              │              │
│       │                                              ↓              │
│       │                                      ACTIVE POLICY          │
│       │                                        │         │          │
│       │                                   CLAIMS    RENEWAL         │
│       │                                        │         │          │
│       │                                        ↓         ↓          │
│       └──────────── (new submission at renewal) ←────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

The cycle repeats annually. Every year at renewal time, the underwriter asks:
"Given what happened this year, do we want them back?"

---

## Step 1: Submission

**What happens:** A broker emails or uploads a package of documents asking Atlas to
quote insurance for a trucking company.

**Daily life analogy:** Applying for college. You submit your transcript, essays, test
scores, and recommendations. Then you wait for an admissions decision.

**What's in a submission:**
- Company name, address, years in business
- Fleet size (number of trucks) and driver count
- What they haul (general freight, refrigerated, chemicals, etc.)
- Where they operate (local, regional, long-haul)
- Current insurance details and what they're paying now (expiring premium)
- Requested coverage limits (e.g., $1,000,000 per accident)

**Real example from Atlas data:**

> **Rockford Grain Transport LLC** submitted on June 15, 2026 through broker
> "Heartland Specialty Insurance" (contact: Tom Berkowitz). They have 28 trucks,
> 32 drivers, haul dry bulk grain regionally. Their current premium is $145,000.
> Target effective date: August 1, 2026. Status: In Review. Assigned to David Chen.

**Submission statuses (the journey):**
- **Received** — just arrived, no one has looked yet
- **In Review** — an underwriter is actively evaluating
- **Quoted** — Atlas made an offer (price)
- **Bound** — the customer accepted, deal done
- **Declined** — Atlas said no
- **Lost** — Atlas quoted but the customer chose a competitor

---

## Step 2: Information Gathering

**What happens:** The underwriter collects and reads documents to understand the risk.
This is the most time-consuming step — it's why the CoPilot exists.

**Daily life analogy:** A detective gathering evidence before making an arrest. They pull
records, interview witnesses, check databases, and build a case file.

### Documents the Underwriter Reviews

(These are the 16 document categories in the Atlas system, totaling 1,500+ PDFs)

| # | Document Type | What It Contains | Analogy |
| --- | --- | --- | --- |
| 1 | **Submissions** | The application package (ACORD forms, supplementals) | College application |
| 2 | **Loss Runs** | 3-5 year accident history with costs | Your driving record at the DMV |
| 3 | **Fleet Inspections** | Physical condition reports on trucks/trailers | Home inspection before buying |
| 4 | **Email Correspondence** | Broker-underwriter communications | Text messages between realtor and buyer |
| 5 | **Meeting Minutes** | Notes from underwriting review meetings | Meeting notes from a job interview panel |
| 6 | **Policy Documents** | The actual contract terms | The lease agreement |
| 7 | **Claim Files** | Detailed records of past accidents | Police accident reports |
| 8 | **Loss Control Reports** | Safety program evaluations (on-site visits) | A health checkup report |
| 9 | **Underwriter Notes** | Internal analysis and decision rationale | Teacher's comments on a report card |
| 10 | **Underwriting Guidelines** | Atlas's internal rulebook for decisions | The grading rubric |
| 11 | **Claims Procedures** | How to handle different claim scenarios | Employee handbook |
| 12 | **Loss Control** | Safety improvement recommendations | Doctor's prescription |
| 13 | **Product Guides** | What coverages Atlas offers and how they work | Product catalog |
| 14 | **Regulatory & Compliance** | Government rules (DOT, FMCSA, state laws) | Traffic laws |
| 15 | **Authority & Limits** | Who can approve what dollar amount | Spending authority chart |
| 16 | **Reference Materials** | Industry benchmarks, rate tables | Textbook |

---

## Step 3: Risk Assessment

**What happens:** The underwriter evaluates how likely it is that this company will have
accidents that cost Atlas money. This is the HEART of underwriting.

**Daily life analogy:** A teacher predicting which students will pass the final exam
based on homework grades, attendance, and class participation.

### The Five Pillars of Risk Assessment

### A. CSA Scores — The Government Report Card

The FMCSA (Federal Motor Carrier Safety Administration) gives every trucking company
scores in several categories. These are **percentiles** — higher = worse (opposite of
school!). Think of it as: "What percentage of trucking companies are SAFER than you?"

| CSA Category | What It Measures | Analogy |
| --- | --- | --- |
| Unsafe Driving | Speeding, reckless driving, texting | Traffic ticket history |
| HOS (Hours of Service) | Driving too many hours without rest | Working overtime violations |
| Vehicle Maintenance | Broken brakes, bad tires, light failures | Car failing inspection |
| Driver Fitness | Expired licenses, medical certificates | Expired gym membership ID |

**Real examples from Atlas:**

| Company | Unsafe Driving | HOS | Vehicle Maint | Verdict |
| --- | --- | --- | --- | --- |
| Summit Petroleum | 15.8 | 22.4 | 20.1 | Excellent (all low) |
| Heartland Express | 22.4 | 31.1 | 18.7 | Good |
| Pacific Coast | 38.2 | 45.6 | 28.3 | Concerning |
| Lone Star Hauling | 42.7 | 55.3 | 38.9 | Borderline |

**The rule of thumb:**
- Below 30 = "A student" (Preferred)
- 30-50 = "B/C student" (Acceptable)
- 50-65 = "D student" (Borderline)
- Above 65 = "Failing" (Decline)

### B. Loss History — What Happened in the Past

The underwriter looks at 3-5 years of past claims. From Atlas's `loss_runs` table:

**Heartland Express (the good student):**
- 2023-2024: 4 claims, $108K incurred, loss ratio 29%
- 2024-2025: 3 claims, $143K incurred, loss ratio 36%
- 2025-2026: 2 claims, $74K incurred, loss ratio 23%

→ Trend: Improving. Few claims, low severity. Atlas makes money.

**Metro Moving (the one who got declined):**
- 3-year loss ratio: 95.3%
- Had 2 excluded drivers out of 10 total

→ Atlas would lose money. Declined.

### C. Driver Quality — Who's Behind the Wheel

A fleet is only as safe as its worst driver. The underwriter reviews every driver:

| Factor | Good (Heartland DRV-2001) | Bad (reason to worry) |
| --- | --- | --- |
| CDL Experience | 18 years | Under 2 years |
| MVR Points | 0 | 4+ |
| Accidents (3yr) | 0 | 2+ |
| Violations (3yr) | 0 | 3+ |
| Telematics Score | 92.4 | Below 70 |
| Disqualifying Offense | No | Yes (DUI, felony) |

**Analogy:** If you owned a pizza delivery company, would you hire a driver with 5
speeding tickets and a suspended license? Neither would an underwriter insure a fleet
that employs them.

### D. Operations — What and Where They Haul

Risk varies dramatically by cargo and route:

| Operation Type | Risk Level | Why |
| --- | --- | --- |
| Local delivery | Lower | Short distances, slower speeds |
| Regional | Medium | Known routes, moderate distances |
| Long Haul | Higher | Fatigue, unfamiliar roads, higher speeds |
| Intermodal (containers) | Medium-High | Port congestion, chassis issues |
| Dedicated | Lower | Same route daily, predictable |

| Commodity | Risk Level | Why |
| --- | --- | --- |
| General Freight | Medium | Standard boxes, low hazard |
| Refrigerated | Medium-High | Time pressure → speeding, jackknife risk |
| Petroleum/Chemicals | Highest | Spills = environmental disaster, explosions |
| Construction Materials | High | Heavy loads, congested work zones |
| Household Goods | Medium | Low value but access to homes |
| Dry Bulk/Grain | Medium | Rollover risk with high center of gravity |

### E. Telematics & Safety Technology

Modern trucks have cameras and sensors that track driver behavior in real-time:

| Technology | What It Does | Impact on Risk |
| --- | --- | --- |
| Telematics (Samsara, KeepTruckin) | Tracks speed, hard braking, location | Lower risk (accountability) |
| Dashcams (front + cab-facing) | Video evidence of accidents | Lower risk (exonerates drivers) |
| ELD (Electronic Logging Device) | Tracks driving hours legally | Compliance with HOS rules |

**Atlas checks dashcam coverage percentage:**
- Heartland: 92% coverage → Good
- Lone Star: 45% coverage → Concerning (what are they hiding?)

---

## Step 4: Pricing

**What happens:** The underwriter calculates how much to charge based on the risk
assessment.

**Daily life analogy:** Setting the price for Uber rides. A ride during rush hour in the
rain costs more because the risk of delay/accident is higher. Same concept.

### What Drives the Premium

| Factor | Effect on Price | Example |
| --- | --- | --- |
| Fleet size | More trucks = more premium | 85 trucks costs more than 18 |
| Loss history | Bad history = higher rate per truck | 95% loss ratio → huge surcharge |
| Commodity | HAZMAT → much higher rate | Petroleum at 3x general freight |
| Territory | NYC traffic vs. rural Nebraska | Urban = more expensive |
| CSA scores | High scores = surcharge | Above 50th = 15-25% surcharge |
| Deductible chosen | Higher deductible = lower premium | $5K deductible saves 10% vs $1K |
| Safety tech | Dashcams/telematics = discount | Full coverage = 5-10% credit |
| Experience | More years in business = discount | 20+ years = stability credit |

### Real Pricing from Atlas

**Heartland Express (85 trucks, preferred risk):**
- Auto Liability: $425,000/year
- Physical Damage: $185,000/year
- Motor Truck Cargo: $42,000/year
- **Total: ~$652,000/year** (~$7,670 per truck)

**Pacific Coast Carriers (42 trucks, acceptable risk):**
- Would be proportionally higher rate per truck due to worse loss history
- Quoted $325,000 (up from $298,000 expiring — a 9% increase)

**The Golden Formula:**
```
Premium = (Base Rate × Fleet Size × Territory Factor × Commodity Factor)
          + Loss History Surcharge
          - Safety Credits
          + Expense Loading
```

---

## Step 5: The Decision

**What happens:** After all the analysis, the underwriter makes the call.

**Possible outcomes:**

### Quoted (Yes, here's our price)
> Dixie Express Lines: 52 trucks, long haul, general freight. 3-year loss ratio 52%.
> Quoted $345,000 (up from $310,000 expiring). Days to quote: 8.

### Declined (No, too risky)
> Metro Moving and Storage: 8 trucks, local, household goods. DECLINED because:
> "Loss ratio exceeds 90% for 3 consecutive years. Fleet has 2 excluded drivers
> out of 10 total."

**Analogy:** A restaurant refusing to seat a customer who walked out on the bill three
times in a row. The risk outweighs the reward.

### Approved with Conditions (Yes, but...)
> Pacific Coast Carriers: Approved BUT must accept 15% rate increase, add $15K
> deductible, and fix the problem with driver DRV-2013 within 60 days.

**Analogy:** Getting accepted to college on probation — you can come, but your GPA
must stay above 3.0 or you're out.

---

## Step 6: Referrals

**What happens:** When the risk is too large or unusual for the underwriter's authority
level, they "refer up" to get a boss's approval.

**Daily life analogy:** A store cashier can approve a $50 return, the floor manager can
do $500, but anything over $5,000 needs the district manager.

### Referral Tiers at Atlas

| Tier | Authority | When Triggered |
| --- | --- | --- |
| Claims Director | First escalation | Unusual claim patterns |
| VP UW (Karen Wallace) | Moderate risk | Bad loss history, high CSA scores |
| CCO (Chief Claims Officer) | High risk | HAZMAT fleets, appetite exceptions |
| Reserve Committee | Catastrophic | Fatalities, $650K+ claims, non-renewals |

### Real Referral Examples from Atlas

**Example 1 — Approved with Conditions (REF-26-001):**
> Pacific Coast Carriers referred to VP UW for "Loss History."
> Three-year trend deteriorating. Large open BI claim at $385K.
> Decision: Approved with conditions (rate increase, higher deductible, driver fix).

**Example 2 — Pending CCO Review (REF-26-002):**
> Coastal Petroleum Haulers referred to CCO for "Risk Appetite."
> HAZMAT fleet, 15 units. Clean history but requires elevated authority per
> commodity class. Still awaiting decision.

**Example 3 — Declined (REF-26-003):**
> INS-1007 referred to VP UW for "CSA Scores."
> Unsafe Driving 52.1, Vehicle Maintenance 55.3. Conditional DOT rating.
> 85% loss ratio with two large losses. SIU referral. Non-renewal recommended.

**Example 4 — Catastrophic (REF-26-004):**
> Lone Star Hauling referred to Reserve Committee.
> Catastrophic claim: $650K incurred, fatality involved.
> Current-term loss ratio exceeds 1100%. Potential non-renewal.

### Common Referral Triggers
- Loss ratio above 60% (3-year)
- CSA scores above 50th percentile in any BASIC
- HAZMAT or high-value cargo
- Fleet with excluded drivers exceeding 10% of total
- Any claim involving a fatality
- New venture (less than 2 years in business)
- Any single claim above $250K

---

## Step 7: Binding

**What happens:** The customer accepts the quote, signs the agreement, and the policy
becomes active. Money changes hands.

**Daily life analogy:** Signing the lease on an apartment. You've toured it, negotiated
the rent, and now you sign + pay the first month.

**What triggers binding:**
- Customer (via broker) confirms acceptance of terms and price
- Premium payment received (or agreed payment plan)
- All required documents submitted (driver lists, vehicle schedules, loss runs)
- Policy issued with effective date

**From Atlas `policies` table:**
```
Policy ID:       ACI-AL-25-732053
Insured:         Heartland Express (INS-1001)
Line:            Auto Liability
Effective:       2025-03-15
Expiration:      2026-03-15
Premium:         $425,000
Limit:           $1,000,000 CSL
Aggregate:       $2,000,000
Deductible:      $5,000
Vehicles:        85
Status:          Active
Renewal:         Auto-Renew
```

---

## Step 8: Claims

**What happens:** A truck gets in an accident. Someone is hurt or property is damaged.
The injured party (or the trucking company for their own truck damage) files a claim
asking Atlas to pay.

**Daily life analogy:** You get in a car accident. You call your insurance company,
file a claim, and they send a check to fix your car or pay the other person's medical
bills.

### Claim Lifecycle

```
Accident Occurs → Reported → Adjuster Assigned → Investigated →
Reserves Set → Payments Made → (Litigation?) → Closed
```

### Real Claims from Atlas

**Simple claim (CLM-25-2614890):**
> Heartland Express truck had a tire blowout on I-55, hit a guardrail.
> Vehicle damage only, no one hurt. 100% our driver's fault.
> Total cost: $28,500. Closed in 2.5 months.

**Complex claim (CLM-25-3891045):**
> Pacific Coast Carriers truck in a multi-vehicle highway accident on I-10.
> Two people hurt (moderate injuries). Attorney involved, lawsuit filed.
> Total incurred: $385,000 ($125K paid so far, $260K in reserves).
> This is a "Large Loss" (>$250K) and is STILL OPEN.

**Catastrophic claim:**
> Lone Star Hauling: $650K incurred, involves a fatality.
> Referred to Reserve Committee. Loss ratio for that policy year: 1100%.

### Key Claim Concepts

| Term | What It Means | Analogy |
| --- | --- | --- |
| **Total Incurred** | Total expected cost (paid + what we think we'll owe) | Your total credit card balance |
| **Total Paid** | Cash actually sent out so far | What you've already paid |
| **Reserves** | Money set aside for future payments | Savings earmarked for a future bill |
| **Fault %** | How much our driver was to blame | 80% your fault, 20% theirs |
| **Subrogation** | Money recovered from the OTHER party | Getting your deposit back |
| **Large Loss** | Any claim ≥ $250K incurred | A VIP alert |
| **Catastrophic** | Fatality or permanent injury | Worst-case scenario |
| **Litigation** | A lawsuit has been filed | Going to court |
| **SIU Referral** | Special Investigation Unit (suspected fraud) | Calling the detective |

### Litigation Stages
1. **None** — no legal action
2. **Pre-Suit** — attorneys involved but no lawsuit yet (demand letters)
3. **Suit Filed** — formal lawsuit filed in court
4. **Trial Set** — court date scheduled
5. **Settled** — resolved without going to trial (most common)

---

## Step 9: Renewal

**What happens:** Every policy lasts one year. Before it expires, the underwriter
decides whether to keep the customer and at what price.

**Daily life analogy:** Your gym membership is up for renewal. The gym looks at:
Did you damage equipment? Cause problems? Were you a good member? Then they decide
whether to renew you and if the price changes.

### Renewal Outcomes (from Atlas `policies` table)

| Status | Meaning | When It Happens |
| --- | --- | --- |
| **Auto-Renew** | Good customer, renew automatically | Loss ratio under 50%, no referrals |
| **Review Required** | Need to re-evaluate before renewing | Claims this year, CSA score changes |
| **Non-Renew** | We're dropping them | Catastrophic losses, fraud, unacceptable risk |

**Auto-Renew example:** Heartland Express — 32% loss ratio, clean history. No reason
not to keep them.

**Non-Renew example:** INS-1007 — CSA scores above 50th percentile, conditional DOT
rating, 85% loss ratio, SIU referral. Too risky to continue.

---

## Key Metrics Every UW Watches

### Loss Ratio (THE most important number)

```
Loss Ratio = Total Claims Incurred / Earned Premium × 100
```

| Loss Ratio | Interpretation | Action |
| --- | --- | --- |
| Under 40% | Excellent — very profitable | Auto-renew, maybe reduce rate |
| 40-55% | Good — profitable | Renew as-is |
| 55-70% | Marginal — breakeven zone | Review, possible rate increase |
| 70-90% | Bad — losing money | Rate increase or non-renew |
| Over 90% | Terrible — bleeding money | Decline or non-renew immediately |

**Analogy:** If you run a lemonade stand and charge $10 per cup:
- Loss ratio 30% = lemons cost you $3, you keep $7. Great business.
- Loss ratio 95% = lemons cost you $9.50, you keep $0.50. Terrible business.
- Loss ratio 150% = lemons cost you $15, you LOSE $5 per cup. Close the stand.

### Frequency (How often do they crash?)

```
Frequency = Number of Claims / Number of Power Units
```

From Atlas: Heartland has a frequency of 0.02-0.05 (2-5 claims per 100 trucks per year).
That's good. Industry average for trucking is about 0.15-0.25.

### Severity (How expensive is each crash?)

```
Severity = Total Incurred / Number of Claims
```

Heartland's average severity: $27,000-$47,500 per claim. Reasonable.
Pacific Coast's severity: $175,000+ per claim. Alarming.

### Combined Ratio (Company-wide profitability)

```
Combined Ratio = Loss Ratio + Expense Ratio
```

- Under 100% = profitable
- Over 100% = losing money on underwriting

---

## Document Types and What They Contain

### Underwriting Guidelines (the rulebook)
These are Atlas's internal rules that tell underwriters what to accept, decline, and
how to price. Think of it as the "instruction manual" for the job.

Key sections include:
- Acceptable risk appetite (what types of operations Atlas will write)
- Prohibited commodities (e.g., oversize/overweight, livestock)
- Minimum requirements (years in business, fleet size)
- Rate tables and modification factors
- Referral triggers (when to escalate)

### Loss Control Reports (safety checkups)
Atlas sends a "loss control specialist" to physically visit the trucking company.
They inspect:
- Truck maintenance practices
- Driver hiring and training programs
- Safety meeting frequency
- Drug testing protocols
- Dashcam and telematics usage
- Terminal security

### ACORD Forms (industry-standard application)
ACORD is the insurance industry's version of a standardized form. Think SAT vs ACT —
everyone uses the same form so it's easy to compare.

Common forms:
- ACORD 125 — commercial insurance application
- ACORD 127 — business auto supplement
- ACORD 137 — trucking supplement

### Loss Runs (accident history transcripts)
A year-by-year breakdown showing every claim:
- Date of loss
- Type of loss (bodily injury, property damage, cargo)
- Amount paid and reserved
- Whether the claim is open or closed

---

## Lines of Business (Coverage Types)

A trucking company typically buys multiple policies ("lines") as a package:

| Line of Business | What It Covers | Daily Life Analogy |
| --- | --- | --- |
| **Auto Liability (AL)** | Injuries/damage Atlas's insured causes to OTHERS | Your car insurance liability coverage |
| **Physical Damage (PD)** | Damage to the insured's OWN trucks | Collision/comprehensive on your car |
| **Motor Truck Cargo (MTC)** | Damage/loss/theft of the freight being hauled | Shipping insurance on a FedEx package |
| **General Liability (GL)** | Slip-and-fall at the trucking company's office | Homeowner's insurance liability |
| **Umbrella/Excess** | Extra coverage above primary limits | An extra safety net |
| **Workers' Compensation** | Injuries to the trucking company's own employees | Your employer's work injury coverage |

**Real example from Atlas policies table:**
Heartland Express carries:
- `ACI-AL-25-732053` — Auto Liability ($1M limit, $425K premium)
- `ACI-PD-25-732054` — Physical Damage (ACV limit, $185K premium)
- `ACI-MC-25-732055` — Motor Truck Cargo ($250K limit, $42K premium)

---

## Risk Tiers — The Report Card

Atlas assigns every insured a risk tier (from `insureds.risk_tier`):

| Tier | Meaning | Characteristics | Premium Impact |
| --- | --- | --- | --- |
| **Preferred** | Honor roll student | Low CSA, low loss ratio, experienced, good tech | Best rates |
| **Acceptable** | Average student | Moderate risk, some concerns but manageable | Standard rates |
| **Borderline** | On academic probation | High CSA scores, bad loss history, but fixable | High rates + conditions |
| **Decline** | Expelled | Unacceptable risk | No coverage offered |

---

## Regulatory Bodies — The Government Referees

### FMCSA (Federal Motor Carrier Safety Administration)
- Issues DOT numbers (like a business license for trucking)
- Conducts roadside inspections
- Issues safety ratings: Satisfactory, Conditional, Unsatisfactory
- Maintains CSA (Compliance, Safety, Accountability) scores
- Can shut down a carrier for safety violations

### USDOT (Department of Transportation)
- Every commercial truck must have a DOT number (visible on the truck door)
- Atlas stores these: e.g., Heartland = DOT 1234567

### State DOIs (Departments of Insurance)
- Each state regulates insurance rates and forms
- Atlas must file rates and get approval in each state they write business
- Consumer complaints go here

### NAIC (National Association of Insurance Commissioners)
- Industry standards body
- Coordinates regulations across states

---

## Glossary of Key Terms

| Term | Plain English Definition |
| --- | --- |
| **Premium** | The annual fee the customer pays for insurance |
| **Claim** | A request for Atlas to pay for an accident |
| **Policy** | The contract between Atlas and the customer |
| **Limit** | Maximum amount Atlas will pay per accident |
| **Deductible** | Amount the customer pays first before Atlas pays |
| **CSL** | Combined Single Limit — one limit for all damages per accident |
| **ACV** | Actual Cash Value — what the truck is worth today (depreciated) |
| **Earned Premium** | Premium that has been "used up" based on time elapsed |
| **Written Premium** | Total premium on the policy |
| **Incurred** | Total expected cost of a claim (paid + reserves) |
| **Reserves** | Money set aside for future claim payments |
| **Subrogation** | Recovering money from the at-fault party |
| **Broker** | Agent who represents the customer (not Atlas) |
| **Bind** | Activate the policy — coverage begins |
| **Endorsement** | A change to an active policy mid-term |
| **Exclusion** | Something specifically NOT covered |
| **Underwriting Authority** | Dollar limit an underwriter can approve alone |
| **SIU** | Special Investigation Unit — fraud detection |
| **MVR** | Motor Vehicle Report — a driver's official driving record |
| **CDL** | Commercial Driver's License — required to drive big trucks |
| **ELD** | Electronic Logging Device — tracks driving hours |
| **HOS** | Hours of Service — federal rules on how long drivers can work |
| **Power Unit** | A truck that can move under its own power (vs. a trailer) |
| **DOT Number** | Federal registration number for commercial carriers |
| **MC Number** | Motor Carrier number — operating authority permit |
| **Loss Ratio** | Claims / Premium — the profitability indicator |
| **Frequency** | How often claims happen (claims per unit) |
| **Severity** | How expensive each claim is (average cost per claim) |
| **Non-Renewal** | Atlas choosing not to continue a policy at expiration |
| **Declination** | Atlas refusing to offer coverage on a new submission |

---

## How the CoPilot Fits In

The UW CoPilot is an AI assistant that helps underwriters work faster and more
consistently. Here's what it does at each stage:

### During Submission Review
- **Instant document search:** "What are the referral triggers for HAZMAT fleets?"
  → Searches 1,500+ PDFs and returns the exact guideline section
- **Structured data queries:** "What's the 3-year loss ratio for Pacific Coast?"
  → Queries the SQL tables and returns: 48.9%

### During Risk Assessment
- **Cross-referencing:** Links a claim (CLM-25-3891045) to the submission it affects
  (SUB-26-11065) to the referral it triggered (REF-26-001)
- **Pattern detection:** "Show me all insureds with CSA Unsafe Driving above 40"
  → Returns a filtered list from the database

### During Pricing
- **Benchmarking:** "What premium did we quote for similar-size refrigerated fleets?"
  → Searches historical submissions
- **Guideline lookup:** "What's the minimum rate for petroleum haulers in Texas?"
  → Returns the rate table from the guidelines PDF

### During Renewal
- **Trend analysis:** "How has Heartland's loss ratio trended over 3 years?"
  → Returns year-over-year comparison
- **Claims summary:** "Summarize all open claims for INS-1002"
  → Returns claim details with reserves and litigation status

### For Training & Compliance
- **Guideline interpretation:** "Can we write a fleet with a Conditional DOT rating?"
  → Finds the relevant section and explains the exceptions
- **Audit trail:** Every question and answer is logged for compliance

---

## Summary — The One-Sentence Version

> **Underwriting is the process of deciding which trucking companies to insure, how
> much to charge them, and under what conditions — based on their safety record,
> driver quality, what they haul, and how likely they are to have expensive accidents.**

The CoPilot makes this process faster (minutes instead of hours), more consistent
(same rules applied every time), and more thorough (no document goes unread).

---

*Document generated from Atlas Commercial Insurance reference implementation data.*
*Last updated: July 2026*
