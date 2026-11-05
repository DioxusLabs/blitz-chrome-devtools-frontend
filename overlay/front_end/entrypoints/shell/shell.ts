// Copyright 2018 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// Blitz: a minimal shell that only registers the panels and tools Blitz's CDP
// server supports (upstream also registers Sources, Profiler, Coverage, AI
// assistance, Protocol monitor, ...).
import '../../Images/Images.js';
import '../../ui/dom_extension/dom_extension.js';
import '../../panels/console/console-meta.js';
import '../../panels/settings/settings-meta.js';
import '../main/main-meta.js';
import '../../ui/legacy/components/quick_open/quick_open-meta.js';
import '../../panels/common/common-meta.js';
import '../main/main.js';
