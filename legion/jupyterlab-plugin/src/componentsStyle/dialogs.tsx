/**
 *   Copyright 2019 EPAM Systems
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */
import { style } from 'typestyle';

export const fieldLabelStyle = style({
  color: 'var(--jp-ui-font-color1)',
  display: 'block',
  fontSize: 'var(--jp-ui-font-size2)',
  marginBottom: 5
});

export const fieldTextStyle = style({
  margin: 0
});

export const ulStyle = style({});

export const ulItemStyle = style({});

export const inputFieldStyle = style({
  borderWidth: 1,
  borderColor: 'var(--jp-ui-font-color1)',
  backgroundColor: 'var(--jp-layout-color0)',
  width: '100%',
  resize: 'none'
});

export const dialogLine = style({
  marginBottom: 8
});

export const dialogInputLabel = style({
  marginBottom: 3,
  fontWeight: 600,
  textTransform: 'uppercase',
  fontSize: 'var(--jp-ui-font-size0)'
});
