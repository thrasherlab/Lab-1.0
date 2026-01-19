# Gmail API Setup Instructions

To use the PE Deal Tracker, you need to set up Gmail API access. Follow these steps:

## 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project name/ID

## 2. Enable Gmail API

1. In the Google Cloud Console, go to **APIs & Services > Library**
2. Search for "Gmail API"
3. Click on it and press **Enable**

## 3. Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External** (unless you have a Google Workspace)
   - App name: PE Deal Tracker
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: You can skip this for now
   - Test users: Add your Gmail address
   - Click **Save and Continue** through the remaining steps

4. Back at Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: PE Deal Tracker
   - Click **Create**

5. Download the JSON file (it will be named something like `client_secret_XXX.json`)

## 4. Set Up Credentials

1. Rename the downloaded file to `credentials.json`
2. Move it to the root of your PE Deal Tracker project directory
3. The file should be at: `/path/to/Lab-1.0/credentials.json`

## 5. First-Time Authentication

When you run the tracker for the first time:

```bash
python src/main.py fetch --days 7
```

1. A browser window will open
2. Sign in with your Gmail account
3. Grant the requested permissions (read-only access to Gmail)
4. The app will save a `token.json` file for future use

## Security Notes

- **credentials.json** and **token.json** contain sensitive information
- They are already in `.gitignore` and won't be committed to git
- Never share these files publicly
- The app only requests **read-only** access to Gmail

## Troubleshooting

**Error: "Access blocked: This app's request is invalid"**
- Make sure you added yourself as a test user in the OAuth consent screen

**Error: "invalid_grant"**
- Delete `token.json` and re-authenticate

**Error: "Credentials file not found"**
- Make sure `credentials.json` is in the project root directory
