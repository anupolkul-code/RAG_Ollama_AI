# Case Study: Normalizing a Sales Order Database from 0NF to 5NF

## 1. The Business and the Vocabulary

A regional office-supply distributor tracks orders in a single spreadsheet: one row per order, with customer details, the assigned sales representative, and a list of items typed into one cell. As the business grows, this sheet produces duplicate data, contradictory updates, and rows that cannot be entered until unrelated facts exist. This case study walks the same data through seven stages of relational design, from the raw spreadsheet (0NF) to Fifth Normal Form (5NF), fixing one category of anomaly at each step.

A few terms recur throughout. A **functional dependency (FD)**, written X → Y, means that a value of X always determines exactly one value of Y — for example, ProductID → UnitPrice. A **candidate key** is a minimal set of attributes that uniquely identifies a row; a **composite key** is a candidate key made of more than one attribute. A **superkey** is any attribute set that determines the whole row, whether minimal or not. These four ideas are enough to follow every stage below.

## 2. 0NF — The Unnormalized Spreadsheet

**Definition.** Unnormalized form is the raw, flat table as it exists before any design rules are applied: it may hold repeating groups or multiple values inside one cell.

The distributor's `ORDER` sheet packs every item of an order into one text field:

| OrderID | CustomerID | CustomerName | CustomerCity | SalesRepID | SalesRepName | SalesRepRegion | Items |
|---|---|---|---|---|---|---|---|
| O1001 | C10 | Acme Clinic | Denver | R5 | J. Kim | West | P100:Stapler:2:6.50; P205:Paper Ream:10:4.25 |
| O1002 | C11 | Blue Ridge School | Boulder | R5 | J. Kim | West | P205:Paper Ream:5:4.25 |
| O1003 | C10 | Acme Clinic | Denver | R7 | M. Diaz | West | P100:Stapler:1:6.50; P310:Binder:3:3.00 |

The `Items` column hides an unknown number of product entries per row. It cannot be searched, summed, or joined without first parsing the text — a query as simple as "total staplers sold this month" is impractical.

## 3. 1NF — Atomic Values, No Repeating Groups

**Definition.** First Normal Form requires every cell to hold a single, atomic value, eliminating repeating groups by giving each repeated fact its own row.

Splitting `Items` produces one row per order line, with the composite key {OrderID, ProductID}:

| OrderID | ProductID | ProductDesc | Qty | UnitPrice | CustomerID | CustomerName | CustomerCity | SalesRepID | SalesRepName | SalesRepRegion |
|---|---|---|---|---|---|---|---|---|---|---|
| O1001 | P100 | Stapler | 2 | 6.50 | C10 | Acme Clinic | Denver | R5 | J. Kim | West |
| O1001 | P205 | Paper Ream | 10 | 4.25 | C10 | Acme Clinic | Denver | R5 | J. Kim | West |
| O1002 | P205 | Paper Ream | 5 | 4.25 | C11 | Blue Ridge School | Boulder | R5 | J. Kim | West |
| O1003 | P100 | Stapler | 1 | 6.50 | C10 | Acme Clinic | Denver | R7 | M. Diaz | West |
| O1003 | P310 | Binder | 3 | 3.00 | C10 | Acme Clinic | Denver | R7 | M. Diaz | West |

The table is queryable, but "Stapler" and "6.50" now repeat on every line that mentions P100, and the customer and rep facts repeat on every line of an order. The table is in 1NF but riddled with redundancy.

## 4. 2NF — Removing Partial Dependencies

**Definition.** Second Normal Form requires 1NF plus the absence of a **partial dependency** — no attribute that is not part of the key may depend on only *part* of a composite key.

Here `ProductID → ProductDesc, UnitPrice` depends on half the key, and `OrderID → CustomerID, CustomerName, CustomerCity, SalesRepID, SalesRepName, SalesRepRegion` depends on the other half. Only `Qty` genuinely needs both {OrderID, ProductID}. The fix is to split off each partial determinant:

**PRODUCT** (key: ProductID)

| ProductID | ProductDesc | UnitPrice |
|---|---|---|
| P100 | Stapler | 6.50 |
| P205 | Paper Ream | 4.25 |
| P310 | Binder | 3.00 |

**ORDER** (key: OrderID)

| OrderID | CustomerID | CustomerName | CustomerCity | SalesRepID | SalesRepName | SalesRepRegion |
|---|---|---|---|---|---|---|
| O1001 | C10 | Acme Clinic | Denver | R5 | J. Kim | West |
| O1002 | C11 | Blue Ridge School | Boulder | R5 | J. Kim | West |
| O1003 | C10 | Acme Clinic | Denver | R7 | M. Diaz | West |

`ORDER_LINE(OrderID, ProductID, Qty)` holds the true composite-key fact. A price change for the stapler now touches one row, not every line that ever sold one.

## 5. 3NF — Removing Transitive Dependencies

**Definition.** Third Normal Form requires 2NF plus the absence of a **transitive dependency**: a non-key attribute must not depend on another non-key attribute rather than directly on the key.

In `ORDER`, `CustomerName` and `CustomerCity` depend on `CustomerID`, not on `OrderID` itself; `SalesRepName` and `SalesRepRegion` similarly depend on `SalesRepID`. Moving a customer's city still means editing every order row for that customer. The remedy is to peel off each intermediate determinant:

**ORDER** (key: OrderID) — `OrderID, CustomerID, SalesRepID`
**CUSTOMER** (key: CustomerID) — `CustomerID, CustomerName, CustomerCity`
**SALESREP** (key: SalesRepID) — `SalesRepID, SalesRepName, SalesRepRegion`

A customer's address now lives in exactly one row, and a new customer can be entered even before their first order exists.

## 6. BCNF — Tightening the Determinant Rule

**Definition.** Boyce–Codd Normal Form strengthens 3NF: for every non-trivial functional dependency X → Y, X must be a superkey, with no exception for the case where Y happens to be part of a key.

The distributor later restricts each sales rep to one product category, and each customer works with one rep per category purchased. This gives `ASSIGNMENT(CustomerID, Category, SalesRepID)` with `{CustomerID, Category} → SalesRepID` and `SalesRepID → Category`. Both `{CustomerID, Category}` and `{CustomerID, SalesRepID}` are candidate keys, so every attribute is prime and the table already satisfies 3NF — yet `SalesRepID → Category` has a determinant that is not itself a key, violating BCNF. Splitting into `REP_CATEGORY(SalesRepID, Category)` and `CUSTOMER_REP(CustomerID, SalesRepID)` removes the overlap; `Category` is now stored once per rep instead of once per customer-rep pair.

## 7. 4NF — Independent Multivalued Facts

**Definition.** A **multivalued dependency (MVD)**, written X ↠ Y, holds when the set of Y-values associated with an X-value is independent of every other attribute. Fourth Normal Form requires that whenever a non-trivial MVD X ↠ Y exists, X must be a superkey.

Suppose the HR system also records, in one table, the languages each rep speaks and the certifications they hold: `REP_SKILLS(SalesRepID, Language, Certification)`. Rep R5 speaks English, Spanish, and Korean, and holds ProductSafety and Ergonomics certifications — two facts that have nothing to do with each other. Because every language must be paired with every certification to avoid implying a false exclusion, R5 alone needs 3 × 2 = 6 rows. There is no FD here, so the table sits in BCNF, but it still forces a combinatorial blow-up. Splitting into `REP_LANGUAGE(SalesRepID, Language)` and `REP_CERT(SalesRepID, Certification)` needs only 3 + 2 = 5 rows for the same facts, and adding a new certification no longer requires inserting one row per language.

## 8. 5NF — Join Dependencies and the Three-Way Split

**Definition.** A **join dependency** generalizes the lossless-join idea to more than two fragments: a relation satisfies one when it can be reconstructed exactly by joining several of its projections. Fifth Normal Form (Project-Join Normal Form) requires that every join dependency present is already implied by the candidate keys — otherwise the table must be split into those projections.

The distributor authorizes a rep to supply a product to a customer under a three-way rule: authorization holds whenever the rep is certified for that product *and* the rep is assigned to that customer *and* the customer has an active account for that product line. No pair of these facts implies the third, so a single `AUTHORIZATION(Rep, Product, Customer)` table cannot be safely reduced to two projections. Consider:

`REP_PRODUCT`: (R5,P100), (R5,P205), (R7,P100)
`REP_CUSTOMER`: (R5,C10), (R5,C11), (R7,C10)
`PRODUCT_CUSTOMER`: (P100,C10), (P205,C10), (P100,C11)

Joining only `REP_PRODUCT` and `REP_CUSTOMER` on Rep produces (R5, P205, C11) as a candidate authorization — but P205 and C11 never appear together in `PRODUCT_CUSTOMER`, so that triple is spurious. Bringing in the third projection filters it out correctly, leaving exactly the four genuine authorizations. Because reconstructing the true table requires all three binary projections together, and no two suffice, the design must remain split three ways: `REP_PRODUCT(Rep, Product)`, `REP_CUSTOMER(Rep, Customer)`, and `PRODUCT_CUSTOMER(Product, Customer)`.

## 9. Summary

| Stage | Fixes | Running-example remedy |
|---|---|---|
| 0NF | — (starting point) | Flat sheet with an `Items` list |
| 1NF | Non-atomic cells | One row per order line |
| 2NF | Partial dependency on part of a key | Split off PRODUCT and ORDER |
| 3NF | Transitive dependency | Split off CUSTOMER and SALESREP |
| BCNF | Non-key determinant of a key attribute | Split REP_CATEGORY from CUSTOMER_REP |
| 4NF | Independent multivalued facts | Split REP_LANGUAGE from REP_CERT |
| 5NF | Join dependency not implied by keys | Three-way split of AUTHORIZATION |

Each stage removes one specific way the same fact could be stored more than once, at the cost of one additional join when the data is read back together.
