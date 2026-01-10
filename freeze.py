from flask_frozen import Freezer
from app import app
import os

# Configure Freezer
app.config['FREEZER_DESTINATION'] = 'dist_static'
app.config['FREEZER_RELATIVE_URLS'] = True

freezer = Freezer(app)

if __name__ == '__main__':
    # Add _redirects to dist_static after building
    freezer.freeze()
    
    # Manually create _redirects file for Netlify in the output folder
    redirects_path = os.path.join(app.config['FREEZER_DESTINATION'], '_redirects')
    with open(redirects_path, 'w') as f:
        f.write('/*    /index.html   200')
        
    print(f"Static site generated in {app.config['FREEZER_DESTINATION']} folder.")
