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

export const normalButtonStyle = style({
  cursor: 'pointer'
});

export const smallButtonStyle = style({
  background: 'var(--jp-layout-color1)',
  border: 'none',
  boxSizing: 'border-box',
  outline: 'none',
  appearance: 'none',
  padding: '0px 16px',
  margin: '0px',
  height: '24px',
  borderRadius: 'var(--jp-border-radius)',
  cursor: 'pointer',
  $nest: {
    '&:hover': {
      background: 'var(--jp-layout-color2)'
    }
  }
});

export const smallButtonStyleImage = style({
  padding: '0px',
  flex: '0 0 auto'
});

export const branchStyle = style({
  zIndex: 1,
  textAlign: 'center',
  overflowY: 'auto'
});

export const buttonDisabled = style({
  cursor: 'wait',
  opacity: 0.4
});
