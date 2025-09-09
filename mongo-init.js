// MongoDB initialization script
db = db.getSiblingDB('document_service');

// Create collections
db.createCollection('documents');
db.createCollection('users');

// Create indexes for better performance
db.documents.createIndex({ "filename": 1 });
db.documents.createIndex({ "upload_date": -1 });
db.documents.createIndex({ "user_id": 1 });
db.documents.createIndex({ "file_type": 1 });

db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });

// Insert sample data (optional)
db.users.insertOne({
    username: "admin",
    email: "admin@example.com",
    created_at: new Date(),
    is_active: true
});

print("MongoDB initialization completed successfully!");