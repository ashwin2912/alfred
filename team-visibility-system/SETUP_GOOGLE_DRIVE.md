# Google Drive API Setup Guide

## Step 1: Place Your Credentials File

You mentioned you already have the Google Drive credentials JSON file. Place it in the project:

```bash
mkdir -p team-visibility-system/credentials
cp /path/to/your/credentials.json team-visibility-system/credentials/google-service-account.json
```

## Step 2: Share Your Google Doc with the Service Account

1. Open your credentials JSON file and find the `client_email` field
   - It looks like: `something@project-name.iam.gserviceaccount.com`

2. Go to your Google Doc (Weekly Goals document)

3. Click "Share" button

4. Add the service account email (the `client_email` from step 1)

5. Give it **Viewer** access (read-only)

6. Click "Done"

## Step 3: Get the Google Doc ID

From your Google Doc URL:
```
https://docs.google.com/document/d/DOCUMENT_ID_HERE/edit
```

Copy the `DOCUMENT_ID_HERE` part.

## Step 4: Update .env File

Add to your `.env` file:

```bash
# Google Drive Configuration
GDRIVE_CREDENTIALS_PATH=credentials/google-service-account.json
WEEKLY_GOALS_DOC_ID=your_document_id_here
```

Replace `your_document_id_here` with the actual document ID from Step 3.

## Step 5: Install Dependencies

```bash
cd team-visibility-system
pip install -r requirements.txt
```

## Step 6: Test the Integration

```bash
python test_stage2_5.py
```

This will:
- ✅ Connect to Google Drive
- ✅ Read your weekly goals document
- ✅ Parse the goals
- ✅ Fetch ClickUp tasks
- ✅ Map tasks to goals using tags
- ✅ Show progress toward each goal

## Troubleshooting

### Error: "Failed to authenticate with Google Drive"
- Check that `GDRIVE_CREDENTIALS_PATH` points to the correct JSON file
- Verify the JSON file is valid (try opening it in a text editor)

### Error: "Failed to read document"
- Make sure you shared the document with the service account email
- Verify the document ID is correct
- Check that the service account has at least "Viewer" permission

### Error: "No goals found"
- Check your Google Doc follows the format in the example
- Make sure sections are titled: "WEEKLY GOALS", "DELIVERABLES", "RISKS & BLOCKERS"

### No tasks mapped to goals
- Verify your ClickUp tasks have tags like `team-visibility`, `stage-1`, etc.
- Check that the goal text mentions these tags (e.g., "Stage 1" in the goal title)
- Add tags to your ClickUp tasks if missing

## What's Next?

Once Stage 2.5 tests pass, you're ready for **Stage 3: AI Summarization**!
