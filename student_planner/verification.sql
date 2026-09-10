-- Safe PostgreSQL verification: only temporary tables, explicit IDs, no real users.
-- Temporary tables shadow the live names within this transaction and are rolled back.
BEGIN;
CREATE TEMP TABLE student_applications
    (LIKE public.student_applications INCLUDING ALL) ON COMMIT DROP;
CREATE TEMP TABLE student_study_tasks
    (LIKE public.student_study_tasks INCLUDING ALL) ON COMMIT DROP;
INSERT INTO student_applications (id,email,program_id,title,deadline)
VALUES (1,'planner-a@example.invalid',1,'Application A',CURRENT_DATE + 7),
       (2,'planner-b@example.invalid',1,'Application B',NULL);
INSERT INTO student_study_tasks (id,email,title,due_date)
VALUES (1,'planner-a@example.invalid','Study task',CURRENT_DATE);
DO $$
DECLARE changed INTEGER;
BEGIN
    UPDATE student_applications SET status='preparing',notes='Private test note',
        checklist='["cv"]'::jsonb,updated_at=CURRENT_TIMESTAMP
        WHERE email='planner-a@example.invalid' AND id=1;
    ASSERT (SELECT checklist FROM student_applications WHERE id=1) = '["cv"]'::jsonb,
        'Checklist did not persist';
    UPDATE student_applications SET notes='Wrong owner'
        WHERE email='planner-b@example.invalid' AND id=1;
    GET DIAGNOSTICS changed = ROW_COUNT;
    ASSERT changed=0, 'Cross-user update was allowed';
    DELETE FROM student_applications WHERE email='planner-b@example.invalid' AND id=1;
    GET DIAGNOSTICS changed = ROW_COUNT;
    ASSERT changed=0, 'Cross-user deletion was allowed';
    ASSERT (SELECT COUNT(*) FROM student_applications WHERE email='planner-a@example.invalid')=1,
        'Owner filtering failed';
    BEGIN
        INSERT INTO student_applications(id,email,program_id,title)
        VALUES(3,'planner-a@example.invalid',1,'Duplicate');
        RAISE EXCEPTION 'Duplicate program application was allowed';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    BEGIN
        UPDATE student_applications SET status='not-a-status' WHERE id=1;
        RAISE EXCEPTION 'Invalid application status was allowed';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    UPDATE student_study_tasks SET completed=TRUE
        WHERE email='planner-a@example.invalid' AND id=1;
    ASSERT (SELECT completed FROM student_study_tasks WHERE id=1), 'Task completion was not saved';
    UPDATE student_study_tasks SET completed=FALSE
        WHERE email='planner-b@example.invalid' AND id=1;
    GET DIAGNOSTICS changed = ROW_COUNT;
    ASSERT changed=0, 'Cross-user task update was allowed';
    DELETE FROM student_study_tasks WHERE email='planner-a@example.invalid' AND id=1;
    ASSERT (SELECT COUNT(*) FROM student_study_tasks)=0, 'Task removal failed';
END $$;
-- Exercise the real opportunity query shape with the temporary per-user tracker.
SELECT COUNT(*) AS visible_opportunities FROM (
    SELECT p.id, a.id AS application_id FROM public.student_programs p
    LEFT JOIN student_applications a ON a.program_id=p.id AND a.email='planner-a@example.invalid'
    WHERE p.is_active=TRUE AND (p.deadline IS NULL OR p.deadline >= CURRENT_DATE)
    ORDER BY p.deadline ASC NULLS LAST,p.id DESC LIMIT 12 OFFSET 0
) AS opportunities;
ROLLBACK;
SELECT 'Planner PostgreSQL assertions passed; temporary test data rolled back.' AS result;
