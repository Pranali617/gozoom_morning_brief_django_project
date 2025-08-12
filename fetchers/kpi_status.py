import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import gspread
from datetime import datetime
from app.models import MorningBrief


class KpiStatus:
    def __init__(self):
        self.option = {}
        self.dataframe = None
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(self.base_dir, "config", "config.json")
        self.creds_path = os.path.join(self.base_dir, "credentials", "credentials.json")
        self.output_path = os.path.join(self.base_dir, "output", "output_details.txt")
        self.setup_logging()

    def setup_logging(self):
        log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_dir, "kpiStatus.log"),
            filemode='a',
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger()

    def load_config(self):
        self.logger.info("Reading config file")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as fp:
                    self.option = json.load(fp)
            except Exception as e:
                self.logger.error("Cannot read config json file: " + str(e))
                sys.exit(-1)
        else:
            self.logger.error("Config file not present, aborting execution")
            sys.exit(-1)

    def get_passed_time(self, deadline):
        today = datetime.today().date()
        if not deadline:
            return ""
        if isinstance(deadline, datetime):
            deadline = deadline.date()
        passed_days = (today - deadline).days
        if passed_days > 0:
            return f"{passed_days}d"
        elif passed_days == 0:
            return "Due today"
        else:
            return f"{abs(passed_days)}d"

    def generate_tasks(self, sheet_type):
        self.logger.info("Reading Spreadsheet")
        all_tasks = []
        try:
            gc = gspread.service_account(self.creds_path)
            spreadsheet_ids = self.option['status_spreadsheet_id'].split(',')

            for spreadsheet_id in spreadsheet_ids:
                spreadsheet = gc.open_by_key(spreadsheet_id)
                sheet_instance = spreadsheet.get_worksheet(0)
                records_data = sheet_instance.get_all_records()
                self.dataframe = pd.DataFrame.from_dict(records_data)
                worksheets = spreadsheet.worksheets()
                properties = spreadsheet.fetch_sheet_metadata()
                filter_views = properties.get('sheets', [{}])[0].get('filterViews', [])
                main_sheet_name = spreadsheet.title

                status_gid = None
                for worksheet in worksheets:
                    if worksheet.title == 'Status':
                        status_gid = worksheet.id
                        break
                if status_gid is None:
                    self.logger.error("Status worksheet not found")
                    continue

                df = self.dataframe
                df["EID"] = str(status_gid) + "_" + df["ID"].astype(str)
                df['Actual'] = df['Actual'].str.rstrip("%").replace('', np.nan).astype(float)
                df['Expected Now'] = df['Expected Now'].str.rstrip("%").replace('', np.nan).astype(float)
                df['Deadline'] = df['Deadline'].replace('', np.nan)
                df['Deadline'] = df['Deadline'].str.split('-').str[0].apply(lambda x: str(x) if isinstance(x, float) else x)
                df['Deadline'] = [datetime.strptime(i, '%Y%m%d').date() if (isinstance(i, str) and i != 'nan') else None for i in df['Deadline']]

                ppl_filter_links = {}
                ppl = ['TY', 'SW', 'TH', 'WY', 'SL', 'ST', 'MM']

                for _, row in df.iterrows():
                    if row['Deadline'] is None:
                        continue
                    if pd.isna(row["Who"]) or pd.isna(row["Doc By"]):
                        continue
                    if row["Who"] in ppl and row["Doc By"] in ppl:
                        if row['Who'] == row['Doc By'] and pd.notnull(row['Actual']):
                            filter_name = f"{row['Who']}: {row['Doc By']} Reviews"
                        elif row['Doc Type'] == "Score Wts":
                            filter_name = f"{row['Who']}: {row['Who']} Reviews"
                        else:
                            continue
                        for fv in filter_views:
                            if fv.get('title') == filter_name:
                                fv_id = fv.get('filterViewId')
                                link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={fv.get('range', {}).get('sheetId', status_gid)}&fvid={fv_id}"
                                if row['Who'] not in ppl_filter_links:
                                    ppl_filter_links[row["Who"]] = link
                                break

                for _, row in df.iterrows():
                    if row['Deadline'] is None or pd.isna(row["Who"]) or pd.isna(row["Doc By"]):
                        continue
                    if pd.isna(row["Actual"]) or pd.isna(row["Expected Now"]):
                        continue
                    if float(row["Actual"]) >= 85:
                        continue
                    try:
                        expected_score = float(row["Expected Now"])
                        actual_score = float(row["Actual"])
                    except Exception as e:
                        self.logger.warning(f"Invalid score data for ID {row.get('ID', 'unknown')}: {e}")
                        continue
                    if actual_score >= expected_score:
                        continue

                    link = ppl_filter_links.get(row['Who'], f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={status_gid}")
                    sheet_name = " ".join(row['URL'].split()[-2:]) if 'URL' in row and isinstance(row['URL'], str) and row['URL'].strip() else main_sheet_name
                    days_passed = self.get_passed_time(row['Deadline'])

                    if row['Who'] != row['Doc By']:
                        if actual_score == 2.0:
                            trigger = f"{row['Who']} missed to score KPI {row['Task']}"
                            desc = f"{row['Who']} missed to Review and Set Score of {row['Doc By']} {sheet_name} to 85%"
                        else:
                            trigger = f"{row['Doc By']} did not set score to 2% for {row['Task']}"
                            desc = f"Please set Actual score to 2% for task {row['Task']} in {sheet_name} so {row['Who']} can review it"
                        task_data = {
                            "title": trigger,
                            "link": link,
                            "image": "",
                            "summary": desc,
                            "category": "Review",
                            "like": 0,
                            "dislike": 0,
                            "hours": days_passed,
                            "source": sheet_name,
                            "original_source": spreadsheet_id,
                            "original_link": link,
                            "owner": row['Who']
                        }
                        # ❌ Skip if owner is 'TH' or Deadline is older than 80 days
                        if row['Who'] == 'TH':
                            continue
                        if row['Deadline'] and (datetime.today().date() - row['Deadline']).days > 80:
                            continue

                        all_tasks.append(task_data)


                    if row['Doc By'] == 'TY' and row['Who'] != 'TY':
                        trigger = f"Info {sheet_name} Status {row['Who']} missed to score KPI for TY"
                        desc = f"{row['Who']} missed to Review and Set Score of TY {sheet_name} to 85%"
                        task_data = {
                            "title": trigger,
                            "link": link,
                            "image": "",
                            "summary": desc,
                            "category": "Review",
                            "like": 0,
                            "dislike": 0,
                            "hours": days_passed,
                            "source": sheet_name,
                            "original_source": spreadsheet_id,
                            "original_link": link,
                            "owner": row['Who']
                        }
                        # ❌ Skip if owner is 'TH' or Deadline is older than 80 days
                        if row['Who'] == 'TH':
                            continue
                        if row['Deadline'] and (datetime.today().date() - row['Deadline']).days > 80:
                            continue

                        all_tasks.append(task_data)
        

        except Exception as e:
            self.logger.error("Error while reading the spreadsheet: " + str(e))

        return all_tasks
