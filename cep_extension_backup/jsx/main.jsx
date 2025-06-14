/**************************************************************************************************
  * ADOBE SYSTEMS INCORPORATED
  * Copyright 2015 Adobe Systems Incorporated
  * All Rights Reserved.
  *
  * NOTICE:  Adobe permits you to use, modify, and distribute this file in accordance with the
  * terms of the Adobe license agreement accompanying it.  If you have received this file from a
  * source other than Adobe, then your use, modification, or distribution of it requires the prior
  * written permission of Adobe.
  *************************************************************************************************/

  var extensionPath = $.fileName.split('/').slice(0, -1).join('/') + '/';
  $.evalFile(extensionPath + 'util.jsx');

  function getMessageFromMain() {
      return 'this is the message from getMessageFromMain';
  }

  var objMain = {};
  objMain.getMessage = function() {
      return 'this is the message from objMain.getMessage';
  }