# Next Steps - Chat Functionality Setup

## ✅ What's Already Done
- Chat functionality implemented with OpenAI integration
- Database model (Chat) created
- API endpoints configured
- Frontend compatibility maintained

## 🚀 Steps to Get Started

### Option 1: Using Docker Compose (Recommended)

1. **Start all services:**
   ```bash
   docker-compose up --build
   ```

2. **The Chat table will be created automatically** when the backend starts (via `Base.metadata.create_all()`)

3. **Access the application:**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Local Development

1. **Set up environment variables** (create `.env` file in backend/):
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
   SECRET_KEY=your-secret-key-here
   OPENAI_API_KEY=your-openai-api-key-here
   S3_ENDPOINT=http://localhost:9000
   S3_ACCESS_KEY=minioadmin
   S3_SECRET_KEY=minioadmin
   S3_BUCKET=ai-stylingapp-demo-bucket
   AWS_ACCESS_KEY_ID=your-aws-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret
   AWS_DEFAULT_REGION=us-east-1
   ```

2. **Start PostgreSQL database:**
   ```bash
   docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15
   ```

3. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run the backend:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **The Chat table will be created automatically** on first run

## 🧪 Testing the Chat Functionality

### 1. Test via API Documentation (Swagger UI)
- Go to: http://localhost:8000/docs
- Navigate to `/api/chat` endpoint
- Click "Authorize" and login first to get a token
- Test the chat endpoint with:
  ```json
  {
    "message": "What hairstyle would suit an oval face?"
  }
  ```

### 2. Test via Frontend
- Make sure you're logged in
- Use the ChatBox component
- It will call `/api/suggestions/prompt` automatically

### 3. Test Chat History
- Use the `/api/chat/history` endpoint to retrieve conversation history
- Returns last 50 messages for the authenticated user

## 📋 Available Chat Endpoints

1. **POST `/api/chat`**
   - Send a chat message
   - Requires authentication
   - Body: `{"message": "your message"}`
   - Returns: `{"response": "AI response"}`

2. **GET `/api/chat/history`**
   - Get chat history
   - Requires authentication
   - Returns: Array of chat messages

3. **POST `/api/suggestions/prompt`** (Frontend compatibility)
   - Same as `/api/chat` but matches frontend expectations
   - Body: `{"prompt": "your message"}`
   - Returns: `{"explanation": "AI response"}`

## 🔍 Verify Everything Works

1. **Check database:**
   ```bash
   # If using Docker
   docker exec -it ai_postgres psql -U postgres -d postgres -c "\d chats"
   ```

2. **Check logs:**
   ```bash
   docker-compose logs backend
   ```

3. **Test authentication:**
   - Register a user at `/api/auth/register`
   - Login at `/api/auth/login`
   - Use the token in Authorization header: `Bearer <token>`

## 🐛 Troubleshooting

### Issue: "No message provided" error
- Make sure you're sending the message in the correct format
- Check that the message field is not empty

### Issue: "Missing authorization header" error
- Make sure you're logged in and have a valid token
- Include the token in the Authorization header: `Bearer <token>`

### Issue: OpenAI API errors
- Verify your `OPENAI_API_KEY` is set correctly
- Check that you have credits in your OpenAI account

### Issue: Database connection errors
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in your environment variables
- Verify database credentials

## 📝 Notes

- The chat functionality uses conversation history (last 10 messages) for context
- All chats are stored in the database
- Authentication is required for all chat endpoints
- The frontend ChatBox component is already configured to work with the new endpoints

## 🎯 Next Enhancements (Optional)

1. Add pagination to chat history endpoint
2. Add ability to delete chat messages
3. Add chat search functionality
4. Add support for file uploads in chat
5. Add typing indicators
6. Add read receipts

