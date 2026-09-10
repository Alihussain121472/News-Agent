# NovaBrief student tools

## What was missing

The website already offered news, saved articles, summaries, and program discovery.
Students could not save an opportunity as an application, record preparation work,
track its outcome, plan study tasks, or export deadlines. The dashboard program
query also returned a fixed list instead of the programs maintained in the admin
app. The admin visibility control referenced a missing database method.

## Implemented

- **My Planner** in both desktop and mobile dashboard navigation.
- Private application records, including opportunities added from NovaBrief or
  manually entered by the student. Statuses: saved, preparing, submitted,
  interview, offer, and closed.
- Editable deadline, provider link, preparation checklist, and private notes.
- Study tasks with optional due dates, completion, editing, and removal.
- Deadline badges and an iCalendar download for upcoming saved/preparing
  applications and unfinished tasks. This is a snapshot, not an automatic sync
  or an email reminder. Students configure notifications in their calendar app.
- Program search, category/organization filters, deadline filters, sorting and
  pagination. The program browser reads actual active database records and
  excludes opportunities with a past recorded deadline.
- Working admin program visibility and correct IDs returned when adding programs.

Tracking a program does not apply to the provider. A missing deadline is explicitly
unconfirmed, not assumed to be rolling or open. The five database program records
checked during this task had no deadlines. Students should verify closing times,
eligibility and availability on the provider's website.

## Storage and safeguards

The existing Flask sign-in is retained. All planner reads and writes are scoped
to the signed-in email; a client-supplied owner is never accepted. Changes require
a session-bound CSRF token. Inputs, URLs, dates and IDs are validated. Writes are
transactional, duplicate program tracking preserves existing notes, and each
account can hold 200 applications and 200 study tasks.

The additive `student_applications` and `student_study_tasks` schema is installed
by the existing database initialization path. RLS is enabled, with no direct
browser-role grants: access is through the authenticated Flask server. The
`add_private_student_planner` migration was also applied successfully to the
connected News-Agent database. Existing users, email settings and program records
were not edited by this migration.

## Verification and rollout

102 selected offline Python tests passed, covering the new APIs and surrounding
student/admin features. JavaScript syntax checks and tracked-file whitespace
checks passed. One stale admin test fixture was corrected to use the dashboard's
existing `daily_visitors` field.

The actual-database assertion script is `student_planner/verification.sql`. It
uses only temporary table copies, explicit test IDs and a rollback; it does not
insert live students or send emails. Execution and a follow-up live permission
check were blocked by the safety-review service's usage limit. They are **not
verified**. Browser interaction testing and publishing are also not confirmed.

The website code changes still need to be published through the existing Render
deployment. Do not redeploy unrelated local scripts or change email/SEO settings
as part of this release. After publishing, verify two separate student accounts,
application/task save and refresh, program visibility, calendar download, mobile
layout and error recovery. No claim is made that the entire website is bug-free
or that the older email/domain configuration has been verified by this work.
