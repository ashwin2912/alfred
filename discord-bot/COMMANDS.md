# Alfred Discord Bot - Commands Reference

Complete reference for all Discord bot commands, their usage, and workflows.

**Last Updated**: December 14, 2024

---

## Table of Contents

1. [User Commands](#user-commands)
2. [Admin Commands](#admin-commands)
3. [Team Management Commands](#team-management-commands)
4. [Task Management Commands](#task-management-commands)
5. [Project Planning Commands](#project-planning-commands)
6. [Admin Configuration Commands](#admin-configuration-commands)
7. [Complete Workflows](#complete-workflows)

---

## User Commands

### `/start-onboarding`

**Description**: Submit your onboarding request to join the organization.

**Who can use**: Any Discord server member

**Parameters**: None (opens an interactive modal)

**What it does**:
1. Opens a modal form requesting:
   - Full Name
   - Work Email
   - Phone Number (optional)
   - Bio (skills and experience)
2. Creates a `pending_onboarding` record in database
3. Posts request to `#admin-onboarding` channel for admin review
4. Waits for admin approval

**User Experience**:
```
User: /start-onboarding
[Modal appears with form fields]
User: [Fills out form and submits]
Bot: ✅ Your onboarding request has been submitted! 
     Please wait for admin approval.
```

**Notes**:
- Can resubmit if you have a pending request (deletes old one)
- Cannot submit if already approved
- Must provide valid email address

---

### `/my-tasks`

**Description**: View all your assigned tasks from ClickUp.

**Who can use**: Onboarded team members with ClickUp access

**Parameters**: None

**What it does**:
1. Fetches all tasks assigned to you from configured ClickUp lists
2. Displays tasks in an interactive embed with pagination
3. Shows: Task name, status, priority, due date

**User Experience**:
```
User: /my-tasks
Bot: 📋 Your Tasks (Page 1/3)
     
     1. Fix authentication bug
        Status: In Progress | Priority: High | Due: Dec 15
     
     2. Write API documentation
        Status: To Do | Priority: Medium | Due: Dec 20
     
     [Previous] [Next] buttons
```

**Notes**:
- Only shows tasks from lists configured by admin via `/add-list`
- Requires ClickUp API token set during onboarding
- Updates in real-time from ClickUp

---

### `/task-info <task_id>`

**Description**: Get detailed information about a specific task.

**Who can use**: Onboarded team members with ClickUp access

**Parameters**:
- `task_id` (required): The ClickUp task ID

**What it does**:
1. Fetches task details from ClickUp
2. Displays comprehensive information including:
   - Task name and description
   - Status, priority, due date
   - Assignees
   - Tags
   - Custom fields
   - Attachments
   - Comments

**User Experience**:
```
User: /task-info abc123
Bot: 📝 Task Details
     
     Fix Authentication Bug
     Status: In Progress | Priority: High
     Due: Dec 15, 2024
     
     Description:
     Users are unable to log in with OAuth...
     
     Assignees: @john, @sarah
     Tags: bug, auth, urgent
     
     [View in ClickUp]
```

**Notes**:
- Task ID can be found in ClickUp URL or from `/my-tasks`
- Shows only tasks you have access to

---

### `/task-comment <task_id> <comment>`

**Description**: Add a comment to a ClickUp task.

**Who can use**: Onboarded team members with ClickUp access

**Parameters**:
- `task_id` (required): The ClickUp task ID
- `comment` (required): Your comment text

**What it does**:
1. Posts your comment to the specified ClickUp task
2. Confirms successful posting
3. Provides link to view in ClickUp

**User Experience**:
```
User: /task-comment abc123 "Deployed the fix to staging"
Bot: ✅ Comment added to task
     [View in ClickUp]
```

**Notes**:
- Must have permission to comment on the task
- Comments are visible to all task collaborators
- Supports Markdown formatting

---

## Admin Commands

### Approve Onboarding (Button Click)

**Description**: Approve a pending onboarding request.

**Who can use**: Admins (members in database)

**How to use**:
1. Go to `#admin-onboarding` channel
2. Find the pending request embed
3. Click "✅ Approve" button

**What it does**:
1. Creates Supabase auth user with temporary password
2. Creates `team_members` database record
3. Creates Google Doc profile in main "Team Management" folder
4. Adds user to main roster spreadsheet
5. Sends welcome DM to user with:
   - Profile document link
   - Temporary password
   - Next steps
6. Updates the request embed to show "Approved"

**Admin Experience**:
```
[Request embed shows:]
New Onboarding Request
Name: John Doe
Email: john@example.com
Bio: 5 years experience in...

[Admin clicks "✅ Approve"]

Bot: ✅ User approved successfully! 
     Use /add-to-team to assign them to a team.

[User receives DM with welcome message]
```

**Notes**:
- You must be in the database as a team member to approve
- Creates profile in main folder (not team-specific)
- User is NOT assigned to a team yet

---

### Reject Onboarding (Button Click)

**Description**: Reject a pending onboarding request.

**Who can use**: Admins (members in database)

**How to use**:
1. Go to `#admin-onboarding` channel
2. Find the pending request embed
3. Click "❌ Reject" button
4. Enter rejection reason in modal

**What it does**:
1. Updates request status to "rejected" in database
2. Records rejection reason
3. Sends DM to user with rejection notification
4. Updates the request embed

**Admin Experience**:
```
[Admin clicks "❌ Reject"]
[Modal appears asking for reason]
Admin: "Please reapply with more details about your experience"
[Submits]

Bot: ✅ Request rejected.

[User receives DM with rejection reason]
```

---

## Team Management Commands

### `/create-team`

**Description**: Create a new team with complete infrastructure.

**Who can use**: Admins only

**Parameters**:
- `team_name` (required): Name of the team (e.g., "Engineering")
- `team_color` (required): Color for Discord roles
  - Choices: Blue, Green, Red, Purple, Orange, Yellow, Teal, Pink
- `description` (required): Brief team description
- `team_lead` (optional): Member to assign as team lead

**What it does**:
1. Creates two Discord roles:
   - Team role (e.g., "Engineering")
   - Manager role (e.g., "Engineering Manager") with elevated permissions
2. Creates Discord channels:
   - Category: "Engineering Team"
   - #engineering-general
   - #engineering-standups
3. Creates Google Drive folder structure:
   - Team folder
   - Team Overview doc
   - Team Roster spreadsheet
4. Creates team record in database with all IDs
5. If team lead specified: assigns both roles and adds to roster

**Admin Experience**:
```
Admin: /create-team 
       team_name:Engineering 
       team_color:Blue 
       description:"Software development team"
       team_lead:@john

Bot: ✅ Team Created: Engineering
     
     📋 What Was Created
     • Team Role: @Engineering (Blue)
     • Manager Role: @Engineering Manager
     • Channels: #engineering-general, #engineering-standups
     • Google Drive Folder: [View Folder]
     • Team Overview: [View Document]
     • Team Roster: [View Spreadsheet]
     • Team Lead: @john
     
     🎯 Next Steps
     1. Use /add-to-team to add members
     2. Use /set-team-workspace to connect ClickUp
     3. Team lead can use /brainstorm for project planning
```

**Notes**:
- Creates complete infrastructure in one command
- Manager role has permissions to manage messages and threads
- All resources are automatically linked in database
- Announcement posted in #engineering-general

---

### `/add-to-team`

**Description**: Add a member to a team or promote to team lead.

**Who can use**: Admins only

**Parameters**:
- `member` (required): The Discord member to add
- `team_name` (required): Name of the team (autocomplete from database)
- `role` (optional): Member's role in the team (e.g., "Senior Engineer")
- `make_team_lead` (optional): Make this person the team lead (default: False)

**What it does**:
1. Checks if member has completed onboarding
2. If new to team:
   - Adds to `team_memberships` table
   - Assigns team Discord role
   - Adds to team roster spreadsheet
3. If `make_team_lead=True`:
   - Assigns manager Discord role
   - Updates `team_lead_id` in teams table
4. Sends DM to member with team details
5. Posts announcement in team channel

**Admin Experience**:

**Adding new member:**
```
Admin: /add-to-team 
       member:@sarah 
       team_name:Engineering 
       role:Senior Engineer

Bot: ✅ Added sarah to Engineering
     
     📋 Updates
     • Team Role: ✅ @Engineering assigned
     • Team Roster: ✅ Added to spreadsheet
     • Channels: ✅ Can access #engineering-general, #engineering-standups

[sarah receives DM]
[#engineering-general]: 👋 Welcome @sarah to the team! (Senior Engineer)
```

**Promoting to team lead:**
```
Admin: /add-to-team 
       member:@john 
       team_name:Engineering 
       make_team_lead:True

Bot: ✅ Promoted john to Team Lead of Engineering
     
     📋 Updates
     • Team Role: ✅ @Engineering assigned
     • Manager Role: ✅ @Engineering Manager assigned
     • Team Roster: ℹ️ Already in roster

[john receives promotion DM]
[#engineering-general]: 🎖️ @john has been promoted to Team Lead! Congrats! 🎉
```

**Notes**:
- Team names autocomplete from database (dynamic)
- Can promote existing members without re-adding
- Only one team lead per team
- Member must complete onboarding first

---

### `/team-report`

**Description**: Generate a comprehensive task report for your team.

**Who can use**: Team Leads and Admins only

**Parameters**: None (auto-detects team from channel)

**What it does**:
1. Fetches all tasks from team's configured ClickUp lists
2. Validates ClickUp API token
3. Generates rich report with:
   - Total tasks and active members
   - Status breakdown
   - Priority distribution
   - Top contributors
   - Recent tasks (top 10) with clickable links
   - Overdue tasks
   - Tasks due soon (within 3 days)

**Team Lead Experience**:
```
# In #engineering-general
Team Lead: /team-report

Bot: 📊 Engineering Team Report
     Daily status report • December 14, 2024
     
     📈 Overview
     Total Tasks: 24
     Active Members: 5
     ⚠️ Overdue: 2
     ⏰ Due Soon (3 days): 4
     
     📝 Recent Tasks
     🔴 [Implement auth system](clickup-link) - In Progress (john_doe)
     🟡 [Design database schema](clickup-link) - To Do (jane_smith)
     ...
```

**Notes**:
- Must be run in team channel (#team-general or #team-standups)
- Requires at least one team member to have ClickUp token configured
- Shows error if token is expired/invalid
- Only shows tasks from configured project lists

---

## Task Management Commands

### `/add-project-list`

**Description**: Add a ClickUp list to your team's project tracking.

**Who can use**: Team Leads and Admins (with Manager roles)

**Parameters**:
- `list_id` (required): The ClickUp list ID
- `list_name` (required): Friendly name for the list
- `description` (optional): Description of this list

**What it does**:
1. Auto-detects team from the channel you're in
2. Adds list to `clickup_lists` table for your team
3. Tasks from this list will appear in `/my-tasks` and `/team-report`
4. Confirms successful addition

**Team Lead Experience**:
```
# In #engineering-general
Team Lead: /add-project-list 
           list_id:901112661012
           list_name:Sprint Tasks
           description:Current sprint work

Bot: ✅ Project List Added
     Successfully added ClickUp list to Engineering team
     
     List Name: Sprint Tasks
     List ID: 901112661012
     Team: Engineering
     
     📝 Note
     Team members will now only see tasks from configured 
     project lists in /my-tasks
```

**Notes**:
- List ID found in ClickUp list URL (e.g., `/l/6-901112661012-1` → `901112661012`)
- Must run in team channel (#team-general or #team-standups)
- Multiple lists can be added per team
- Each list can only be added once (unique constraint)

---

### `/remove-project-list`

**Description**: Remove a ClickUp list from team tracking.

**Who can use**: Team Leads and Admins

**Parameters**:
- `list_id` (required): The ClickUp list ID to remove

**What it does**:
1. Deactivates list in `clickup_lists` table
2. Tasks from this list will no longer appear in `/my-tasks` or `/team-report`
3. Confirms successful removal

**Admin Experience**:
```
Admin: /remove-project-list list_id:901112661012

Bot: ✅ Project List Removed
     List 901112661012 has been deactivated.
     
     Team members will no longer see tasks from this 
     list in /my-tasks.
```

---

### `/list-project-lists`

**Description**: View all configured ClickUp lists for your team.

**Who can use**: Admins only

**Parameters**: None

**What it does**:
1. Fetches lists from `clickup_lists` table
2. Displays list IDs and names by team
3. Shows which lists are active/inactive

**Admin Experience**:
```
Admin: /list-project-lists

Bot: 📋 All Project Lists
     Configured ClickUp lists by team
     
     Engineering (2 lists)
     • 901112661012 - Sprint Tasks
     • 901112661013 - Backlog
     
     Product (1 list)
     • 901112661014 - Feature Requests
```

**Team-Specific View**:
```
Team Lead: /list-project-lists team_name:Engineering

Bot: 📋 Engineering Project Lists (2)
     
     Sprint Tasks
     ID: 901112661012
     Status: ✅ Active
     
     Backlog
     ID: 901112661013
     Description: Long-term tasks
     Status: ✅ Active
```

---

## Project Planning Commands

### `/brainstorm`

**Description**: Start an AI-powered project planning session.

**Who can use**: Team members (usually team leads)

**Parameters**: None (opens an interactive modal)

**What it does**:
1. Opens modal asking for:
   - Project Name
   - Project Description
   - Key Objectives
   - Team (dropdown)
2. Sends data to Project Planning API
3. AI analyzes and generates:
   - Suggested milestones
   - Task breakdown
   - Timeline estimates
   - Resource requirements
4. Creates Google Doc with brainstorming session
5. Stores in team's Google Drive folder

**User Experience**:
```
User: /brainstorm
[Modal appears]
User fills:
  Project Name: "Mobile App Redesign"
  Description: "Redesign our mobile app with modern UI..."
  Objectives: "Improve UX, increase engagement..."
  Team: Engineering

Bot: 🧠 Processing your brainstorming session...
     [Progress updates]
     
     ✅ Brainstorming complete!
     
     📊 AI Analysis:
     • 4 suggested milestones
     • 23 tasks identified
     • Estimated timeline: 8 weeks
     
     📄 Document created: [View Brainstorming Session]
     
     🎯 Next Steps:
     Review the document and use /publish-plan to create ClickUp tasks
```

**Notes**:
- Uses OpenAI GPT-4 for analysis
- Creates structured Google Doc
- Stored in team's folder
- Does not create ClickUp tasks (use `/publish-plan` for that)

---

## Admin Configuration Commands

### `/help`

**Description**: Show all available commands with descriptions.

**Who can use**: Everyone

**Parameters**: None

**What it does**:
Displays comprehensive list of all commands organized by category.

---

## Complete Workflows

### Workflow 1: New Member Onboarding

**Actors**: New User, Admin

**Steps**:

1. **User joins Discord server**
   - Bot sends welcome message in #alfred

2. **User runs `/start-onboarding`**
   - Fills out modal with name, email, bio
   - Submits

3. **Admin reviews in #admin-onboarding**
   - Sees embed with user info
   - Clicks "✅ Approve"

4. **System creates resources**
   - Supabase auth user
   - Database record
   - Google Doc profile
   - Main roster entry

5. **User receives DM**
   - Welcome message
   - Profile link
   - Temporary password
   - Instructions to wait for team assignment

6. **Admin assigns to team**
   - `/add-to-team @user team:Engineering role:Engineer`

7. **System assigns team**
   - Adds to database
   - Assigns Discord role
   - Adds to team roster
   - Grants channel access

8. **User receives team DM**
   - Team assignment notification
   - Channel links
   - Profile link

9. **Team channel announcement**
   - Welcome message posted

**Result**: User is fully onboarded and assigned to team

---

### Workflow 2: Creating a New Team

**Actors**: Admin

**Steps**:

1. **Admin runs `/create-team`**
   ```
   team_name: Engineering
   team_color: Blue
   description: Software development team
   team_lead: @john
   ```

2. **System creates infrastructure**
   - Two Discord roles (team + manager)
   - Discord channels (category, general, standups)
   - Google Drive folder with docs
   - Database record

3. **If team lead specified**
   - Assigns both roles to lead
   - Adds to team roster
   - Updates team_lead_id

4. **Admin receives confirmation**
   - Shows all created resources
   - Provides next steps

5. **Announcement posted**
   - In #engineering-general
   - Welcome message for team

**Result**: Team fully set up with all infrastructure

---

### Workflow 3: Promoting Member to Team Lead

**Actors**: Admin, Team Member

**Steps**:

1. **Admin runs `/add-to-team`**
   ```
   member: @sarah
   team_name: Engineering
   make_team_lead: True
   ```

2. **System checks membership**
   - Detects sarah is already a member

3. **System promotes**
   - Assigns manager Discord role
   - Updates team_lead_id in database

4. **Sarah receives promotion DM**
   - Congratulations message
   - Responsibilities listed
   - Manager permissions explained

5. **Team channel announcement**
   - "🎖️ @sarah has been promoted to Team Lead!"

**Result**: Member promoted to team lead with manager permissions

---

### Workflow 4: Working with Tasks

**Actors**: Team Member

**Steps**:

1. **View all tasks**
   - `/my-tasks`
   - See paginated list

2. **Get task details**
   - `/task-info abc123`
   - See full description, comments, attachments

3. **Add comment**
   - `/task-comment abc123 "Completed the implementation"`
   - Comment posted to ClickUp

4. **Check updated tasks**
   - `/my-tasks` again
   - See status changes

**Result**: Member can manage tasks without leaving Discord

---

## Permission Levels

### Everyone (Server Members)
- `/start-onboarding`
- `/help`

### Onboarded Members
- `/my-tasks`
- `/task-info`
- `/task-comment`
- `/brainstorm` (team members)

### Admins (in database)
- All user commands, plus:
- Approve/Reject onboarding (button)
- `/create-team`
- `/add-to-team`
- `/set-team-workspace`
- `/add-list`
- `/remove-list`
- `/list-lists`

---

## Tips and Best Practices

### For Admins

1. **Onboarding**
   - Approve users promptly
   - Assign to team within 24 hours
   - Check Google Drive folders are created

2. **Team Management**
   - Create teams before onboarding members
   - Assign clear team leads
   - Use descriptive role names

3. **Task Management**
   - Configure project lists before team starts
   - Use meaningful list names
   - Remove old/unused lists

### For Users

1. **Onboarding**
   - Provide detailed bio with skills
   - Use work email
   - Check DMs for notifications

2. **Tasks**
   - Check `/my-tasks` daily
   - Use `/task-comment` for updates
   - Keep ClickUp API token secure

3. **Projects**
   - Use `/brainstorm` for new projects
   - Provide detailed objectives
   - Review AI suggestions before publishing

---

## Troubleshooting

### "❌ Could not find your admin profile"
**Cause**: You're not in the database as a team member
**Fix**: Have another admin add you via direct SQL or onboarding

### "❌ Team '<name>' not found in database"
**Cause**: Team hasn't been created yet
**Fix**: Use `/create-team` first

### "❌ <user> has not completed onboarding yet"
**Cause**: Trying to add user who hasn't been approved
**Fix**: User must complete `/start-onboarding` and get approved first

### "⚠️ This request has already been approved"
**Cause**: Trying to approve already-approved request
**Fix**: User is already onboarded, use `/add-to-team` instead

### Tasks not showing in `/my-tasks`
**Cause**: ClickUp lists not configured
**Fix**: Admin needs to use `/add-list` for each relevant list

---

## Environment Setup

Required environment variables in `.env`:

```bash
# Discord
DISCORD_BOT_TOKEN=your_token
DISCORD_GUILD_ID=your_guild_id
DISCORD_ADMIN_CHANNEL_ID=channel_id_for_admin_onboarding
DISCORD_ALFRED_CHANNEL_ID=channel_id_for_alfred

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_role_key

# Google
GOOGLE_CREDENTIALS_PATH=/path/to/service-account.json
GOOGLE_DRIVE_FOLDER_ID=main_team_management_folder_id
GOOGLE_MAIN_ROSTER_SHEET_ID=main_roster_spreadsheet_id
GOOGLE_DELEGATED_USER_EMAIL=your_workspace_email@example.com

# ClickUp (optional)
CLICKUP_API_BASE_URL=https://api.clickup.com/api/v2

# Project Planning (optional)
PROJECT_PLANNING_API_URL=http://localhost:8001
GOOGLE_DRIVE_PROJECT_PLANNING_FOLDER_ID=folder_for_brainstorms
```

---

**For more information, see:**
- `README.md` - General setup instructions
- `progress.md` - Development history and features
- Architecture docs in `/docs` folder
