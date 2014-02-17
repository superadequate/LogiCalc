"""
Import a csv file containing loan data into the db.
"""
import csv
from lc_calc.models import LoanCompany, LoanType, LoanAdditionLookupValueType, LoanAdditionLookup


class LoanDataImporter(object):
    value_keys = ['vi{0}'.format(i) for i in range(1, 11)]
    value_indices = None

    @staticmethod
    def get_or_create(model_class, **kwargs):
        try:
            return model_class.objects.get(**kwargs)
        except model_class.DoesNotExist:
            obj = model_class(**kwargs)
            obj.save()
            return obj

    def import_file(self, csv_file):
        for row in csv.DictReader(csv_file):
            if row['Type'] == 'value_index':
                # Set the reference data and current indices
                self.loan_company = self.get_or_create(LoanCompany, title=row['LoanCompany_title'])
                self.loan_type = self.get_or_create(LoanType, name=row['LoanType_name'])
                self.value_type = self.get_or_create(LoanAdditionLookupValueType, name=row['LoanAdditionLookupValueType'])
                self.value_indices = [(k, int(row[k])) for k in self.value_keys]

                # Delete old values
                for vo in LoanAdditionLookup.objects.filter(loan_company=self.loan_company,
                                                            loan_type=self.loan_type,
                                                            value_type=self.value_type,):
                    vo.delete()
            elif row['Type'] == 'values':

                # Add the new values
                for (value_index_key, value_index) in self.value_indices:
                    loan_lookup_value = LoanAdditionLookup(
                        loan_company=self.loan_company,
                        loan_type=self.loan_type,
                        value_type=self.value_type,
                        credit_score=int(row['credit_score']),
                        value_index=value_index,
                        value=float(row[value_index_key]))
                    loan_lookup_value.save()
            else:
                import IPython; IPython.embed()


def process_command_line(importer_class):
    """
    Process the command line, passing the csv files and parameters to the importer_class
    """
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Import any asset CSV file into adaptwater from the command line.",
                                     epilog="Trying a dry run first is highly recommended")
    parser.add_argument('csv_file_or_folder', help='the csv file or folder of files to be imported')
    args = parser.parse_args()

    def is_csv(fname):
        return os.path.splitext(fname)[1].lower() == '.csv'

    # Get the csv filenames
    if os.path.isdir(args.csv_file_or_folder):
        folder = args.csv_file_or_folder
        csv_filenames = [os.path.join(folder, fname) for fname in os.listdir(folder)
                         if is_csv(fname)]
    elif os.path.isfile(args.csv_file_or_folder) and is_csv(args.csv_file_or_folder):
        csv_filenames = [args.csv_file_or_folder]
    else:
        print('csv_file_or_folder must be a csv file or a folder containing csv files')
        csv_filenames = []

    # import each csv file
    importer = importer_class()
    for csv_filename in csv_filenames:
        with open(csv_filename, 'rt') as csv_file:
            importer.import_file(csv_file)

if __name__ == "__main__":
    process_command_line(LoanDataImporter)