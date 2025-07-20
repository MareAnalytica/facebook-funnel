# Facebook Funnel with ScoreApp Integration

A simple web funnel that collects Facebook profile data and integrates with ScoreApp quizzes.

## Features

- Facebook Login integration (profile + likes)
- ScoreApp webhook endpoint
- PostgreSQL database (Supabase)
- Clean, responsive UI with Tailwind CSS
- Error handling and logging

## Setup Instructions

### 1. Set up Supabase Database

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Go to Settings > Database to get your connection details
4. Copy the connection string details

### 2. Configure Environment Variables

1. Copy `env.example` to `.env`
2. Fill in your Supabase database credentials:
   ```
   DB_HOST=your-project-ref.supabase.co
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=your-database-password
   DB_PORT=5432
   ```

### 3. Set up Facebook App

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create a new app
3. Add Facebook Login product
4. Get your App ID
5. Update the `appId` in `templates/index.html`

### 4. Update URLs

In `templates/index.html`, replace:
- `YOUR_FACEBOOK_APP_ID` with your actual Facebook App ID
- `YOUR_SCOREAPP_URL` with your ScoreApp quiz URL

### 5. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 6. Run Locally

```bash
# Make sure virtual environment is activated
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Run the application
python app.py
```

Visit `http://localhost:5000` to test.

## Deployment

### Deploy to Render.com

1. Push your code to GitHub
2. Go to [render.com](https://render.com) and create account
3. Create new Web Service
4. Connect your GitHub repo
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `python app.py`
7. Add environment variables from your `.env` file
8. Deploy!

### Deploy to Railway

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) and create account
3. Create new project from GitHub repo
4. Add environment variables
5. Deploy!

## How Data Linking Works

The app links Facebook data with ScoreApp quiz results using ScoreApp's query parameter system:

1. **Facebook Login**: User logs in and we save their Facebook ID to the database
2. **Redirect to ScoreApp**: User is redirected with Facebook data as URL parameters:
   ```
   YOUR_SCOREAPP_URL?facebook_id=123456789&email=user@example.com&first_name=John&last_name=Smith
   ```
3. **ScoreApp Pre-fills Form**: ScoreApp automatically pre-fills the form fields with the URL parameters
4. **User Completes Quiz**: User completes the quiz (form fields are already filled)
5. **Webhook Processing**: ScoreApp sends quiz results including the `facebook_id` field
6. **Data Matching**: The app matches the `facebook_id` from ScoreApp with the `facebook_id` in the database

### ScoreApp Configuration Required

1. **Add Custom Field**: In your ScoreApp quiz, add a custom field with the key `facebook_id`
2. **Set Webhook URL**: Configure ScoreApp to send webhooks to: `https://your-app.onrender.com/webhooks/scoreapp`
3. **Optional**: Add `email`, `first_name`, `last_name` fields to pre-fill user data

The `facebook_id` field will be automatically included in the webhook payload when users complete the quiz.

## API Endpoints

### POST /api/facebook-data
Receives Facebook profile and likes data.

**Request Body:**
```json
{
  "id": "facebook_user_id",
  "name": "User Name",
  "email": "user@example.com",
  "likes": [...]
}
```

### POST /webhooks/scoreapp
Receives ScoreApp completion data.

**Request Body:** (varies based on ScoreApp configuration)

## Database Schema

```sql
CREATE TABLE user_responses (
    id SERIAL PRIMARY KEY,
    facebook_id VARCHAR(255),
    facebook_name VARCHAR(255),
    facebook_email VARCHAR(255),
    facebook_likes JSONB,
    scoreapp_data JSONB,
    scoreapp_quiz_id VARCHAR(255),
    scoreapp_result_url TEXT,
    scoreapp_finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Data Storage

- **Facebook Data**: Stored when user logs in with Facebook
- **ScoreApp Data**: Stored when user completes quiz (QUIZ_FINISHED) or signs up (LEAD_SIGNED_UP)
- **Each quiz completion**: Creates a new record (no updates)
- **Linking**: Facebook ID connects Facebook data with ScoreApp responses

## Troubleshooting

### Facebook Login Issues
- Ensure your Facebook App is configured correctly
- Check that your domain is added to allowed domains
- Verify App ID is correct

### Database Connection Issues
- Check Supabase credentials
- Ensure database is accessible from your deployment platform
- Verify environment variables are set correctly

### ScoreApp Webhook Issues
- Check webhook URL is correct in ScoreApp settings
- Verify the endpoint accepts POST requests
- Check logs for detailed error messages

## Security Notes

- Never commit `.env` file to version control
- Use HTTPS in production
- Consider rate limiting for webhook endpoints
- Validate all incoming data

## Support

For issues or questions, check the logs in your deployment platform's dashboard. 