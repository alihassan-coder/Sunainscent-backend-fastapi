# Sunainscent E-commerce Platform

A full-stack e-commerce platform built with FastAPI (backend) and Next.js (frontend), featuring JWT authentication, MongoDB Atlas integration, and a beautiful responsive design.

## Features

### Backend (FastAPI)
- ✅ JWT-based authentication system
- ✅ User registration and login with email, password, first name, and phone
- ✅ Password hashing with bcrypt
- ✅ MongoDB Atlas integration
- ✅ Product CRUD operations
- ✅ Protected routes with authentication middleware
- ✅ RESTful API design
- ✅ Request validation with Pydantic
- ✅ CORS configuration for frontend integration

### Frontend (Next.js)
- ✅ Beautiful responsive design with Tailwind CSS
- ✅ Hero section with gradient backgrounds
- ✅ Authentication context with React Context API
- ✅ Login and registration forms with validation
- ✅ Product listing page with search and filtering
- ✅ Dynamic product rendering from API
- ✅ Protected routing system
- ✅ Mobile-responsive navigation
- ✅ Loading states and error handling
- ✅ Cookie-based token storage

## Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for Python
- **MongoDB Atlas** - Cloud database service
- **Motor** - Async MongoDB driver
- **JWT** - JSON Web Tokens for authentication
- **Passlib** - Password hashing
- **Pydantic** - Data validation and serialization
- **Python-JOSE** - JWT handling
- **Uvicorn** - ASGI server

### Frontend
- **Next.js 15** - React framework
- **React 19** - UI library
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client
- **js-cookie** - Cookie handling
- **React Context** - State management

## Project Structure

```
Sunainscent/
├── Sunainscent-backend-fastapi/
│   ├── config/
│   │   ├── database.py          # MongoDB connection
│   │   └── settings.py          # App configuration
│   ├── routes/
│   │   ├── auth.py              # Authentication routes
│   │   └── products.py          # Product management routes
│   ├── utils/
│   │   └── auth.py              # Authentication utilities
│   ├── validation/
│   │   ├── user_models.py       # User data models
│   │   └── product_models.py    # Product data models
│   ├── main.py                  # FastAPI application
│   ├── .env                     # Environment variables
│   └── pyproject.toml           # Dependencies
│
└── Sunainscent-frountend-nextjs/
    ├── src/
    │   ├── app/
    │   │   ├── auth/
    │   │   │   ├── login/page.js    # Login page
    │   │   │   └── register/page.js # Registration page
    │   │   ├── shop/page.js         # Shop/products page
    │   │   ├── layout.js            # Root layout
    │   │   ├── page.js              # Landing page
    │   │   └── globals.css          # Global styles
    │   ├── components/
    │   │   ├── Navigation.js        # Navigation component
    │   │   └── ProtectedRoute.js    # Route protection
    │   ├── contexts/
    │   │   └── AuthContext.js       # Authentication context
    │   └── lib/
    │       └── api.js               # API client configuration
    ├── package.json
    └── .env.local                   # Environment variables
```

## Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+
- MongoDB Atlas account

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd Sunainscent-backend-fastapi
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\\Scripts\\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```
   Or if you prefer uv:
   ```bash
   uv sync
   ```

4. **Configure environment variables:**
   - Update `.env` file with your MongoDB Atlas connection string
   - Replace the placeholder values:
   ```env
   MONGODB_URL=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/sunainscent?retryWrites=true&w=majority
   JWT_SECRET_KEY=your_super_secret_jwt_key_here_change_this_in_production
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_TIME=1440
   API_V1_STR=/api/v1
   ```

5. **Run the backend server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd Sunainscent-frountend-nextjs
   ```

2. **Install dependencies:**
   ```bash
   pnpm install
   # or
   npm install
   ```

3. **Configure environment variables:**
   - The `.env.local` file is already configured for local development
   - For production, update the API URL accordingly

4. **Run the development server:**
   ```bash
   pnpm dev
   # or
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user profile
- `GET /api/v1/auth/verify-token` - Verify JWT token

### Products
- `GET /api/v1/products` - Get all products (with pagination, search, filter)
- `GET /api/v1/products/{id}` - Get specific product
- `POST /api/v1/products` - Create product (requires auth)
- `PUT /api/v1/products/{id}` - Update product (requires auth)
- `DELETE /api/v1/products/{id}` - Delete product (requires auth)
- `GET /api/v1/products/categories/list` - Get all categories

## Usage

1. **Start both servers** (backend on port 8000, frontend on port 3000)

2. **Create an account** by visiting `http://localhost:3000/auth/register`

3. **Add some products** using the API endpoints (requires authentication)

4. **Browse products** on the shop page or landing page

5. **Test the authentication** by logging in and out

## MongoDB Atlas Setup

1. Create a MongoDB Atlas account at https://www.mongodb.com/atlas
2. Create a new cluster
3. Create a database user
4. Configure network access (add your IP or use 0.0.0.0/0 for development)
5. Get your connection string and update the `.env` file

## Environment Variables

### Backend (.env)
```env
MONGODB_URL=your_mongodb_atlas_connection_string
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_TIME=1440
API_V1_STR=/api/v1
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Development Tips

1. **Adding Products**: Use tools like Postman or curl to add initial products via the API
2. **Database Inspection**: Use MongoDB Compass to view your database
3. **API Testing**: FastAPI provides interactive documentation at `/docs`
4. **Debugging**: Check browser console and terminal logs for errors

## Production Deployment

### Backend
- Deploy on platforms like Railway, Heroku, or DigitalOcean
- Update CORS origins for your domain
- Use environment variables for sensitive data
- Consider using a proper ASGI server like Gunicorn with Uvicorn workers

### Frontend
- Deploy on Vercel, Netlify, or similar platforms
- Update `NEXT_PUBLIC_API_URL` to your production API URL
- Ensure proper environment variable configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

If you encounter any issues or have questions, please check the API documentation at `http://localhost:8000/docs` or create an issue in the repository.

---

**Happy coding! 🚀**