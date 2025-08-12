
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gozoom_morning_brief.settings')
django.setup()

from fetchers.kpi_status import KpiStatus
from db.task_inserter import insert_tasks
from template_renderer import render_html_for_user

def main():
    print("🔄 Loading KPI Status...")
    kpi = KpiStatus()
    kpi.load_config()


    print("📥 Generating tasks...")  
    tasks = kpi.generate_tasks(sheet_type="status")  

    if tasks:  
        print(f"📝 Generated {len(tasks)} tasks. Inserting into DB...")  
        insert_tasks(tasks)  

        print("🧩 Rendering templates for each user...")  
        users = ['TY', 'SW', 'SL', 'ST', 'WY', 'MM']  
        for user in users:  
            user_tasks = [task for task in tasks if task.get('owner') == user]  
            if user_tasks:  
                try:  
                    render_html_for_user(user, user_tasks)  
                    print(f"✅ Rendered template for {user}")  
                except Exception as e:  
                    print(f"❌ Failed to render template for {user}: {e}")  
            else:  
                print(f"⚠️ No tasks found for {user}, skipping rendering.")  
    else:  
        print("⚠️ No tasks generated.")  
if __name__ == "__main__":
    main()
