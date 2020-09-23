# (c) 2019 The Johns Hopkins University Applied Physics Laboratory LLC (JHU/APL).
# All Rights Reserved. This material may be only be used, modified, or reproduced
# by or for the U.S. Government pursuant to the license rights granted under the
# clauses at DFARS 252.227-7013/7014 or FAR 52.227-14. For any other permission,
# please contact the Office of Technology Transfer at JHU/APL.

# NO WARRANTY, NO LIABILITY. THIS MATERIAL IS PROVIDED "AS IS." JHU/APL MAKES NO
# REPRESENTATION OR WARRANTY WITH RESPECT TO THE PERFORMANCE OF THE MATERIALS,
# INCLUDING THEIR SAFETY, EFFECTIVENESS, OR COMMERCIAL VIABILITY, AND DISCLAIMS
# ALL WARRANTIES IN THE MATERIAL, WHETHER EXPRESS OR IMPLIED, INCLUDING (BUT NOT
# LIMITED TO) ANY AND ALL IMPLIED WARRANTIES OF PERFORMANCE, MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT OF INTELLECTUAL PROPERTY
# OR OTHER THIRD PARTY RIGHTS. ANY USER OF THE MATERIAL ASSUMES THE ENTIRE RISK
# AND LIABILITY FOR USING THE MATERIAL. IN NO EVENT SHALL JHU/APL BE LIABLE TO ANY
# USER OF THE MATERIAL FOR ANY ACTUAL, INDIRECT, CONSEQUENTIAL, SPECIAL OR OTHER
# DAMAGES ARISING FROM THE USE OF, OR INABILITY TO USE, THE MATERIAL, INCLUDING,
# BUT NOT LIMITED TO, ANY DAMAGES FOR LOST PROFITS.

import os
import re
import csv
import time
import json
from datetime import datetime

def _sanitize_task_name(name):
    return re.sub('[.]', '_', name).lower()


def get_log_foldername(path, format_str="{scenario}-{timestamp}"):
    scenario_name = os.path.basename(os.path.basename(path)).split('.')[0]
    # int(round(time.time() * 1000))
    timestamp = re.sub('[.]', '-', str(time.time()))
    return format_str.format(scenario=scenario_name, timestamp=timestamp)


class TSVLogFile():
    def __init__(self, log_file_name):
        self.log_file_name = log_file_name
        self._initialized = False
        self._tsv_log_file = None
        self._tsv_log = None
        self._fieldnames = None

    def _initialize(self, fieldnames):
        self._fieldnames = self.order_fieldnames(fieldnames)
        if not self._fieldnames:
            raise RuntimeError(
                "Fieldnames not specified for TSV log file {0}".format(self.log_file_name))
        if os.path.exists(self.log_file_name):
            mode, write_header = "a", False
        else:
            (dir_name, filename) = os.path.split(self.log_file_name)
            os.makedirs(dir_name, exist_ok=True)
            mode, write_header = "w", True
        self._tsv_log_file = open(self.log_file_name, mode)
        self._tsv_log = csv.DictWriter(self._tsv_log_file, fieldnames=self._fieldnames,
                                       delimiter='\t', quotechar='"', lineterminator='\n')
        if write_header:
            self._tsv_log.writeheader()
        self._initialized = True

    def add_row(self, record):
        if not self._initialized:
            self._initialize(fieldnames=list(record.keys()))
        self._tsv_log.writerow(record)
        self._tsv_log_file.flush()

    def close(self):
        if self._tsv_log_file and not self._tsv_log_file.closed:
            self._tsv_log_file.close()
            self._initialized = False

    def order_fieldnames(self, fieldnames):
        # default implementation
        return fieldnames


class DataLog(TSVLogFile):
    def __init__(self, output_dir):
        log_file_name = os.path.join(output_dir, "data-log.tsv")
        super().__init__(log_file_name)
        self._standard_fields = None

    def order_fieldnames(self, fieldnames):
        # TODO: should be ordered sets?
        fieldnames_set = set(fieldnames)
        standard_fields_set = set(self._standard_fields)
        if not fieldnames_set.issuperset(standard_fields_set):
            raise RuntimeError("Unexpected field names for data log")
        updated_fields = self._standard_fields
        updated_fields.extend(list(fieldnames_set - standard_fields_set))
        return updated_fields


# hierarchy: block_sequence, sub_task (local to block), task (global across blocks)
class RLDataLog(DataLog):
    def __init__(self, *args):
        super().__init__(*args)
        self._standard_fields = [
            'block_num', 'regime_num', 'exp_num', 'status', 'timestamp'
        ]


class ClassifDataLog(DataLog):
    def __init__(self, *args):
        super().__init__(*args)
        self._standard_fields = [
            'block_num', 'regime_num', 'exp_num', 'timestamp'
        ]


class BlocksLog(TSVLogFile):
    def __init__(self, output_dir):
        log_file_name = os.path.join(output_dir, "block-report.tsv")
        super().__init__(log_file_name)

    def order_fieldnames(self, fieldnames):
        standard_fields = ['block_num', 'regime_num', 'block_type', 'worker', 'task_name', 'params']
        if set(standard_fields) != set(fieldnames):
            print(standard_fields)
            print(fieldnames)
            raise RuntimeError("Unexpected field names for blocks log")
        return standard_fields


class PerformanceLogger():
    def __init__(self, toplevel_dir, column_info=None, scenario_info=None):
        self._toplevel_dir = toplevel_dir

        # TODO: determine what constraints to put on column_info and scenario_info
        # scenario_info is object containing whatever the caller desires
        # column_info is object with key for metric columns
        col_key = 'metrics_columns'
        # default to empty list
        self._column_info = column_info or {col_key: []}
        assert(col_key in self._column_info)
        assert(all(isinstance(s, str) for s in self._column_info[col_key]))
        # coalesce if the scenario_info object is false-y
        self._scenario_info = scenario_info or {}

        self._logging_dir = None
        self.data_log = None
        self.blocks_log = None
        self._logging_context = None
        self._data_logger_class = None
        self._blocks_logger_class = None
        # os.makedirs(self._toplevel_dir, exist_ok=True)

    @property
    def logging_dir(self):
        return self._logging_dir

    @property
    def toplevel_dir(self):
        return self._toplevel_dir

    def _check_and_update_context(self, state: dict):
        # keys: worker, phase_filename, task
        new_logging_context = (state['scenario_dirname'], state['worker_dirname'],
                               state['block_dirname'], state['task_dirname'])

        if new_logging_context != self._logging_context:
            self.close_logs()
            assert(self._toplevel_dir is not None)
            self._logging_dir = os.path.join(
                self._toplevel_dir, os.path.sep.join(new_logging_context))
            os.makedirs(self._logging_dir, exist_ok=True)
            self._logging_context = new_logging_context

            scenario_dir = os.path.sep.join((self._toplevel_dir, state['scenario_dirname']))
            column_info_path = os.path.sep.join((scenario_dir, "column_info.json"))
            scenario_info_path = os.path.sep.join((scenario_dir, "scenario_info.json"))
            self._write_info_files(column_info_path, scenario_info_path)
            self.data_log = self._data_logger_class(self._logging_dir)
            self.blocks_log = self._blocks_logger_class(self._logging_dir)

    def _write_info_files(self, column_info_path, scenario_info_path):
        # For now, open the info json files, then create the file (exist already is not ok)
        if not os.path.exists(column_info_path):
            with open(column_info_path, 'w+') as column_file:
                column_file.write(json.dumps(self._column_info, indent=2))
        if not os.path.exists(scenario_info_path):
            with open(scenario_info_path, 'w+') as scenario_file:
                scenario_file.write(json.dumps(self._scenario_info, indent=2))

    def close_logs(self):
        if self.data_log:
            self.data_log.close()
        if self.blocks_log:
            self.blocks_log.close()

    @classmethod
    def get_readable_timestamp(cls):
        return datetime.now().strftime('%Y%m%dT%H%M%S.%f')

    def _get_block_dirname(self, block_num, block_type):
        return f'{block_num}-{block_type}'

    def write_new_regime(self, record: dict, scenario_dirname: str, update_context_only=False):
        # required fields, even before the add_row call
        assert('worker' in record)
        assert('block_num' in record)
        assert('block_type' in record)
        assert('task_name' in record)
        self._check_and_update_context({
            'scenario_dirname': scenario_dirname,
            'worker_dirname': record['worker'],
            'block_dirname': self._get_block_dirname(record['block_num'],
                                                     record['block_type']),
            'task_dirname': record['task_name']
        })
        if not update_context_only:
            self.blocks_log.add_row(record)

    def write_to_data_log(self, record: dict):
        # automating timestamp generation if not provided
        if not 'timestamp' in record:
            record['timestamp'] = PerformanceLogger.get_readable_timestamp()
        self.data_log.add_row(record)


class RLPerformanceLogger(PerformanceLogger):
    def __init__(self, *args):
        super().__init__(*args)
        self._data_logger_class = RLDataLog
        self._blocks_logger_class = BlocksLog


# TODO: determine differences between this and RLPerformanceLogger
class ClassifPerformanceLogger(PerformanceLogger):
    def __init__(self, *args):
        super().__init__(*args)
        self._data_logger_class = ClassifDataLog
        self._blocks_logger_class = BlocksLog
