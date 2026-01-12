from odoo import fields

def test_milestones(env):
    print("Starting Verification...")
    # Create Project
    project = env['project.project'].create({'name': 'Test Milestone Project'})
    
    # Create Milestones (Sections) and Tasks
    # Phase 1: 25%
    p1 = env['project.plan.line'].create({
        'project_id': project.id,
        'name': 'Phase 1',
        'display_type': 'line_section',
        'milestone_type': 'gap_analysis',
        'milestone_weight': 25
    })
    t1_1 = env['project.plan.line'].create({
        'project_id': project.id,
        'name': 'Task 1.1',
    })
    t1_2 = env['project.plan.line'].create({
        'project_id': project.id,
        'name': 'Task 1.2',
    })
    t1_3 = env['project.plan.line'].create({
        'project_id': project.id,
        'name': 'Task 1.3',
    })
    t1_4 = env['project.plan.line'].create({
        'project_id': project.id,
        'name': 'Task 1.4',
    })
    
    # Phase 2: 50%
    p2 = env['project.plan.line'].create({
        'project_id': project.id,
        'name': 'Phase 2',
        'display_type': 'line_section',
        'milestone_type': 'implementation',
        'milestone_weight': 50
    })
    t2_1 = env['project.plan.line'].create({
        'project_id': project.id,
        'name': 'Task 2.1',
    })
    t2_2 = env['project.plan.line'].create({
        'project_id': project.id,
        'name': 'Task 2.2',
    })
    
    # Phase 3: 25%
    p3 = env['project.plan.line'].create({
        'project_id': project.id,
        'name': 'Phase 3',
        'display_type': 'line_section',
        'milestone_type': 'training',
        'milestone_weight': 25
    })
    t3_1 = env['project.plan.line'].create({
        'project_id': project.id,
        'name': 'Task 3.1',
    })

    # Trigger compute
    project._compute_completion_percent()
    print(f"Initial Completion: {project.completion_percent}% (Expected 0.0)")
    
    # Mark 1 task in Phase 1 as Done
    t1_1.status_done = True
    project._compute_completion_percent()
    print(f"After Task 1.1 Done: {project.completion_percent}% (Expected 6.25)")
    
    # Mark all Phase 1 Done
    t1_2.status_done = True
    t1_3.status_done = True
    t1_4.status_done = True
    project._compute_completion_percent()
    print(f"After Phase 1 Done: {project.completion_percent}% (Expected 25.0)")
    
    # Mark 1 task in Phase 2 Done
    t2_1.status_done = True
    project._compute_completion_percent()
    # 25 + (1/2 * 50) = 25 + 25 = 50
    print(f"After Task 2.1 Done: {project.completion_percent}% (Expected 50.0)")

    # Mark all done
    t2_2.status_done = True
    t3_1.status_done = True
    project._compute_completion_percent()
    print(f"All Done: {project.completion_percent}% (Expected 100.0)")

test_milestones(env)
