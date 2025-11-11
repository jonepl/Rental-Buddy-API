How do I acquire the following given:
 - property taxes 
 - insurance
 - hoa
 - 


I have attached my up to date PRD document. I would like to expand my MPV to include more features. I need help fleshing out the details. Here are some features that I would like to include, after we have worked through the details I would like to update my attached PRD.  See the new features below

# App use cases: 
1. A user determines rental area using filter like geolocation bedrooms/bathrooms, etc and is presented with rental data from RentCast and the following new information:
  - Provide soft metrics
    - School
    - Transportation
    - Crime
    - Bike

  - Climate Risk
    - Flood
    - Fire
    - Wind
    - Air
    - Heat Factor
2. Given the user has defined an area of interest, the user will provide expense metrics to the UI
    - Property Taxes
    - Insurance
    - Maintenance & Repairs (estimated %)
    - HOA Fees (if applicable)
    - Property Management Fee (%)
    - Utilities (if owner-paid)
    - CapEx Reserves (Capital Expenditures)
    - Miscellaneous / Admin Costs
3. With the provided expense metrics, the backend should be able to rank the currently viewed properties that cash flow in order to provide data to the UI to be rendered.
 - Compare/Display Investable rental properties
    - Net Operating Income (NOI) = Gross Income − Operating Expenses
    - Cash Flow (Before Financing) = NOI − Debt Service
    - Cash Flow (After Financing) = NOI − Mortgage Payments
    - Cash-on-Cash Return (%) = (Annual Cash Flow ÷ Total Cash Invested) × 100
    - Gross Rent Multiplier (GRM) = Property Price ÷ Annual Rent
    - Cap Rate (%) = (NOI ÷ Purchase Price) × 100
    - Debt Service Coverage Ratio (DSCR) = NOI ÷ Annual Debt Service
    - Break-even Occupancy (%) = (Operating Expenses + Debt Service) ÷ Gross Income

    Appreciation & Equity Metrics
      - Price per Square Foot
      - Historical Appreciation Rate (5-year, 10-year)
      - Projected Appreciation (%)
      - Equity Growth Over Time
      - Loan-to-Value Ratio (LTV%)
      - Principal Paydown Over Time

4. Additional metrics can be visible via clickable link to view a deep dive into Profitability
  Advanced / Derived Metrics
  More sophisticated metrics seasoned investors track:
    - Internal Rate of Return (IRR)
    - Return on Investment (ROI)
    - Total Return (Cash Flow + Appreciation)
    - Operating Expense Ratio (%) = Operating Expenses ÷ Gross Income
    - Rent-to-Price Ratio (%) = Monthly Rent ÷ Purchase Price
    - 1% Rule Indicator (Monthly Rent ≥ 1% of Purchase Price)
    - 50% Rule (Operating expenses ≈ 50% of rent)
    - Rent Growth vs. Inflation
    - Expense Growth Rate (CAGR)

I have not figure  out how to retrieve/generate the data required to perform the use cases above. Let's explore how to incorporate these features into my existing feature set.