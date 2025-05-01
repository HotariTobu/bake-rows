/**
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/* eslint-disable @typescript-eslint/no-unused-vars */

const onOpen = (_: GoogleAppsScript.Events.SheetsOnOpen) => {
  SpreadsheetApp.getUi()
    .createMenu('BAKE ROWS')
    .addItem('サイドバーを開く', '__showSidebar__')
    .addToUi();
};

const __showSidebar__ = () => {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();

  const template = HtmlService.createTemplateFromFile('page');
  template.sheetId = sheet.getSheetId();
  template.columnsJSON = JSON.stringify(__extractColumns__(sheet));
  const html = template.evaluate().setTitle('BAKE ROWS');

  const ui = SpreadsheetApp.getUi();
  ui.showSidebar(html);
};

const __extractColumns__ = (sheet: GoogleAppsScript.Spreadsheet.Sheet) => {
  const headerRange = sheet.getRange('1:1');
  const headerValues = headerRange.getValues();
  const headers = headerValues[0];
  const columns: [number, string][] = [];

  for (let i = 0; i < headers.length; i++) {
    const header = headers[i];
    if (header) {
      columns.push([i + 1, header]); // Store column index (1-based)
    }
  }
  return columns;
};

const getColumnValuesRecord = (
  sheetId: GoogleAppsScript.Integer,
  columnIndexRecord: Record<string, GoogleAppsScript.Integer>
) => {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetById(sheetId);
  if (sheet === null) {
    throw new Error(`Not found: sheet ${sheetId}`);
  }

  const columnValuesRecord: Record<string, unknown[]> = {};

  for (const name of Object.keys(columnIndexRecord)) {
    const columnIndex = columnIndexRecord[name];
    const columnValues = __getColumnValues__(sheet, columnIndex);
    columnValuesRecord[name] = columnValues.map(value => String(value));
  }

  return columnValuesRecord;
};

const __getColumnValues__ = (
  sheet: GoogleAppsScript.Spreadsheet.Sheet,
  columnIndex: GoogleAppsScript.Integer
) => {
  const rowCount = sheet.getMaxRows() - 1;
  const range = sheet.getRange(2, columnIndex, rowCount, 1);
  const columnValues = range.getValues().map(row => row[0]);
  return columnValues;
};

const insertSheet = (columns: Record<string, unknown[]>) => {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.insertSheet();

  sheet.setTabColor('#FF0000');

  const headers = Object.keys(columns);

  const rowCount = columns[headers[0]].length;
  const columnCount = headers.length;

  const headerRange = sheet.getRange(1, 1, 1, columnCount);
  headerRange.setValues([headers]);

  const values: unknown[][] = [];

  for (let i = 0; i < rowCount; i++) {
    const row = headers.map(header => columns[header][i]);
    values.push(row);
  }

  const range = sheet.getRange(2, 1, rowCount, headers.length);
  range.setValues(values);

  sheet.setFrozenRows(1);
};
