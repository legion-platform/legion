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

export const infoHolder = style({
  textAlign: 'left',
  padding: '2px 2px 2px 2px'
});

export const infoList = style({
  listStyleType: 'none',
  paddingInlineStart: '12px'
});

export const infoTitle = style({
  color: 'var(--jp-ui-font-color1)',
  display: 'inline-block',
  fontSize: 'var(--jp-ui-font-size0)',
  fontWeight: 600,
  letterSpacing: 1,
  textTransform: 'uppercase',
  margin: 0,
  marginBottom: 5
});

export const infoPairLine = style({
  margin: 0,
  marginBottom: 3,
  color: 'var(--jp-ui-font-color1)',
  fontSize: 'var(--jp-ui-font-size0)'
});

export const infoPairTitle = style({
  fontWeight: 600,
  display: 'inline-block',
  marginRight: 10
});
