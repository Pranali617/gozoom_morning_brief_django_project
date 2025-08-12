from app.models import MorningBrief # adjust the import path to your app name

def insert_tasks(task_list):
    inserted = 0
    for task in task_list:
        try:
            # Optional: skip if already exists (adjust logic if needed)
            exists = MorningBrief.objects.filter(
            title=task["title"],
            link=task["link"],
            owner=task["owner"]
            ).exists()
            if exists:
                continue


            MorningBrief.objects.create(
                title=task["title"],
                link=task["link"],
                image=task.get("image", ""),
                summary=task["summary"],
                category=task["category"],
                like=task.get("like", 0),
                dislike=task.get("dislike", 0),
                hours=task["hours"],
                source=task["source"],
                original_source=task["original_source"],
                original_link=task["original_link"],
                owner=task["owner"]
            )
            inserted += 1
        except Exception as e:
            print(f"❌ Error inserting task for {task.get('owner')}: {e}")

        print(f"✅ Inserted {inserted} tasks into DB.")