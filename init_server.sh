echo "开始初始化博客系统..."

if [ -f "requirements.txt" ]; then
    echo "Installing/updating dependencies..."
    pip install -r requirements.txt
fi

echo "Synchronizing database structure..."
python manage.py makemigrations
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Initializing user groups (Administrators, Users, Guests)..."
python manage.py setup_groups

echo "------------------------------------------------"
echo "✅ Initialization complete! You can run the service now."
echo "------------------------------------------------"