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

export const holder = style({
  display: 'flex',
  flexDirection: 'row',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: 'var(--jp-toolbar-header-margin)'
});

export const text = style({
  display: 'inline-block',
  color: 'var(--jp-ui-font-color1)',
  flex: '0 0 auto',
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '1px',
  fontSize: 'var(--jp-ui-font-size0)',
  padding: '8px 8px 8px 12px',
  margin: '0px'
});

export const refreshAnimated = style({
  '-webkit-animation': 'legion-loading-rotate-center 1s linear infinite both',
  animation: 'legion-loading-rotate-center 1s linear infinite both',
  minWidth: 16,
  minHeight: 16,
  backgroundSize: 16,
  backgroundImage: 'var(--jp-icon-refresh)'
});
