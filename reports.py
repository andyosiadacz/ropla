import pandas, sqlite3
import datetime

REPORT_TIME = datetime.datetime.today()

def generate_build_today():

    conn = sqlite3.connect('ropla.db')

    df = pandas.read_sql('SELECT * FROM order_detail WHERE buildable = TRUE', conn)

    conn.close()

    report_generated = False

    while not report_generated:
        try:
            df.to_excel(f'NINER BUILDABLE {REPORT_TIME.date()}.xlsx', index=False)
            print(f"NINER BUILDABLE {REPORT_TIME.date()}.xlsx succesfully generated.")

            report_generated = True
        except PermissionError:
            abort = input(f"Permission error. Please close 'NINER BUILDABLE {REPORT_TIME.date()}.xlsx' and hit enter. Input 'x' to abort.").lower()
            if abort == "x":
                report_generated = True
                print("Report generation aborted.")


def generate_OOR():

    conn = sqlite3.connect('ropla.db')

    df = pandas.read_sql('SELECT * FROM order_detail', conn)

    conn.close()

    report_generated = False

    while not report_generated:
        try:
            df.to_excel(f'NINER OOR {REPORT_TIME.date()}.xlsx', index=False)
            print(f"NINER OOR {REPORT_TIME.date()}.xlsx succesfully generated.")
            report_generated = True
        except PermissionError:
            abort = input(f"Permission error. Please close 'NINER OOR {REPORT_TIME.date()}.xlsx' and hit enter. Input 'x' to abort.").lower()
            if abort == "x":
                report_generated = True
                print("Report generation aborted.")
    return df