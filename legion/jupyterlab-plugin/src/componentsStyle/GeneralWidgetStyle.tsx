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

export const widgetPane = style({
  background: 'var(--jp-layout-color0)',
  height: '100%'
});

/**
 * Authorization
 */
export const authSubPane = style({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%'
});

export const authIcon = style({
  backgroundImage: 'var(--jp-icon-legion-lock)',
  width: 80,
  height: 80,
  backgroundSize: 80,
  backgroundRepeat: 'no-repeat',
  backgroundPosition: 'center'
});

export const authDisclaimerText = style({
  color: 'var(--jp-ui-font-color1)',
  display: 'block',
  fontSize: 'var(--jp-ui-font-size2)',
  margin: '20px 0',
  textAlign: 'center'
});

export const cloudModeTabStyle = style({
  backgroundImage: 'var(--jp-icon-legion-cloud)'
});

/**
 * Stripper line
 */
export const stripperLine = style({
  width: '100%',
  backgroundImage:
    'repeating-linear-gradient(-45deg, #dbd52c, #dbd52c 1rem, #000000 1rem, #000000 2rem)',
  backgroundSize: '200% 200%',
  animation: 'legion-stripe-animation 10s linear infinite',
  textAlign: 'center',
  color: '#fff',
  fontSize: 'var(--jp-ui-font-size1)',
  fontWeight: 'bold',
  padding: '4px 10px'
});

export const generalWidgetCentered = style({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center'
});

export const noDataLine = style({
  color: 'var(--jp-ui-font-color1)',
  fontSize: 'var(--jp-ui-font-size2)',
  textAlign: 'center'
});

/**
 * Cloud training
 */
export const cloudTrainingLogWidget = style({
  overflow: 'auto',
  padding: 'var(--jp-code-padding)'
});

export const cloudTrainingLogWidgetText = style({
  textAlign: 'left',
  whiteSpace: 'pre',
  color: 'var(--jp-ui-font-color1)',
  fontFamily: 'var(--jp-code-font-family)',
  fontSize: 'var(--jp-code-font-size)',
  lineHeight: 'var(--jp-private-completer-item-height)'
});

export const cloudTrainingLogWidgetIcon = style({
  backgroundImage: 'var(--jp-icon-refresh)',
  '-webkit-animation': 'legion-loading-rotate-center 1s linear infinite both',
  animation: 'legion-loading-rotate-center 1s linear infinite both',
  minWidth: 16,
  minHeight: 16,
  backgroundSize: 16,
  backgroundPosition: 'center center'
});
