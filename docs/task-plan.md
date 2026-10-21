# Flex Library Practice task plan

Seven mandatory coding tasks were selected. Each has its own branch and PR to main.

| Order | Task | Depends on | Acceptance criteria |
| --- | --- | --- | --- |
| 1 | Book CRUD | Foundation | Model, migration, list/detail/create/update/delete, input/database validation |
| 2 | Book permissions | 1 | Public reads; staff-only writes; anonymous/customer denial tests |
| 3 | User accounts | Foundation | Email accounts, password hashing/validation, custom-header JWT, private profile |
| 4 | Borrowing reads | 1, 3 | Date constraints, nested book details, authenticated owner-only access |
| 5 | Borrowing creation | 4 | Assign current user/date, reject empty stock, atomic inventory decrement |
| 6 | Borrowing filtering | 4 | Active/returned filter, staff user filter, no customer data leakage |
| 7 | Borrowing return | 5, 6 | One-time return, actual return date, atomic inventory increment, contention tests |

Recommended review/merge order: 1 → 2 → 3 → 4 → 5 → 6 → 7. Later branches include their dependencies; their diffs against main shrink as preceding PRs are merged.

To Do → In Progress → On Review → Done. Move a card to Done only after its PR is actually merged; passing tests alone does not mean merged.

Shared quality criteria: at least 60% custom-code coverage, Swagger documentation, setup instructions, no secrets/redundant files committed, descriptive branches and commits.
