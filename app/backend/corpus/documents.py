"""Original educational financial document corpus for VeriCoach."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FinancialDocument:
    doc_id: str
    title: str
    category: str
    content: str
    keywords: list[str]


DOCUMENTS_CORPUS: list[FinancialDocument] = [
    # ── Category 1: UPI Safety (4 documents) ──────────────────────────────
    FinancialDocument(
        doc_id="upi_pin_rules",
        title="UPI PIN Usage Rules and Receiving Money",
        category="UPI Safety",
        content=(
            "A UPI PIN (Unified Payments Interface Personal Identification Number) is required ONLY when sending money "
            "or checking your account balance. You NEVER need to enter your UPI PIN to receive money or accept a refund. "
            "If any sender or merchant sends a QR code or payment link asking you to enter your PIN to claim a lottery, "
            "prize, cashback, or incoming funds, it is a fraud attempt. Entering your UPI PIN authorizes a debit from your bank account."
        ),
        keywords=[
            "upi",
            "pin",
            "receive money",
            "qr code",
            "cashback",
            "यूपीआई",
            "पिन",
            "ఖాతా",
            "డబ్బులు",
        ],
    ),
    FinancialDocument(
        doc_id="upi_collect_requests",
        title="Handling UPI Collect Requests Safely",
        category="UPI Safety",
        content=(
            "UPI collect requests allow a payee to request a transfer from your bank account. Always verify the requester's "
            "verified name, VPA (Virtual Payment Address), and the requested amount before approving. Never approve collect requests "
            "from unknown contacts or classifieds buyers (e.g., OLX, Quikr). Declining an unauthorized collect request is safe "
            "and does not penalize your account or credit score."
        ),
        keywords=[
            "collect request",
            "vpa",
            "virtual payment address",
            "approve",
            "decline",
            "రసీదు",
            "అభ్యర్థన",
        ],
    ),
    FinancialDocument(
        doc_id="upi_qr_code_scams",
        title="QR Code Scams in Peer-to-Peer Payments",
        category="UPI Safety",
        content=(
            "Scanning a QR code on phone payment apps like BHIM, Google Pay, PhonePe, or Paytm initiates a debit (outflow) "
            "from your bank account. Scammers frequently send fake QR codes claiming 'Scan here to receive payment'. Scanning "
            "such codes and entering your secret UPI PIN transfers funds immediately to the fraudster. Never scan unknown QR codes "
            "sent via WhatsApp, Telegram, or email."
        ),
        keywords=[
            "qr code",
            "bhim",
            "gpay",
            "phonepe",
            "paytm",
            "scan",
            "कस्टमर",
            "క్యూఆర్ కోడ్",
        ],
    ),
    FinancialDocument(
        doc_id="upi_transaction_limits",
        title="Daily UPI Transaction Limits and Security Controls",
        category="UPI Safety",
        content=(
            "NPCI (National Payments Corporation of India) sets a standard daily limit of INR 100,000 for standard peer-to-peer UPI transfers, "
            "though specific categories like education and healthcare allow up to INR 500,000. Many banks also limit individual users to 10 or 20 "
            "transactions per day. Users can proactively set lower daily limits in their mobile banking app to minimize financial loss if their "
            "phone is stolen or compromised."
        ),
        keywords=[
            "npci",
            "transaction limit",
            "daily limit",
            "security",
            "100000",
            "పరిమితి",
            "నియంత్రణ",
        ],
    ),
    # ── Category 2: KYC Basics (4 documents) ──────────────────────────────
    FinancialDocument(
        doc_id="kyc_definition_purpose",
        title="What is KYC and Why Financial Institutions Require It",
        category="KYC Basics",
        content=(
            "KYC stands for 'Know Your Customer'. It is a mandatory regulatory customer-identification process mandated by the "
            "Reserve Bank of India (RBI) and SEBI under the Prevention of Money Laundering Act (PMLA). KYC verifies the legal identity, "
            "physical address, and tax identification of an individual to prevent financial crime, money laundering, identity theft, "
            "and illicit funding."
        ),
        keywords=[
            "kyc",
            "know your customer",
            "rbi",
            "sebi",
            "pmla",
            "identity",
            "केवाईसी",
            "గుర్తింపు",
            "కేవైసీ",
        ],
    ),
    FinancialDocument(
        doc_id="kyc_officially_valid_docs",
        title="Officially Valid Documents (OVD) for KYC in India",
        category="KYC Basics",
        content=(
            "As per RBI regulations, six documents qualify as Officially Valid Documents (OVDs) for proof of identity and address: "
            "Passport, Driving Licence, Proof of possession of Aadhaar number, Voter's Identity Card, NREGA Job Card, and Letter issued "
            "by National Population Register. For financial accounts and investments above prescribed thresholds, providing a valid PAN card "
            "(or Form 60) is mandatory."
        ),
        keywords=[
            "ovd",
            "aadhaar",
            "pan",
            "passport",
            "voter id",
            "driving licence",
            "దస్తావేజులు",
            "పత్రాలు",
        ],
    ),
    FinancialDocument(
        doc_id="video_kyc_procedure",
        title="Video-based Customer Identification Process (V-CIP / Video KYC)",
        category="KYC Basics",
        content=(
            "Video KYC (V-CIP) enables fully digital, paperless account opening without visiting a bank branch. During an encrypted video session, "
            "a bank official captures live geo-tagged photographs, inspects the physical PAN card, verifies audio-visual liveliness, and compares "
            "facial biometrics. Customers should ensure they are within Indian territory and have their original physical PAN card handy during the call."
        ),
        keywords=[
            "video kyc",
            "v-cip",
            "paperless",
            "geo-tagged",
            "facial verification",
            "లైవ్",
            "వీడియో",
        ],
    ),
    FinancialDocument(
        doc_id="ckyc_central_registry",
        title="Central KYC (CKYC) and 14-Digit KIN Registry",
        category="KYC Basics",
        content=(
            "Central KYC Registry (CKYCR) is managed by CERSAI to eliminate repetitive KYC submissions across different financial institutions. "
            "Once you complete KYC with a bank, mutual fund, or insurer, you receive a unique 14-digit KYC Identification Number (KIN). You can "
            "quote this KIN at other SEBI/RBI regulated entities to open accounts or invest without resubmitting physical paperwork."
        ),
        keywords=[
            "ckyc",
            "kin",
            "cersai",
            "central kyc",
            "registry",
            "కేంద్రీయ",
            "నంబర్",
        ],
    ),
    # ── Category 3: Credit Score Basics (4 documents) ─────────────────────
    FinancialDocument(
        doc_id="credit_score_ranges",
        title="Credit Score Ranges and Loan Eligibility",
        category="Credit Score Basics",
        content=(
            "In India, credit bureaus like CIBIL, Experian, CRIF High Mark, and Equifax score creditworthiness between 300 and 900. "
            "A score above 750 is considered excellent and commands the lowest interest rates on home and personal loans. Scores between 700 "
            "and 749 are good. A score below 650 indicates high credit risk, resulting in loan rejections, high interest rates, or demands for collateral."
        ),
        keywords=[
            "credit score",
            "cibil",
            "experian",
            "750",
            "loan approval",
            "क्रेडिट स्कोर",
            "క్రెడిట్ స్కోర్",
            "సిబిల్",
        ],
    ),
    FinancialDocument(
        doc_id="credit_utilization_ratio",
        title="Credit Utilization Ratio (CUR) and Its Impact",
        category="Credit Score Basics",
        content=(
            "Credit Utilization Ratio (CUR) is the percentage of your total revolving credit card limit that you spend. Financial planners "
            "and credit rating models recommend keeping your aggregate CUR below 30%. Consistently maxing out credit cards signals financial "
            "distress and directly reduces your credit score, even if you make minimum payments on time."
        ),
        keywords=[
            "cur",
            "credit utilization",
            "credit limit",
            "revolving debt",
            "30 percent",
            "వినియోగం",
            "కార్డు",
        ],
    ),
    FinancialDocument(
        doc_id="credit_hard_vs_soft_inquiries",
        title="Hard Inquiries vs Soft Inquiries on Credit Reports",
        category="Credit Score Basics",
        content=(
            "A soft inquiry occurs when you check your own credit score or when an employer does background verification; soft inquiries do not "
            "affect your credit score. A hard inquiry occurs when a lender checks your bureau report following a loan or credit card application. "
            "Submitting multiple loan applications to multiple banks in a short timeframe creates multiple hard inquiries and lowers your credit score."
        ),
        keywords=[
            "hard inquiry",
            "soft inquiry",
            "bureau report",
            "credit check",
            "loan application",
            "విచారణ",
        ],
    ),
    FinancialDocument(
        doc_id="rebuilding_damaged_credit_score",
        title="Strategies for Rebuilding a Damaged Credit Score",
        category="Credit Score Basics",
        content=(
            "To repair a damaged credit score: (1) Pay all EMIs and credit card dues in full before the due date, (2) Clear overdue or written-off "
            "accounts and obtain a No Objection Certificate (NOC), (3) Maintain older credit card accounts to preserve credit history length, and "
            "(4) Consider an FD-backed secured credit card to re-establish a positive repayment pattern over 6 to 12 months."
        ),
        keywords=[
            "repair credit",
            "rebuild score",
            "secured credit card",
            "noc",
            "overdue",
            "మరమ్మతు",
            "పునరుద్ధరణ",
        ],
    ),
    # ── Category 4: SIP and Mutual Fund Basics (4 documents) ──────────────
    FinancialDocument(
        doc_id="sip_rupee_cost_averaging",
        title="Systematic Investment Plan (SIP) and Rupee Cost Averaging",
        category="SIP & Mutual Funds",
        content=(
            "A Systematic Investment Plan (SIP) lets you invest a fixed sum into a mutual fund scheme at regular intervals (monthly or weekly). "
            "SIP utilizes Rupee Cost Averaging: when market prices are low, your fixed installment buys more mutual fund units; when markets rise, "
            "it buys fewer units. This eliminates the need to time the market and instills long-term financial discipline."
        ),
        keywords=[
            "sip",
            "mutual fund",
            "rupee cost averaging",
            "disciplined investing",
            "एसआईपी",
            "మ్యూచువల్ ఫండ్",
            "పెట్టుబడి",
        ],
    ),
    FinancialDocument(
        doc_id="nav_and_expense_ratio",
        title="Net Asset Value (NAV) and Mutual Fund Expense Ratio",
        category="SIP & Mutual Funds",
        content=(
            "Net Asset Value (NAV) represents the market value per unit of a mutual fund scheme, calculated daily after subtracting scheme liabilities. "
            "Total Expense Ratio (TER) is the annual percentage fee deducted by Asset Management Companies (AMCs) to cover fund management, "
            "administration, and marketing. Direct plans have lower expense ratios than regular plans because direct plans exclude distributor commissions."
        ),
        keywords=[
            "nav",
            "net asset value",
            "expense ratio",
            "ter",
            "direct plan",
            "ఎన్ఏవి",
            "ఖర్చు నిష్పత్తి",
        ],
    ),
    FinancialDocument(
        doc_id="equity_vs_debt_funds",
        title="Asset Classes: Equity vs Debt vs Hybrid Mutual Funds",
        category="SIP & Mutual Funds",
        content=(
            "Equity mutual funds invest predominantly in company stocks and offer high potential long-term capital growth suitable for horizons of "
            "5+ years, with accompanying market volatility. Debt funds invest in fixed-income securities like government bonds, corporate debentures, "
            "and treasury bills, providing relative stability and liquidity for short-to-medium horizons. Hybrid funds blend equity and debt."
        ),
        keywords=[
            "equity fund",
            "debt fund",
            "hybrid fund",
            "bonds",
            "volatility",
            "ఈక్విటీ",
            "రుణ నిధులు",
        ],
    ),
    FinancialDocument(
        doc_id="elss_tax_saving_mutual_funds",
        title="Equity Linked Savings Schemes (ELSS) Tax Deductions",
        category="SIP & Mutual Funds",
        content=(
            "ELSS (Equity Linked Savings Scheme) is an equity mutual fund eligible for tax deduction up to INR 150,000 under Section 80C of the "
            "Income Tax Act (in the old tax regime). ELSS features a mandatory lock-in period of 3 years, which is the shortest among all Section 80C "
            "tax-saving instruments like PPF (15 years) or Tax-saving FDs (5 years)."
        ),
        keywords=[
            "elss",
            "section 80c",
            "tax saving",
            "lock-in period",
            "3 years",
            "పన్ను ఆదా",
        ],
    ),
    # ── Category 5: Fraud Awareness (4 documents) ─────────────────────────
    FinancialDocument(
        doc_id="screen_sharing_app_scams",
        title="Remote Screen-Sharing App Fraud (AnyDesk, TeamViewer)",
        category="Fraud Awareness",
        content=(
            "Cyber fraudsters posing as bank executives or tech support trick victims into downloading remote access tools like AnyDesk, TeamViewer, "
            "or RustDesk. Once installed, the scammer views the victim's phone screen in real time, observes banking passwords, and intercepts OTPs. "
            "Legitimate bank or payment company employees will never ask you to install third-party screen-sharing applications."
        ),
        keywords=[
            "screen sharing",
            "anydesk",
            "teamviewer",
            "remote access",
            "otp interception",
            "రిమోట్ యాప్",
            "మోసం",
        ],
    ),
    FinancialDocument(
        doc_id="fake_customer_care_numbers",
        title="Fake Search Engine Customer Care Numbers",
        category="Fraud Awareness",
        content=(
            "Scammers post fake customer care phone numbers on search engines, Google Maps, and social media for courier services, banks, and e-wallets. "
            "When desperate callers reach out for refund issues, the imposter asks for banking card details or a token transfer of INR 10. Always look up "
            "official customer support contacts directly inside verified apps or on official HTTPS bank domain websites."
        ),
        keywords=[
            "customer care",
            "google search scam",
            "fake helpline",
            "impersonation",
            "సహాయవాణి",
        ],
    ),
    FinancialDocument(
        doc_id="lottery_job_task_scams",
        title="Telegram Task Scams and Part-time Job Frauds",
        category="Fraud Awareness",
        content=(
            "Task-based frauds involve messages on WhatsApp or Telegram offering daily payments of INR 2,000 to 5,000 for liking YouTube videos or "
            "rating hotels. After small initial payouts, victims are directed into crypto or prepaid 'investment tasks' where deposits are frozen. "
            "Genuine employers never ask candidates to pay advance registration fees or deposit funds into unverified bank accounts."
        ),
        keywords=[
            "job scam",
            "task scam",
            "telegram fraud",
            "prepaid task",
            "రహస్య మోసాలు",
        ],
    ),
    FinancialDocument(
        doc_id="reporting_cyber_crime_india",
        title="Reporting Financial Cyber Fraud (Helpline 1930)",
        category="Fraud Awareness",
        content=(
            "If you fall victim to financial online fraud, immediately call the National Cyber Crime Helpline number '1930' (formerly 155260) "
            "and file an official incident report on 'cybercrime.gov.in'. Reporting within the first two hours (the golden hour) allows banks "
            "to freeze transaction trails and prevent fraudsters from withdrawing or siphoning the stolen funds."
        ),
        keywords=[
            "1930",
            "cybercrime",
            "helpline",
            "golden hour",
            "reporting",
            "సైబర్ క్రైమ్",
        ],
    ),
    # ── Category 6: Budgeting and Emergency Funds (4 documents) ───────────
    FinancialDocument(
        doc_id="fifty_thirty_twenty_budget_rule",
        title="The 50/30/20 Budgeting Framework",
        category="Budgeting & Emergency Funds",
        content=(
            "The 50/30/20 rule is an intuitive personal budgeting framework: Allocate 50% of your net post-tax income to Needs (rent, groceries, "
            "utility bills, minimum loan payments), 30% to Wants (dining out, entertainment, shopping), and at least 20% to Savings, investments, "
            "and accelerated debt reduction. This prevents lifestyle inflation while securing future financial goals."
        ),
        keywords=[
            "50 30 20",
            "budgeting",
            "needs",
            "wants",
            "savings",
            "బడ్జెట్",
            "ఖర్చులు",
        ],
    ),
    FinancialDocument(
        doc_id="emergency_fund_sizing",
        title="Emergency Fund Sizing and Liquid Allocation",
        category="Budgeting & Emergency Funds",
        content=(
            "An emergency fund should cover 3 to 6 months of mandatory living expenses (rent, food, insurance premiums, EMIs). For individuals with "
            "variable income or single-earner households, maintaining 9 to 12 months is prudent. Emergency funds must be held in highly liquid, "
            "low-risk instruments like bank savings accounts, sweep-in fixed deposits, or liquid mutual funds, never in volatile equity stocks."
        ),
        keywords=[
            "emergency fund",
            "liquid fund",
            "6 months expenses",
            "savings buffer",
            "అత్యవసర నిధి",
        ],
    ),
    FinancialDocument(
        doc_id="zero_based_budgeting",
        title="Zero-Based Budgeting and Expense Auditing",
        category="Budgeting & Emergency Funds",
        content=(
            "Zero-based budgeting involves assigning every single rupee of monthly income to a specific category (living costs, retirement savings, "
            "debt repayment, discretionary spending) until income minus expenditures equals zero. Conducting periodic 90-day subscription and "
            "bank statement audits helps detect recurring leaks and fees."
        ),
        keywords=[
            "zero based budgeting",
            "expense tracking",
            "audit",
            "cashflow",
            "లెక్కలు",
        ],
    ),
    FinancialDocument(
        doc_id="sinking_funds_planned_expenses",
        title="Sinking Funds for Planned Lump-Sum Expenses",
        category="Budgeting & Emergency Funds",
        content=(
            "A sinking fund is money set aside incrementally each month for a predictable upcoming lump-sum expense, such as annual car insurance, "
            "festival gifts, home maintenance, or medical dental work. By planning ahead in recurring deposits or liquid pots, you avoid tapping "
            "into your core emergency fund or relying on high-interest personal credit cards."
        ),
        keywords=[
            "sinking fund",
            "recurring expenses",
            "planned purchases",
            "short term savings",
            "పొదుపు",
        ],
    ),
    # ── Category 7: Loan Terminology (3 documents) ────────────────────────
    FinancialDocument(
        doc_id="emi_and_amortization",
        title="Equated Monthly Installment (EMI) and Amortization Schedules",
        category="Loan Terminology",
        content=(
            "An EMI (Equated Monthly Installment) is the fixed payment amount made by a borrower to a lender at a specified date each month. "
            "Each EMI comprises both interest and principal repayment. In the early stages of a loan amortization schedule, the interest component "
            "makes up the largest share of the EMI; as the loan matures, the principal repayment portion progressively increases."
        ),
        keywords=[
            "emi",
            "amortization",
            "principal",
            "interest",
            "installment",
            "ఈఎంఐ",
            "కిస్తీ",
        ],
    ),
    FinancialDocument(
        doc_id="fixed_vs_floating_rates",
        title="Fixed vs Floating Interest Rates on Loans",
        category="Loan Terminology",
        content=(
            "A fixed interest rate remains unchanged throughout the loan tenure, providing certainty in monthly payments. A floating interest rate "
            "is linked to an external benchmark (such as the RBI Repo Rate via EBLR) and changes periodically when benchmark rates fluctuate. "
            "Floating rate home loans generally carry lower starting rates and, by RBI directive, cannot be charged prepayment penalties for retail borrowers."
        ),
        keywords=[
            "fixed rate",
            "floating rate",
            "eblr",
            "repo rate",
            "prepayment penalty",
            "వడ్డీ రేటు",
        ],
    ),
    FinancialDocument(
        doc_id="foreclosure_prepayment_charges",
        title="Loan Foreclosure and Part-Prepayment Guidelines",
        category="Loan Terminology",
        content=(
            "Prepayment refers to repaying a portion of the loan principal before the scheduled tenure, reducing either future EMI amounts or total loan duration. "
            "Foreclosure means settling the entire outstanding loan balance in a single payment. Under RBI regulations, banks and NBFCs cannot levy foreclosure "
            "charges or prepayment penalties on floating-rate individual term loans."
        ),
        keywords=[
            "foreclosure",
            "prepayment",
            "rbi rule",
            "early closure",
            "ముందస్తు చెల్లింపు",
        ],
    ),
    # ── Category 8: Insurance Basics (3 documents) ────────────────────────
    FinancialDocument(
        doc_id="term_insurance_vs_endowment",
        title="Pure Term Life Insurance vs Endowment/ULIP Plans",
        category="Insurance Basics",
        content=(
            "Term life insurance provides pure death-benefit financial protection for a specified period with no maturity payout if the policyholder survives. "
            "Because there is no investment component, term insurance offers large sum assured coverage (e.g., INR 1 crore) for affordable premiums. "
            "Endowment policies and ULIPs combine insurance with investments but typically offer lower cover and higher management fees."
        ),
        keywords=[
            "term insurance",
            "endowment",
            "ulip",
            "sum assured",
            "death benefit",
            "భీమా",
            "టర్మ్ ఇన్సూరెన్స్",
        ],
    ),
    FinancialDocument(
        doc_id="health_insurance_deductible_copay",
        title="Health Insurance: Deductible, Co-payment, and Waiting Periods",
        category="Insurance Basics",
        content=(
            "In health insurance, a Deductible is the amount the insured must pay out-of-pocket before the insurer begins covering medical claims. "
            "Co-payment is a fixed percentage of each medical claim that the policyholder agrees to pay. Waiting periods are predefined spans (typically "
            "1 to 3 years) before pre-existing health conditions or specific surgical procedures are covered under the policy."
        ),
        keywords=[
            "health insurance",
            "deductible",
            "co-payment",
            "waiting period",
            "ఆరోగ్య భీమా",
        ],
    ),
    FinancialDocument(
        doc_id="claim_settlement_ratio_csr",
        title="Claim Settlement Ratio (CSR) and Incurred Claim Ratio (ICR)",
        category="Insurance Basics",
        content=(
            "Claim Settlement Ratio (CSR) published annually by IRDAI represents the percentage of claims an insurance company pays out compared to "
            "the total claims received. A CSR above 95% indicates reliable claim settlement. Incurred Claim Ratio (ICR) measures the total claim payouts "
            "divided by the net premium collected, reflecting the insurer's underwriting sustainability."
        ),
        keywords=[
            "claim settlement ratio",
            "csr",
            "irdai",
            "icr",
            "insurance reliability",
            "క్లెయిమ్",
        ],
    ),
]
