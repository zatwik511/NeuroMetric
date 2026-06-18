from app import create_app

# create_app() creates tables and auto-seeds the database when it's empty
# (see app/seed.py), so both local dev and the deployed app share one path.
app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
