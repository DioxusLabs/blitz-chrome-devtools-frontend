// Copyright 2018 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// Blitz: only register the panels Blitz's CDP server supports (upstream also
// registers Application, Performance, Lighthouse, Sensors, ...).
import '../shell/shell.js';
import '../../panels/elements/elements-meta.js';
import '../../panels/network/network-meta.js';
import '../../panels/mobile_throttling/mobile_throttling-meta.js';
import '../inspector_main/inspector_main-meta.js';

import * as Root from '../../core/root/root.js';
import * as Main from '../main/main.js';

// @ts-expect-error Exposed for legacy layout tests
self.runtime = Root.Runtime.Runtime.instance({forceNew: true});
new Main.MainImpl.MainImpl({supportsEmulation: false});
