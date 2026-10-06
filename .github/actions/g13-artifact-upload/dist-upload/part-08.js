  // Replace standard entities
  for (let entityName in this.lastEntities) {
    const entity = this.lastEntities[entityName];
    val = val.replace(entity.regex, entity.val);
  }
  if (val.indexOf('&') === -1) return val;  // Early exit

  // Replace HTML entities if enabled
  if (this.options.htmlEntities) {
    for (let entityName in this.htmlEntities) {
      const entity = this.htmlEntities[entityName];
      val = val.replace(entity.regex, entity.val);
    }
  }

  // Replace ampersand entity last
  val = val.replace(this.ampEntity.regex, this.ampEntity.val);

  return val;
}


function saveTextToParentTag(textData, parentNode, jPath, isLeafNode) {
  if (textData) { //store previously collected data as textNode
    if (isLeafNode === undefined) isLeafNode = parentNode.child.length === 0

    textData = this.parseTextData(textData,
      parentNode.tagname,
      jPath,
      false,
      parentNode[":@"] ? Object.keys(parentNode[":@"]).length !== 0 : false,
      isLeafNode);

    if (textData !== undefined && textData !== "")
      parentNode.add(this.options.textNodeName, textData);
    textData = "";
  }
  return textData;
}

//TODO: use jPath to simplify the logic
/**
 * @param {Set} stopNodesExact
 * @param {Set} stopNodesWildcard
 * @param {string} jPath
 * @param {string} currentTagName
 */
function isItStopNode(stopNodesExact, stopNodesWildcard, jPath, currentTagName) {
  if (stopNodesWildcard && stopNodesWildcard.has(currentTagName)) return true;
  if (stopNodesExact && stopNodesExact.has(jPath)) return true;
  return false;
}

/**
 * Returns the tag Expression and where it is ending handling single-double quotes situation
 * @param {string} xmlData 
 * @param {number} i starting index
 * @returns 
 */
function tagExpWithClosingIndex(xmlData, i, closingChar = ">") {
  let attrBoundary;
  let tagExp = "";
  for (let index = i; index < xmlData.length; index++) {
    let ch = xmlData[index];
    if (attrBoundary) {
      if (ch === attrBoundary) attrBoundary = "";//reset
    } else if (ch === '"' || ch === "'") {
      attrBoundary = ch;
    } else if (ch === closingChar[0]) {
      if (closingChar[1]) {
        if (xmlData[index + 1] === closingChar[1]) {
          return {
            data: tagExp,
            index: index
          }
        }
      } else {
        return {
          data: tagExp,
          index: index
        }
      }
    } else if (ch === '\t') {
      ch = " "
    }
    tagExp += ch;
  }
}

function findClosingIndex(xmlData, str, i, errMsg) {
  const closingIndex = xmlData.indexOf(str, i);
  if (closingIndex === -1) {
    throw new Error(errMsg)
  } else {
    return closingIndex + str.length - 1;
  }
}

function readTagExp(xmlData, i, removeNSPrefix, closingChar = ">") {
  const result = tagExpWithClosingIndex(xmlData, i + 1, closingChar);
  if (!result) return;
  let tagExp = result.data;
  const closeIndex = result.index;
  const separatorIndex = tagExp.search(/\s/);
  let tagName = tagExp;
  let attrExpPresent = true;
  if (separatorIndex !== -1) {//separate tag name and attributes expression
    tagName = tagExp.substring(0, separatorIndex);
    tagExp = tagExp.substring(separatorIndex + 1).trimStart();
  }

  const rawTagName = tagName;
  if (removeNSPrefix) {
    const colonIndex = tagName.indexOf(":");
    if (colonIndex !== -1) {
      tagName = tagName.substr(colonIndex + 1);
      attrExpPresent = tagName !== result.data.substr(colonIndex + 1);
    }
  }

  return {
    tagName: tagName,
    tagExp: tagExp,
    closeIndex: closeIndex,
    attrExpPresent: attrExpPresent,
    rawTagName: rawTagName,
  }
}
/**
 * find paired tag for a stop node
 * @param {string} xmlData 
 * @param {string} tagName 
 * @param {number} i 
 */
function readStopNodeData(xmlData, tagName, i) {
  const startIndex = i;
  // Starting at 1 since we already have an open tag
  let openTagCount = 1;

  for (; i < xmlData.length; i++) {
    if (xmlData[i] === "<") {
      if (xmlData[i + 1] === "/") {//close tag
        const closeIndex = findClosingIndex(xmlData, ">", i, `${tagName} is not closed`);
        let closeTagName = xmlData.substring(i + 2, closeIndex).trim();
        if (closeTagName === tagName) {
          openTagCount--;
          if (openTagCount === 0) {
            return {
              tagContent: xmlData.substring(startIndex, i),
              i: closeIndex
            }
          }
        }
        i = closeIndex;
      } else if (xmlData[i + 1] === '?') {
        const closeIndex = findClosingIndex(xmlData, "?>", i + 1, "StopNode is not closed.")
        i = closeIndex;
      } else if (xmlData.substr(i + 1, 3) === '!--') {
        const closeIndex = findClosingIndex(xmlData, "-->", i + 3, "StopNode is not closed.")
        i = closeIndex;
      } else if (xmlData.substr(i + 1, 2) === '![') {
        const closeIndex = findClosingIndex(xmlData, "]]>", i, "StopNode is not closed.") - 2;
        i = closeIndex;
      } else {
        const tagData = readTagExp(xmlData, i, '>')

        if (tagData) {
          const openTagName = tagData && tagData.tagName;
          if (openTagName === tagName && tagData.tagExp[tagData.tagExp.length - 1] !== "/") {
            openTagCount++;
          }
          i = tagData.closeIndex;
        }
      }
    }
  }//end for loop
}

function parseValue(val, shouldParse, options) {
  if (shouldParse && typeof val === 'string') {
    //console.log(options)
    const newval = val.trim();
    if (newval === 'true') return true;
    else if (newval === 'false') return false;
    else return toNumber(val, options);
  } else {
    if (isExist(val)) {
      return val;
    } else {
      return '';
    }
  }
}

function fromCodePoint(str, base, prefix) {
  const codePoint = Number.parseInt(str, base);

  if (codePoint >= 0 && codePoint <= 0x10FFFF) {
    return String.fromCodePoint(codePoint);
  } else {
    return prefix + str + ";";
  }
}
;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/xmlparser/node2json.js




const node2json_METADATA_SYMBOL = XmlNode.getMetaDataSymbol();

/**
 * 
 * @param {array} node 
 * @param {any} options 
 * @returns 
 */
function prettify(node, options) {
  return compress(node, options);
}

/**
 * 
 * @param {array} arr 
 * @param {object} options 
 * @param {string} jPath 
 * @returns object
 */
function compress(arr, options, jPath) {
  let text;
  const compressedObj = {}; //This is intended to be a plain object
  for (let i = 0; i < arr.length; i++) {
    const tagObj = arr[i];
    const property = node2json_propName(tagObj);
    let newJpath = "";
    if (jPath === undefined) newJpath = property;
    else newJpath = jPath + "." + property;

    if (property === options.textNodeName) {
      if (text === undefined) text = tagObj[property];
      else text += "" + tagObj[property];
    } else if (property === undefined) {
      continue;
    } else if (tagObj[property]) {

      let val = compress(tagObj[property], options, newJpath);
      const isLeaf = isLeafTag(val, options);

      if (tagObj[":@"]) {
        assignAttributes(val, tagObj[":@"], newJpath, options);
      } else if (Object.keys(val).length === 1 && val[options.textNodeName] !== undefined && !options.alwaysCreateTextNode) {
        val = val[options.textNodeName];
      } else if (Object.keys(val).length === 0) {
        if (options.alwaysCreateTextNode) val[options.textNodeName] = "";
        else val = "";
      }

      if (tagObj[node2json_METADATA_SYMBOL] !== undefined && typeof val === "object" && val !== null) {
        val[node2json_METADATA_SYMBOL] = tagObj[node2json_METADATA_SYMBOL]; // copy over metadata
      }


      if (compressedObj[property] !== undefined && Object.prototype.hasOwnProperty.call(compressedObj, property)) {
        if (!Array.isArray(compressedObj[property])) {
          compressedObj[property] = [compressedObj[property]];
        }
        compressedObj[property].push(val);
      } else {
        //TODO: if a node is not an array, then check if it should be an array
        //also determine if it is a leaf node
        if (options.isArray(property, newJpath, isLeaf)) {
          compressedObj[property] = [val];
        } else {
          compressedObj[property] = val;
        }
      }
    }

  }
  // if(text && text.length > 0) compressedObj[options.textNodeName] = text;
  if (typeof text === "string") {
    if (text.length > 0) compressedObj[options.textNodeName] = text;
  } else if (text !== undefined) compressedObj[options.textNodeName] = text;


  return compressedObj;
}

function node2json_propName(obj) {
  const keys = Object.keys(obj);
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    if (key !== ":@") return key;
  }
}

function assignAttributes(obj, attrMap, jpath, options) {
  if (attrMap) {
    const keys = Object.keys(attrMap);
    const len = keys.length; //don't make it inline
    for (let i = 0; i < len; i++) {
      const atrrName = keys[i];
      if (options.isArray(atrrName, jpath + "." + atrrName, true, true)) {
        obj[atrrName] = [attrMap[atrrName]];
      } else {
        obj[atrrName] = attrMap[atrrName];
      }
    }
  }
}

function isLeafTag(obj, options) {
  const { textNodeName } = options;
  const propCount = Object.keys(obj).length;

  if (propCount === 0) {
    return true;
  }

  if (
    propCount === 1 &&
    (obj[textNodeName] || typeof obj[textNodeName] === "boolean" || obj[textNodeName] === 0)
  ) {
    return true;
  }

  return false;
}

;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/xmlparser/XMLParser.js






class XMLParser {

    constructor(options) {
        this.externalEntities = {};
        this.options = buildOptions(options);

    }
    /**
     * Parse XML dats to JS object 
     * @param {string|Uint8Array} xmlData 
     * @param {boolean|Object} validationOption 
     */
    parse(xmlData, validationOption) {
        if (typeof xmlData !== "string" && xmlData.toString) {
            xmlData = xmlData.toString();
        } else if (typeof xmlData !== "string") {
            throw new Error("XML data is accepted in String or Bytes[] form.")
        }

        if (validationOption) {
            if (validationOption === true) validationOption = {}; //validate with default options

            const result = validate(xmlData, validationOption);
            if (result !== true) {
                throw Error(`${result.err.msg}:${result.err.line}:${result.err.col}`)
            }
        }
        const orderedObjParser = new OrderedObjParser(this.options);
        orderedObjParser.addExternalEntities(this.externalEntities);
        const orderedResult = orderedObjParser.parseXml(xmlData);
        if (this.options.preserveOrder || orderedResult === undefined) return orderedResult;
        else return prettify(orderedResult, this.options);
    }

    /**
     * Add Entity which is not by default supported by this library
     * @param {string} key 
     * @param {string} value 
     */
    addEntity(key, value) {
        if (value.indexOf("&") !== -1) {
            throw new Error("Entity value can't have '&'")
        } else if (key.indexOf("&") !== -1 || key.indexOf(";") !== -1) {
            throw new Error("An entity must be set without '&' and ';'. Eg. use '#xD' for '&#xD;'")
        } else if (value === "&") {
            throw new Error("An entity with value '&' is not permitted");
        } else {
            this.externalEntities[key] = value;
        }
    }

    /**
     * Returns a Symbol that can be used to access the metadata
     * property on a node.
     * 
     * If Symbol is not available in the environment, an ordinary property is used
     * and the name of the property is here returned.
     * 
     * The XMLMetaData property is only present when `captureMetaData`
     * is true in the options.
     */
    static getMetaDataSymbol() {
        return XmlNode.getMetaDataSymbol();
    }
}

;// CONCATENATED MODULE: ./node_modules/@azure/core-xml/dist/esm/xml.common.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Default key used to access the XML attributes.
 */
const xml_common_XML_ATTRKEY = "$";
/**
 * Default key used to access the XML value content.
 */
const xml_common_XML_CHARKEY = "_";
//# sourceMappingURL=xml.common.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-xml/dist/esm/xml.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


function getCommonOptions(options) {
    var _a;
    return {
        attributesGroupName: xml_common_XML_ATTRKEY,
        textNodeName: (_a = options.xmlCharKey) !== null && _a !== void 0 ? _a : xml_common_XML_CHARKEY,
        ignoreAttributes: false,
        suppressBooleanAttributes: false,
    };
}
function getSerializerOptions(options = {}) {
    var _a, _b;
    return Object.assign(Object.assign({}, getCommonOptions(options)), { attributeNamePrefix: "@_", format: true, suppressEmptyNode: true, indentBy: "", rootNodeName: (_a = options.rootName) !== null && _a !== void 0 ? _a : "root", cdataPropName: (_b = options.cdataPropName) !== null && _b !== void 0 ? _b : "__cdata" });
}
function getParserOptions(options = {}) {
    return Object.assign(Object.assign({}, getCommonOptions(options)), { parseAttributeValue: false, parseTagValue: false, attributeNamePrefix: "", stopNodes: options.stopNodes, processEntities: true, trimValues: false });
}
/**
 * Converts given JSON object to XML string
 * @param obj - JSON object to be converted into XML string
 * @param opts - Options that govern the XML building of given JSON object
 * `rootName` indicates the name of the root element in the resulting XML
 */
function stringifyXML(obj, opts = {}) {
    const parserOptions = getSerializerOptions(opts);
    const j2x = new json2xml(parserOptions);
    const node = { [parserOptions.rootNodeName]: obj };
    const xmlData = j2x.build(node);
    return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>${xmlData}`.replace(/\n/g, "");
}
/**
 * Converts given XML string into JSON
 * @param str - String containing the XML content to be parsed into JSON
 * @param opts - Options that govern the parsing of given xml string
 * `includeRoot` indicates whether the root element is to be included or not in the output
 */
async function parseXML(str, opts = {}) {
    if (!str) {
        throw new Error("Document is empty");
    }
    const validation = XMLValidator.validate(str);
    if (validation !== true) {
        throw validation;
    }
    const parser = new XMLParser(getParserOptions(opts));
    const parsedXml = parser.parse(str);
    // Remove the <?xml version="..." ?> node.
    // This is a change in behavior on fxp v4. Issue #424
    if (parsedXml["?xml"]) {
        delete parsedXml["?xml"];
    }
    if (!opts.includeRoot) {
        for (const key of Object.keys(parsedXml)) {
            const value = parsedXml[key];
            return typeof value === "object" ? Object.assign({}, value) : value;
        }
    }
    return parsedXml;
}
//# sourceMappingURL=xml.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/log.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * The `@azure/logger` configuration for this package.
 */
const storage_blob_dist_esm_log_logger = esm_createClientLogger("storage-blob");
//# sourceMappingURL=log.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/BuffersStream.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * This class generates a readable stream from the data in an array of buffers.
 */
class BuffersStream extends external_node_stream_.Readable {
    buffers;
    byteLength;
    /**
     * The offset of data to be read in the current buffer.
     */
    byteOffsetInCurrentBuffer;
    /**
     * The index of buffer to be read in the array of buffers.
     */
    bufferIndex;
    /**
     * The total length of data already read.
     */
    pushedBytesLength;
    /**
     * Creates an instance of BuffersStream that will emit the data
     * contained in the array of buffers.
     *
     * @param buffers - Array of buffers containing the data
     * @param byteLength - The total length of data contained in the buffers
     */
    constructor(buffers, byteLength, options) {
        super(options);
        this.buffers = buffers;
        this.byteLength = byteLength;
        this.byteOffsetInCurrentBuffer = 0;
        this.bufferIndex = 0;
        this.pushedBytesLength = 0;
        // check byteLength is no larger than buffers[] total length
        let buffersLength = 0;
        for (const buf of this.buffers) {
            buffersLength += buf.byteLength;
        }
        if (buffersLength < this.byteLength) {
            throw new Error("Data size shouldn't be larger than the total length of buffers.");
        }
    }
    /**
     * Internal _read() that will be called when the stream wants to pull more data in.
     *
     * @param size - Optional. The size of data to be read
     */
    _read(size) {
        if (this.pushedBytesLength >= this.byteLength) {
            this.push(null);
        }
        if (!size) {
            size = this.readableHighWaterMark;
        }
        const outBuffers = [];
        let i = 0;
        while (i < size && this.pushedBytesLength < this.byteLength) {
            // The last buffer may be longer than the data it contains.
            const remainingDataInAllBuffers = this.byteLength - this.pushedBytesLength;
            const remainingCapacityInThisBuffer = this.buffers[this.bufferIndex].byteLength - this.byteOffsetInCurrentBuffer;
            const remaining = Math.min(remainingCapacityInThisBuffer, remainingDataInAllBuffers);
            if (remaining > size - i) {
                // chunkSize = size - i
                const end = this.byteOffsetInCurrentBuffer + size - i;
                outBuffers.push(this.buffers[this.bufferIndex].slice(this.byteOffsetInCurrentBuffer, end));
                this.pushedBytesLength += size - i;
                this.byteOffsetInCurrentBuffer = end;
                i = size;
                break;
            }
            else {
                // chunkSize = remaining
                const end = this.byteOffsetInCurrentBuffer + remaining;
                outBuffers.push(this.buffers[this.bufferIndex].slice(this.byteOffsetInCurrentBuffer, end));
                if (remaining === remainingCapacityInThisBuffer) {
                    // this.buffers[this.bufferIndex] used up, shift to next one
                    this.byteOffsetInCurrentBuffer = 0;
                    this.bufferIndex++;
                }
                else {
                    this.byteOffsetInCurrentBuffer = end;
                }
                this.pushedBytesLength += remaining;
                i += remaining;
            }
        }
        if (outBuffers.length > 1) {
            this.push(Buffer.concat(outBuffers));
        }
        else if (outBuffers.length === 1) {
            this.push(outBuffers[0]);
        }
    }
}
//# sourceMappingURL=BuffersStream.js.map
// EXTERNAL MODULE: external "node:buffer"
var external_node_buffer_ = __nccwpck_require__(4573);
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/PooledBuffer.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * maxBufferLength is max size of each buffer in the pooled buffers.
 */
const maxBufferLength = external_node_buffer_.constants.MAX_LENGTH;
/**
 * This class provides a buffer container which conceptually has no hard size limit.
 * It accepts a capacity, an array of input buffers and the total length of input data.
 * It will allocate an internal "buffer" of the capacity and fill the data in the input buffers
 * into the internal "buffer" serially with respect to the total length.
 * Then by calling PooledBuffer.getReadableStream(), you can get a readable stream
 * assembled from all the data in the internal "buffer".
 */
class PooledBuffer {
    /**
     * Internal buffers used to keep the data.
     * Each buffer has a length of the maxBufferLength except last one.
     */
    buffers = [];
    /**
     * The total size of internal buffers.
     */
    capacity;
    /**
     * The total size of data contained in internal buffers.
     */
    _size;
    /**
     * The size of the data contained in the pooled buffers.
     */
    get size() {
        return this._size;
    }
    constructor(capacity, buffers, totalLength) {
        this.capacity = capacity;
        this._size = 0;
        // allocate
        const bufferNum = Math.ceil(capacity / maxBufferLength);
        for (let i = 0; i < bufferNum; i++) {
            let len = i === bufferNum - 1 ? capacity % maxBufferLength : maxBufferLength;
            if (len === 0) {
                len = maxBufferLength;
            }
            this.buffers.push(Buffer.allocUnsafe(len));
        }
        if (buffers) {
            this.fill(buffers, totalLength);
        }
    }
    /**
     * Fill the internal buffers with data in the input buffers serially
     * with respect to the total length and the total capacity of the internal buffers.
     * Data copied will be shift out of the input buffers.
     *
     * @param buffers - Input buffers containing the data to be filled in the pooled buffer
     * @param totalLength - Total length of the data to be filled in.
     *
     */
    fill(buffers, totalLength) {
        this._size = Math.min(this.capacity, totalLength);
        let i = 0, j = 0, targetOffset = 0, sourceOffset = 0, totalCopiedNum = 0;
        while (totalCopiedNum < this._size) {
            const source = buffers[i];
            const target = this.buffers[j];
            const copiedNum = source.copy(target, targetOffset, sourceOffset);
            totalCopiedNum += copiedNum;
            sourceOffset += copiedNum;
            targetOffset += copiedNum;
            if (sourceOffset === source.length) {
                i++;
                sourceOffset = 0;
            }
            if (targetOffset === target.length) {
                j++;
                targetOffset = 0;
            }
        }
        // clear copied from source buffers
        buffers.splice(0, i);
        if (buffers.length > 0) {
            buffers[0] = buffers[0].slice(sourceOffset);
        }
    }
    /**
     * Get the readable stream assembled from all the data in the internal buffers.
     *
     */
    getReadableStream() {
        return new BuffersStream(this.buffers, this.size);
    }
}
//# sourceMappingURL=PooledBuffer.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/BufferScheduler.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * This class accepts a Node.js Readable stream as input, and keeps reading data
 * from the stream into the internal buffer structure, until it reaches maxBuffers.
 * Every available buffer will try to trigger outgoingHandler.
 *
 * The internal buffer structure includes an incoming buffer array, and a outgoing
 * buffer array. The incoming buffer array includes the "empty" buffers can be filled
 * with new incoming data. The outgoing array includes the filled buffers to be
 * handled by outgoingHandler. Every above buffer size is defined by parameter bufferSize.
 *
 * NUM_OF_ALL_BUFFERS = BUFFERS_IN_INCOMING + BUFFERS_IN_OUTGOING + BUFFERS_UNDER_HANDLING
 *
 * NUM_OF_ALL_BUFFERS lesser than or equal to maxBuffers
 *
 * PERFORMANCE IMPROVEMENT TIPS:
 * 1. Input stream highWaterMark is better to set a same value with bufferSize
 *    parameter, which will avoid Buffer.concat() operations.
 * 2. concurrency should set a smaller value than maxBuffers, which is helpful to
 *    reduce the possibility when a outgoing handler waits for the stream data.
 *    in this situation, outgoing handlers are blocked.
 *    Outgoing queue shouldn't be empty.
 */
class BufferScheduler {
    /**
     * Size of buffers in incoming and outgoing queues. This class will try to align
     * data read from Readable stream into buffer chunks with bufferSize defined.
     */
    bufferSize;
    /**
     * How many buffers can be created or maintained.
     */
    maxBuffers;
    /**
     * A Node.js Readable stream.
     */
    readable;
    /**
     * OutgoingHandler is an async function triggered by BufferScheduler when there
     * are available buffers in outgoing array.
     */
    outgoingHandler;
    /**
     * An internal event emitter.
     */
    emitter = new external_events_.EventEmitter();
    /**
     * Concurrency of executing outgoingHandlers. (0 lesser than concurrency lesser than or equal to maxBuffers)
     */
    concurrency;
    /**
     * An internal offset marker to track data offset in bytes of next outgoingHandler.
     */
    offset = 0;
    /**
     * An internal marker to track whether stream is end.
     */
    isStreamEnd = false;
    /**
     * An internal marker to track whether stream or outgoingHandler returns error.
     */
    isError = false;
    /**
     * How many handlers are executing.
     */
    executingOutgoingHandlers = 0;
    /**
     * Encoding of the input Readable stream which has string data type instead of Buffer.
     */
    encoding;
    /**
     * How many buffers have been allocated.
     */
    numBuffers = 0;
    /**
     * Because this class doesn't know how much data every time stream pops, which
     * is defined by highWaterMarker of the stream. So BufferScheduler will cache
     * data received from the stream, when data in unresolvedDataArray exceeds the
     * blockSize defined, it will try to concat a blockSize of buffer, fill into available
     * buffers from incoming and push to outgoing array.
     */
    unresolvedDataArray = [];
    /**
     * How much data consisted in unresolvedDataArray.
     */
    unresolvedLength = 0;
    /**
     * The array includes all the available buffers can be used to fill data from stream.
     */
    incoming = [];
    /**
     * The array (queue) includes all the buffers filled from stream data.
     */
    outgoing = [];
    /**
     * Creates an instance of BufferScheduler.
     *
     * @param readable - A Node.js Readable stream
     * @param bufferSize - Buffer size of every maintained buffer
     * @param maxBuffers - How many buffers can be allocated
     * @param outgoingHandler - An async function scheduled to be
     *                                          triggered when a buffer fully filled
     *                                          with stream data
     * @param concurrency - Concurrency of executing outgoingHandlers (&gt;0)
     * @param encoding - [Optional] Encoding of Readable stream when it's a string stream
     */
    constructor(readable, bufferSize, maxBuffers, outgoingHandler, concurrency, encoding) {
        if (bufferSize <= 0) {
            throw new RangeError(`bufferSize must be larger than 0, current is ${bufferSize}`);
        }
        if (maxBuffers <= 0) {
            throw new RangeError(`maxBuffers must be larger than 0, current is ${maxBuffers}`);
        }
        if (concurrency <= 0) {
            throw new RangeError(`concurrency must be larger than 0, current is ${concurrency}`);
        }
        this.bufferSize = bufferSize;
        this.maxBuffers = maxBuffers;
        this.readable = readable;
        this.outgoingHandler = outgoingHandler;
        this.concurrency = concurrency;
        this.encoding = encoding;
    }
    /**
     * Start the scheduler, will return error when stream of any of the outgoingHandlers
     * returns error.
     *
     */
    async do() {
        return new Promise((resolve, reject) => {
            this.readable.on("data", (data) => {
                data = typeof data === "string" ? Buffer.from(data, this.encoding) : data;
                this.appendUnresolvedData(data);
                if (!this.resolveData()) {
                    this.readable.pause();
                }
            });
            this.readable.on("error", (err) => {
                this.emitter.emit("error", err);
            });
            this.readable.on("end", () => {
                this.isStreamEnd = true;
                this.emitter.emit("checkEnd");
            });
            this.emitter.on("error", (err) => {
                this.isError = true;
                this.readable.pause();
                reject(err);
            });
            this.emitter.on("checkEnd", () => {
                if (this.outgoing.length > 0) {
                    this.triggerOutgoingHandlers();
                    return;
                }
                if (this.isStreamEnd && this.executingOutgoingHandlers === 0) {
                    if (this.unresolvedLength > 0 && this.unresolvedLength < this.bufferSize) {
                        const buffer = this.shiftBufferFromUnresolvedDataArray();
                        this.outgoingHandler(() => buffer.getReadableStream(), buffer.size, this.offset)
                            .then(resolve)
                            .catch(reject);
                    }
                    else if (this.unresolvedLength >= this.bufferSize) {
                        return;
                    }
                    else {
                        resolve();
                    }
                }
            });
        });
    }
    /**
     * Insert a new data into unresolved array.
     *
     * @param data -
     */
    appendUnresolvedData(data) {
        this.unresolvedDataArray.push(data);
        this.unresolvedLength += data.length;
    }
    /**
     * Try to shift a buffer with size in blockSize. The buffer returned may be less
     * than blockSize when data in unresolvedDataArray is less than bufferSize.
     *
     */
    shiftBufferFromUnresolvedDataArray(buffer) {
        if (!buffer) {
            buffer = new PooledBuffer(this.bufferSize, this.unresolvedDataArray, this.unresolvedLength);
        }
        else {
            buffer.fill(this.unresolvedDataArray, this.unresolvedLength);
        }
        this.unresolvedLength -= buffer.size;
        return buffer;
    }
    /**
     * Resolve data in unresolvedDataArray. For every buffer with size in blockSize
     * shifted, it will try to get (or allocate a buffer) from incoming, and fill it,
     * then push it into outgoing to be handled by outgoing handler.
     *
     * Return false when available buffers in incoming are not enough, else true.
     *
     * @returns Return false when buffers in incoming are not enough, else true.
     */
    resolveData() {
        while (this.unresolvedLength >= this.bufferSize) {
            let buffer;
            if (this.incoming.length > 0) {
                buffer = this.incoming.shift();
                this.shiftBufferFromUnresolvedDataArray(buffer);
            }
            else {
                if (this.numBuffers < this.maxBuffers) {
                    buffer = this.shiftBufferFromUnresolvedDataArray();
                    this.numBuffers++;
                }
                else {
                    // No available buffer, wait for buffer returned
                    return false;
                }
            }
            this.outgoing.push(buffer);
            this.triggerOutgoingHandlers();
        }
        return true;
    }
    /**
     * Try to trigger a outgoing handler for every buffer in outgoing. Stop when
     * concurrency reaches.
     */
    async triggerOutgoingHandlers() {
        let buffer;
        do {
            if (this.executingOutgoingHandlers >= this.concurrency) {
                return;
            }
            buffer = this.outgoing.shift();
            if (buffer) {
                this.triggerOutgoingHandler(buffer);
            }
        } while (buffer);
    }
    /**
     * Trigger a outgoing handler for a buffer shifted from outgoing.
     *
     * @param buffer -
     */
    async triggerOutgoingHandler(buffer) {
        const bufferLength = buffer.size;
        this.executingOutgoingHandlers++;
        this.offset += bufferLength;
        try {
            await this.outgoingHandler(() => buffer.getReadableStream(), bufferLength, this.offset - bufferLength);
        }
        catch (err) {
            this.emitter.emit("error", err);
            return;
        }
        this.executingOutgoingHandlers--;
        this.reuseBuffer(buffer);
        this.emitter.emit("checkEnd");
    }
    /**
     * Return buffer used by outgoing handler into incoming.
     *
     * @param buffer -
     */
    reuseBuffer(buffer) {
        this.incoming.push(buffer);
        if (!this.isError && this.resolveData() && !this.isStreamEnd) {
            this.readable.resume();
        }
    }
}
//# sourceMappingURL=BufferScheduler.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/cache.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

let _defaultHttpClient;
function cache_getCachedDefaultHttpClient() {
    if (!_defaultHttpClient) {
        _defaultHttpClient = esm_defaultHttpClient_createDefaultHttpClient();
    }
    return _defaultHttpClient;
}
//# sourceMappingURL=cache.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/RequestPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * The base class from which all request policies derive.
 */
class BaseRequestPolicy {
    _nextPolicy;
    _options;
    /**
     * The main method to implement that manipulates a request/response.
     */
    constructor(
    /**
     * The next policy in the pipeline. Each policy is responsible for executing the next one if the request is to continue through the pipeline.
     */
    _nextPolicy, 
    /**
     * The options that can be passed to a given request policy.
     */
    _options) {
        this._nextPolicy = _nextPolicy;
        this._options = _options;
    }
    /**
     * Get whether or not a log with the provided log level should be logged.
     * @param logLevel - The log level of the log that will be logged.
     * @returns Whether or not a log with the provided log level should be logged.
     */
    shouldLog(logLevel) {
        return this._options.shouldLog(logLevel);
    }
    /**
     * Attempt to log the provided message to the provided logger. If no logger was provided or if
     * the log level does not meat the logger's threshold, then nothing will be logged.
     * @param logLevel - The log level of this log.
     * @param message - The message of this log.
     */
    log(logLevel, message) {
        this._options.log(logLevel, message);
    }
}
//# sourceMappingURL=RequestPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/utils/constants.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
const utils_constants_SDK_VERSION = "1.0.0";
const constants_URLConstants = {
    Parameters: {
        FORCE_BROWSER_NO_CACHE: "_",
        SIGNATURE: "sig",
        SNAPSHOT: "snapshot",
        VERSIONID: "versionid",
        TIMEOUT: "timeout",
    },
};
const constants_HeaderConstants = {
    AUTHORIZATION: "Authorization",
    AUTHORIZATION_SCHEME: "Bearer",
    CONTENT_ENCODING: "Content-Encoding",
    CONTENT_ID: "Content-ID",
    CONTENT_LANGUAGE: "Content-Language",
    CONTENT_LENGTH: "Content-Length",
    CONTENT_MD5: "Content-Md5",
    CONTENT_TRANSFER_ENCODING: "Content-Transfer-Encoding",
    CONTENT_TYPE: "Content-Type",
    COOKIE: "Cookie",
    DATE: "date",
    IF_MATCH: "if-match",
    IF_MODIFIED_SINCE: "if-modified-since",
    IF_NONE_MATCH: "if-none-match",
    IF_UNMODIFIED_SINCE: "if-unmodified-since",
    PREFIX_FOR_STORAGE: "x-ms-",
    RANGE: "Range",
    USER_AGENT: "User-Agent",
    X_MS_CLIENT_REQUEST_ID: "x-ms-client-request-id",
    X_MS_COPY_SOURCE: "x-ms-copy-source",
    X_MS_DATE: "x-ms-date",
    X_MS_ERROR_CODE: "x-ms-error-code",
    X_MS_VERSION: "x-ms-version",
    X_MS_CopySourceErrorCode: "x-ms-copy-source-error-code",
};
const constants_DevelopmentConnectionString = (/* unused pure expression or super */ null && (`DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;`));
/// List of ports used for path style addressing.
/// Path style addressing means that storage account is put in URI's Path segment in instead of in host.
const constants_PathStylePorts = (/* unused pure expression or super */ null && ([
    "10000",
    "10001",
    "10002",
    "10003",
    "10004",
    "10100",
    "10101",
    "10102",
    "10103",
    "10104",
    "11000",
    "11001",
    "11002",
    "11003",
    "11004",
    "11100",
    "11101",
    "11102",
    "11103",
    "11104",
]));
//# sourceMappingURL=constants.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/utils/utils.common.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * Reserved URL characters must be properly escaped for Storage services like Blob or File.
 *
 * ## URL encode and escape strategy for JS SDKs
 *
 * When customers pass a URL string into XxxClient classes constructor, the URL string may already be URL encoded or not.
 * But before sending to Azure Storage server, the URL must be encoded. However, it's hard for a SDK to guess whether the URL
 * string has been encoded or not. We have 2 potential strategies, and chose strategy two for the XxxClient constructors.
 *
 * ### Strategy One: Assume the customer URL string is not encoded, and always encode URL string in SDK.
 *
 * This is what legacy V2 SDK does, simple and works for most of the cases.
 * - When customer URL string is "http://account.blob.core.windows.net/con/b:",
 *   SDK will encode it to "http://account.blob.core.windows.net/con/b%3A" and send to server. A blob named "b:" will be created.
 * - When customer URL string is "http://account.blob.core.windows.net/con/b%3A",
 *   SDK will encode it to "http://account.blob.core.windows.net/con/b%253A" and send to server. A blob named "b%3A" will be created.
 *
 * But this strategy will make it not possible to create a blob with "?" in it's name. Because when customer URL string is
 * "http://account.blob.core.windows.net/con/blob?name", the "?name" will be treated as URL paramter instead of blob name.
 * If customer URL string is "http://account.blob.core.windows.net/con/blob%3Fname", a blob named "blob%3Fname" will be created.
 * V2 SDK doesn't have this issue because it doesn't allow customer pass in a full URL, it accepts a separate blob name and encodeURIComponent for it.
 * We cannot accept a SDK cannot create a blob name with "?". So we implement strategy two:
 *
 * ### Strategy Two: SDK doesn't assume the URL has been encoded or not. It will just escape the special characters.
 *
 * This is what V10 Blob Go SDK does. It accepts a URL type in Go, and call url.EscapedPath() to escape the special chars unescaped.
 * - When customer URL string is "http://account.blob.core.windows.net/con/b:",
 *   SDK will escape ":" like "http://account.blob.core.windows.net/con/b%3A" and send to server. A blob named "b:" will be created.
 * - When customer URL string is "http://account.blob.core.windows.net/con/b%3A",
 *   There is no special characters, so send "http://account.blob.core.windows.net/con/b%3A" to server. A blob named "b:" will be created.
 * - When customer URL string is "http://account.blob.core.windows.net/con/b%253A",
 *   There is no special characters, so send "http://account.blob.core.windows.net/con/b%253A" to server. A blob named "b%3A" will be created.
 *
 * This strategy gives us flexibility to create with any special characters. But "%" will be treated as a special characters, if the URL string
 * is not encoded, there shouldn't a "%" in the URL string, otherwise the URL is not a valid URL.
 * If customer needs to create a blob with "%" in it's blob name, use "%25" instead of "%". Just like above 3rd sample.
 * And following URL strings are invalid:
 * - "http://account.blob.core.windows.net/con/b%"
 * - "http://account.blob.core.windows.net/con/b%2"
 * - "http://account.blob.core.windows.net/con/b%G"
 *
 * Another special character is "?", use "%2F" to represent a blob name with "?" in a URL string.
 *
 * ### Strategy for containerName, blobName or other specific XXXName parameters in methods such as `containerClient.getBlobClient(blobName)`
 *
 * We will apply strategy one, and call encodeURIComponent for these parameters like blobName. Because what customers passes in is a plain name instead of a URL.
 *
 * @see https://learn.microsoft.com/rest/api/storageservices/naming-and-referencing-containers--blobs--and-metadata
 * @see https://learn.microsoft.com/rest/api/storageservices/naming-and-referencing-shares--directories--files--and-metadata
 *
 * @param url -
 */
function escapeURLPath(url) {
    const urlParsed = new URL(url);
    let path = urlParsed.pathname;
    path = path || "/";
    path = utils_common_escape(path);
    urlParsed.pathname = path;
    return urlParsed.toString();
}
function getProxyUriFromDevConnString(connectionString) {
    // Development Connection String
    // https://learn.microsoft.com/azure/storage/common/storage-configure-connection-string#connect-to-the-emulator-account-using-the-well-known-account-name-and-key
    let proxyUri = "";
    if (connectionString.search("DevelopmentStorageProxyUri=") !== -1) {
        // CONNECTION_STRING=UseDevelopmentStorage=true;DevelopmentStorageProxyUri=http://myProxyUri
        const matchCredentials = connectionString.split(";");
        for (const element of matchCredentials) {
            if (element.trim().startsWith("DevelopmentStorageProxyUri=")) {
                proxyUri = element.trim().match("DevelopmentStorageProxyUri=(.*)")[1];
            }
        }
    }
    return proxyUri;
}
function getValueInConnString(connectionString, argument) {
    const elements = connectionString.split(";");
    for (const element of elements) {
        if (element.trim().startsWith(argument)) {
            return element.trim().match(argument + "=(.*)")[1];
        }
    }
    return "";
}
/**
 * Extracts the parts of an Azure Storage account connection string.
 *
 * @param connectionString - Connection string.
 * @returns String key value pairs of the storage account's url and credentials.
 */
function extractConnectionStringParts(connectionString) {
    let proxyUri = "";
    if (connectionString.startsWith("UseDevelopmentStorage=true")) {
        // Development connection string
        proxyUri = getProxyUriFromDevConnString(connectionString);
        connectionString = DevelopmentConnectionString;
    }
    // Matching BlobEndpoint in the Account connection string
    let blobEndpoint = getValueInConnString(connectionString, "BlobEndpoint");
    // Slicing off '/' at the end if exists
    // (The methods that use `extractConnectionStringParts` expect the url to not have `/` at the end)
    blobEndpoint = blobEndpoint.endsWith("/") ? blobEndpoint.slice(0, -1) : blobEndpoint;
    if (connectionString.search("DefaultEndpointsProtocol=") !== -1 &&
        connectionString.search("AccountKey=") !== -1) {
        // Account connection string
        let defaultEndpointsProtocol = "";
        let accountName = "";
        let accountKey = Buffer.from("accountKey", "base64");
        let endpointSuffix = "";
        // Get account name and key
        accountName = getValueInConnString(connectionString, "AccountName");
        accountKey = Buffer.from(getValueInConnString(connectionString, "AccountKey"), "base64");
        if (!blobEndpoint) {
            // BlobEndpoint is not present in the Account connection string
            // Can be obtained from `${defaultEndpointsProtocol}://${accountName}.blob.${endpointSuffix}`
            defaultEndpointsProtocol = getValueInConnString(connectionString, "DefaultEndpointsProtocol");
            const protocol = defaultEndpointsProtocol.toLowerCase();
            if (protocol !== "https" && protocol !== "http") {
                throw new Error("Invalid DefaultEndpointsProtocol in the provided Connection String. Expecting 'https' or 'http'");
            }
            endpointSuffix = getValueInConnString(connectionString, "EndpointSuffix");
            if (!endpointSuffix) {
                throw new Error("Invalid EndpointSuffix in the provided Connection String");
            }
            blobEndpoint = `${defaultEndpointsProtocol}://${accountName}.blob.${endpointSuffix}`;
        }
        if (!accountName) {
            throw new Error("Invalid AccountName in the provided Connection String");
        }
        else if (accountKey.length === 0) {
            throw new Error("Invalid AccountKey in the provided Connection String");
        }
        return {
            kind: "AccountConnString",
            url: blobEndpoint,
            accountName,
            accountKey,
            proxyUri,
        };
    }
    else {
        // SAS connection string
        let accountSas = getValueInConnString(connectionString, "SharedAccessSignature");
        let accountName = getValueInConnString(connectionString, "AccountName");
        // if accountName is empty, try to read it from BlobEndpoint
        if (!accountName) {
            accountName = getAccountNameFromUrl(blobEndpoint);
        }
        if (!blobEndpoint) {
            throw new Error("Invalid BlobEndpoint in the provided SAS Connection String");
        }
        else if (!accountSas) {
            throw new Error("Invalid SharedAccessSignature in the provided SAS Connection String");
        }
        // client constructors assume accountSas does *not* start with ?
        if (accountSas.startsWith("?")) {
            accountSas = accountSas.substring(1);
        }
        return { kind: "SASConnString", url: blobEndpoint, accountName, accountSas };
    }
}
/**
 * Internal escape method implemented Strategy Two mentioned in escapeURL() description.
 *
 * @param text -
 */
function utils_common_escape(text) {
    return encodeURIComponent(text)
        .replace(/%2F/g, "/") // Don't escape for "/"
        .replace(/'/g, "%27") // Escape for "'"
        .replace(/\+/g, "%20")
        .replace(/%25/g, "%"); // Revert encoded "%"
}
/**
 * Append a string to URL path. Will remove duplicated "/" in front of the string
 * when URL path ends with a "/".
 *
 * @param url - Source URL string
 * @param name - String to be appended to URL
 * @returns An updated URL string
 */
function appendToURLPath(url, name) {
    const urlParsed = new URL(url);
    let path = urlParsed.pathname;
    path = path ? (path.endsWith("/") ? `${path}${name}` : `${path}/${name}`) : name;
    urlParsed.pathname = path;
    return urlParsed.toString();
}
/**
 * Set URL parameter name and value. If name exists in URL parameters, old value
 * will be replaced by name key. If not provide value, the parameter will be deleted.
 *
 * @param url - Source URL string
 * @param name - Parameter name
 * @param value - Parameter value
 * @returns An updated URL string
 */
function setURLParameter(url, name, value) {
    const urlParsed = new URL(url);
    const encodedName = encodeURIComponent(name);
    const encodedValue = value ? encodeURIComponent(value) : undefined;
    // mutating searchParams will change the encoding, so we have to do this ourselves
    const searchString = urlParsed.search === "" ? "?" : urlParsed.search;
    const searchPieces = [];
    for (const pair of searchString.slice(1).split("&")) {
        if (pair) {
            const [key] = pair.split("=", 2);
            if (key !== encodedName) {
                searchPieces.push(pair);
            }
        }
    }
    if (encodedValue) {
        searchPieces.push(`${encodedName}=${encodedValue}`);
    }
    urlParsed.search = searchPieces.length ? `?${searchPieces.join("&")}` : "";
    return urlParsed.toString();
}
/**
 * Get URL parameter by name.
 *
 * @param url -
 * @param name -
 */
function getURLParameter(url, name) {
    const urlParsed = new URL(url);
    return urlParsed.searchParams.get(name) ?? undefined;
}
/**
 * Set URL host.
 *
 * @param url - Source URL string
 * @param host - New host string
 * @returns An updated URL string
 */
function setURLHost(url, host) {
    const urlParsed = new URL(url);
    urlParsed.hostname = host;
    return urlParsed.toString();
}
/**
 * Get URL path from an URL string.
 *
 * @param url - Source URL string
 */
function getURLPath(url) {
    try {
        const urlParsed = new URL(url);
        return urlParsed.pathname;
    }
    catch (e) {
        return undefined;
    }
}
/**
 * Get URL scheme from an URL string.
 *
 * @param url - Source URL string
 */
function getURLScheme(url) {
    try {
        const urlParsed = new URL(url);
        return urlParsed.protocol.endsWith(":") ? urlParsed.protocol.slice(0, -1) : urlParsed.protocol;
    }
    catch (e) {
        return undefined;
    }
}
/**
 * Get URL path and query from an URL string.
 *
 * @param url - Source URL string
 */
function getURLPathAndQuery(url) {
    const urlParsed = new URL(url);
    const pathString = urlParsed.pathname;
    if (!pathString) {
        throw new RangeError("Invalid url without valid path.");
    }
    let queryString = urlParsed.search || "";
    queryString = queryString.trim();
    if (queryString !== "") {
        queryString = queryString.startsWith("?") ? queryString : `?${queryString}`; // Ensure query string start with '?'
    }
    return `${pathString}${queryString}`;
}
/**
 * Get URL query key value pairs from an URL string.
 *
 * @param url -
 */
function getURLQueries(url) {
    let queryString = new URL(url).search;
    if (!queryString) {
        return {};
    }
    queryString = queryString.trim();
    queryString = queryString.startsWith("?") ? queryString.substring(1) : queryString;
    let querySubStrings = queryString.split("&");
    querySubStrings = querySubStrings.filter((value) => {
        const indexOfEqual = value.indexOf("=");
        const lastIndexOfEqual = value.lastIndexOf("=");
        return (indexOfEqual > 0 && indexOfEqual === lastIndexOfEqual && lastIndexOfEqual < value.length - 1);
    });
    const queries = {};
    for (const querySubString of querySubStrings) {
        const splitResults = querySubString.split("=");
        const key = splitResults[0];
        const value = splitResults[1];
        queries[key] = value;
    }
    return queries;
}
/**
 * Append a string to URL query.
 *
 * @param url - Source URL string.
 * @param queryParts - String to be appended to the URL query.
 * @returns An updated URL string.
 */
function appendToURLQuery(url, queryParts) {
    const urlParsed = new URL(url);
    let query = urlParsed.search;
    if (query) {
        query += "&" + queryParts;
    }
    else {
        query = queryParts;
    }
    urlParsed.search = query;
    return urlParsed.toString();
}
/**
 * Rounds a date off to seconds.
 *
 * @param date -
 * @param withMilliseconds - If true, YYYY-MM-DDThh:mm:ss.fffffffZ will be returned;
 *                                          If false, YYYY-MM-DDThh:mm:ssZ will be returned.
 * @returns Date string in ISO8061 format, with or without 7 milliseconds component
 */
function truncatedISO8061Date(date, withMilliseconds = true) {
    // Date.toISOString() will return like "2018-10-29T06:34:36.139Z"
    const dateString = date.toISOString();
    return withMilliseconds
        ? dateString.substring(0, dateString.length - 1) + "0000" + "Z"
        : dateString.substring(0, dateString.length - 5) + "Z";
}
/**
 * Base64 encode.
 *
 * @param content -
 */
function base64encode(content) {
    return !isNodeLike ? btoa(content) : Buffer.from(content).toString("base64");
}
/**
 * Base64 decode.
 *
 * @param encodedString -
 */
function base64decode(encodedString) {
    return !isNodeLike ? atob(encodedString) : Buffer.from(encodedString, "base64").toString();
}
/**
 * Generate a 64 bytes base64 block ID string.
 *
 * @param blockIndex -
 */
function generateBlockID(blockIDPrefix, blockIndex) {
    // To generate a 64 bytes base64 string, source string should be 48
    const maxSourceStringLength = 48;
    // A blob can have a maximum of 100,000 uncommitted blocks at any given time
    const maxBlockIndexLength = 6;
    const maxAllowedBlockIDPrefixLength = maxSourceStringLength - maxBlockIndexLength;
    if (blockIDPrefix.length > maxAllowedBlockIDPrefixLength) {
        blockIDPrefix = blockIDPrefix.slice(0, maxAllowedBlockIDPrefixLength);
    }
    const res = blockIDPrefix +
        padStart(blockIndex.toString(), maxSourceStringLength - blockIDPrefix.length, "0");
    return base64encode(res);
}
/**
 * Delay specified time interval.
 *
 * @param timeInMs -
 * @param aborter -
 * @param abortError -
 */
async function utils_common_delay(timeInMs, aborter, abortError) {
    return new Promise((resolve, reject) => {
        /* eslint-disable-next-line prefer-const */
        let timeout;
        const abortHandler = () => {
            if (timeout !== undefined) {
                clearTimeout(timeout);
            }
            reject(abortError);
        };
        const resolveHandler = () => {
            if (aborter !== undefined) {
                aborter.removeEventListener("abort", abortHandler);
            }
            resolve();
        };
        timeout = setTimeout(resolveHandler, timeInMs);
        if (aborter !== undefined) {
            aborter.addEventListener("abort", abortHandler);
        }
    });
}
/**
 * String.prototype.padStart()
 *
 * @param currentString -
 * @param targetLength -
 * @param padString -
 */
function padStart(currentString, targetLength, padString = " ") {
    // @ts-expect-error: TS doesn't know this code needs to run downlevel sometimes
    if (String.prototype.padStart) {
        return currentString.padStart(targetLength, padString);
    }
    padString = padString || " ";
    if (currentString.length > targetLength) {
        return currentString;
    }
    else {
        targetLength = targetLength - currentString.length;
        if (targetLength > padString.length) {
            padString += padString.repeat(targetLength / padString.length);
        }
        return padString.slice(0, targetLength) + currentString;
    }
}
function sanitizeURL(url) {
    let safeURL = url;
    if (getURLParameter(safeURL, URLConstants.Parameters.SIGNATURE)) {
        safeURL = setURLParameter(safeURL, URLConstants.Parameters.SIGNATURE, "*****");
    }
    return safeURL;
}
function sanitizeHeaders(originalHeader) {
    const headers = createHttpHeaders();
    for (const [name, value] of originalHeader) {
        if (name.toLowerCase() === HeaderConstants.AUTHORIZATION.toLowerCase()) {
            headers.set(name, "*****");
        }
        else if (name.toLowerCase() === HeaderConstants.X_MS_COPY_SOURCE) {
            headers.set(name, sanitizeURL(value));
        }
        else {
            headers.set(name, value);
        }
    }
    return headers;
}
/**
 * If two strings are equal when compared case insensitive.
 *
 * @param str1 -
 * @param str2 -
 */
function iEqual(str1, str2) {
    return str1.toLocaleLowerCase() === str2.toLocaleLowerCase();
}
/**
 * Extracts account name from the url
 * @param url - url to extract the account name from
 * @returns with the account name
 */
function getAccountNameFromUrl(url) {
    const parsedUrl = new URL(url);
    let accountName;
    try {
        if (parsedUrl.hostname.split(".")[1] === "blob") {
            // `${defaultEndpointsProtocol}://${accountName}.blob.${endpointSuffix}`;
            accountName = parsedUrl.hostname.split(".")[0];
        }
        else if (isIpEndpointStyle(parsedUrl)) {
            // IPv4/IPv6 address hosts... Example - http://192.0.0.10:10001/devstoreaccount1/
            // Single word domain without a [dot] in the endpoint... Example - http://localhost:10001/devstoreaccount1/
            // .getPath() -> /devstoreaccount1/
            accountName = parsedUrl.pathname.split("/")[1];
        }
        else {
            // Custom domain case: "https://customdomain.com/containername/blob".
            accountName = "";
        }
        return accountName;
    }
    catch (error) {
        throw new Error("Unable to extract accountName with provided information.");
    }
}
function isIpEndpointStyle(parsedUrl) {
    const host = parsedUrl.host;
    // Case 1: Ipv6, use a broad regex to find out candidates whose host contains two ':'.
    // Case 2: localhost(:port) or host.docker.internal, use broad regex to match port part.
    // Case 3: Ipv4, use broad regex which just check if host contains Ipv4.
    // For valid host please refer to https://man7.org/linux/man-pages/man7/hostname.7.html.
    return (/^.*:.*:.*$|^(localhost|host.docker.internal)(:[0-9]+)?$|^(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])(\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])){3}(:[0-9]+)?$/.test(host) ||
        (Boolean(parsedUrl.port) && PathStylePorts.includes(parsedUrl.port)));
}
/**
 * Attach a TokenCredential to an object.
 *
 * @param thing -
 * @param credential -
 */
function attachCredential(thing, credential) {
    thing.credential = credential;
    return thing;
}
function httpAuthorizationToString(httpAuthorization) {
    return httpAuthorization ? httpAuthorization.scheme + " " + httpAuthorization.value : undefined;
}
/**
 * Escape the blobName but keep path separator ('/').
 */
function EscapePath(blobName) {
    const split = blobName.split("/");
    for (let i = 0; i < split.length; i++) {
        split[i] = encodeURIComponent(split[i]);
    }
    return split.join("/");
}
/**
 * A typesafe helper for ensuring that a given response object has
 * the original _response attached.
 * @param response - A response object from calling a client operation
 * @returns The same object, but with known _response property
 */
function assertResponse(response) {
    if (`_response` in response) {
        return response;
    }
    throw new TypeError(`Unexpected response object ${response}`);
}
//# sourceMappingURL=utils.common.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/StorageBrowserPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




/**
 * StorageBrowserPolicy will handle differences between Node.js and browser runtime, including:
 *
 * 1. Browsers cache GET/HEAD requests by adding conditional headers such as 'IF_MODIFIED_SINCE'.
 * StorageBrowserPolicy is a policy used to add a timestamp query to GET/HEAD request URL
 * thus avoid the browser cache.
 *
 * 2. Remove cookie header for security
 *
 * 3. Remove content-length header to avoid browsers warning
 */
class StorageBrowserPolicy extends BaseRequestPolicy {
    /**
     * Creates an instance of StorageBrowserPolicy.
     * @param nextPolicy -
     * @param options -
     */
    // The base class has a protected constructor. Adding a public one to enable constructing of this class.
    /* eslint-disable-next-line @typescript-eslint/no-useless-constructor*/
    constructor(nextPolicy, options) {
        super(nextPolicy, options);
    }
    /**
     * Sends out request.
     *
     * @param request -
     */
    async sendRequest(request) {
        if (esm_isNodeLike) {
            return this._nextPolicy.sendRequest(request);
        }
        if (request.method.toUpperCase() === "GET" || request.method.toUpperCase() === "HEAD") {
            request.url = setURLParameter(request.url, constants_URLConstants.Parameters.FORCE_BROWSER_NO_CACHE, new Date().getTime().toString());
        }
        request.headers.remove(constants_HeaderConstants.COOKIE);
        // According to XHR standards, content-length should be fully controlled by browsers
        request.headers.remove(constants_HeaderConstants.CONTENT_LENGTH);
        return this._nextPolicy.sendRequest(request);
    }
}
//# sourceMappingURL=StorageBrowserPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/StorageBrowserPolicyFactory.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * StorageBrowserPolicyFactory is a factory class helping generating StorageBrowserPolicy objects.
 */
class StorageBrowserPolicyFactory {
    /**
     * Creates a StorageBrowserPolicyFactory object.
     *
     * @param nextPolicy -
     * @param options -
     */
    create(nextPolicy, options) {
        return new StorageBrowserPolicy(nextPolicy, options);
    }
}
//# sourceMappingURL=StorageBrowserPolicyFactory.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/CredentialPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Credential policy used to sign HTTP(S) requests before sending. This is an
 * abstract class.
 */
class CredentialPolicy extends BaseRequestPolicy {
    /**
     * Sends out request.
     *
     * @param request -
     */
    sendRequest(request) {
        return this._nextPolicy.sendRequest(this.signRequest(request));
    }
    /**
     * Child classes must implement this method with request signing. This method
     * will be executed in {@link sendRequest}.
     *
     * @param request -
     */
    signRequest(request) {
        // Child classes must override this method with request signing. This method
        // will be executed in sendRequest().
        return request;
    }
}
//# sourceMappingURL=CredentialPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/AnonymousCredentialPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * AnonymousCredentialPolicy is used with HTTP(S) requests that read public resources
 * or for use with Shared Access Signatures (SAS).
 */
class AnonymousCredentialPolicy extends CredentialPolicy {
    /**
     * Creates an instance of AnonymousCredentialPolicy.
     * @param nextPolicy -
     * @param options -
     */
    // The base class has a protected constructor. Adding a public one to enable constructing of this class.
    /* eslint-disable-next-line @typescript-eslint/no-useless-constructor*/
    constructor(nextPolicy, options) {
        super(nextPolicy, options);
    }
}
//# sourceMappingURL=AnonymousCredentialPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/credentials/Credential.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Credential is an abstract class for Azure Storage HTTP requests signing. This
 * class will host an credentialPolicyCreator factory which generates CredentialPolicy.
 */
class Credential {
    /**
     * Creates a RequestPolicy object.
     *
     * @param _nextPolicy -
     * @param _options -
     */
    create(_nextPolicy, _options) {
        throw new Error("Method should be implemented in children classes.");
    }
}
//# sourceMappingURL=Credential.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/credentials/AnonymousCredential.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * AnonymousCredential provides a credentialPolicyCreator member used to create
 * AnonymousCredentialPolicy objects. AnonymousCredentialPolicy is used with
 * HTTP(S) requests that read public resources or for use with Shared Access
 * Signatures (SAS).
 */
class AnonymousCredential extends Credential {
    /**
     * Creates an {@link AnonymousCredentialPolicy} object.
     *
     * @param nextPolicy -
     * @param options -
     */
    create(nextPolicy, options) {
        return new AnonymousCredentialPolicy(nextPolicy, options);
    }
}
//# sourceMappingURL=AnonymousCredential.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/utils/SharedKeyComparator.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/*
 * We need to imitate .Net culture-aware sorting, which is used in storage service.
 * Below tables contain sort-keys for en-US culture.
 */
const table_lv0 = new Uint32Array([
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x71c, 0x0, 0x71f, 0x721,
    0x723, 0x725, 0x0, 0x0, 0x0, 0x72d, 0x803, 0x0, 0x0, 0x733, 0x0, 0xd03, 0xd1a, 0xd1c, 0xd1e,
    0xd20, 0xd22, 0xd24, 0xd26, 0xd28, 0xd2a, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0xe02, 0xe09, 0xe0a,
    0xe1a, 0xe21, 0xe23, 0xe25, 0xe2c, 0xe32, 0xe35, 0xe36, 0xe48, 0xe51, 0xe70, 0xe7c, 0xe7e, 0xe89,
    0xe8a, 0xe91, 0xe99, 0xe9f, 0xea2, 0xea4, 0xea6, 0xea7, 0xea9, 0x0, 0x0, 0x0, 0x743, 0x744, 0x748,
    0xe02, 0xe09, 0xe0a, 0xe1a, 0xe21, 0xe23, 0xe25, 0xe2c, 0xe32, 0xe35, 0xe36, 0xe48, 0xe51, 0xe70,
    0xe7c, 0xe7e, 0xe89, 0xe8a, 0xe91, 0xe99, 0xe9f, 0xea2, 0xea4, 0xea6, 0xea7, 0xea9, 0x0, 0x74c,
    0x0, 0x750, 0x0,
]);
const table_lv2 = new Uint32Array([
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12,
    0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12,
    0x12, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
]);
const table_lv4 = new Uint32Array([
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x8012, 0x0, 0x0, 0x0, 0x0, 0x0, 0x8212, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
]);
function compareHeader(lhs, rhs) {
    if (isLessThan(lhs, rhs))
        return -1;
    return 1;
}
function isLessThan(lhs, rhs) {
    const tables = [table_lv0, table_lv2, table_lv4];
    let curr_level = 0;
    let i = 0;
    let j = 0;
    while (curr_level < tables.length) {
        if (curr_level === tables.length - 1 && i !== j) {
            return i > j;
        }
        const weight1 = i < lhs.length ? tables[curr_level][lhs[i].charCodeAt(0)] : 0x1;
        const weight2 = j < rhs.length ? tables[curr_level][rhs[j].charCodeAt(0)] : 0x1;
        if (weight1 === 0x1 && weight2 === 0x1) {
            i = 0;
            j = 0;
            ++curr_level;
        }
        else if (weight1 === weight2) {
            ++i;
            ++j;
        }
        else if (weight1 === 0) {
            ++i;
        }
        else if (weight2 === 0) {
            ++j;
        }
        else {
            return weight1 < weight2;
        }
    }
    return false;
}
//# sourceMappingURL=SharedKeyComparator.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/StorageSharedKeyCredentialPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




/**
 * StorageSharedKeyCredentialPolicy is a policy used to sign HTTP request with a shared key.
 */
class StorageSharedKeyCredentialPolicy extends CredentialPolicy {
    /**
     * Reference to StorageSharedKeyCredential which generates StorageSharedKeyCredentialPolicy
     */
    factory;
    /**
     * Creates an instance of StorageSharedKeyCredentialPolicy.
     * @param nextPolicy -
     * @param options -
     * @param factory -
     */
    constructor(nextPolicy, options, factory) {
        super(nextPolicy, options);
        this.factory = factory;
    }
    /**
     * Signs request.
     *
     * @param request -
     */
    signRequest(request) {
        request.headers.set(constants_HeaderConstants.X_MS_DATE, new Date().toUTCString());
        if (request.body &&
            (typeof request.body === "string" || request.body !== undefined) &&
            request.body.length > 0) {
            request.headers.set(constants_HeaderConstants.CONTENT_LENGTH, Buffer.byteLength(request.body));
        }
        const stringToSign = [
            request.method.toUpperCase(),
            this.getHeaderValueToSign(request, constants_HeaderConstants.CONTENT_LANGUAGE),
            this.getHeaderValueToSign(request, constants_HeaderConstants.CONTENT_ENCODING),
            this.getHeaderValueToSign(request, constants_HeaderConstants.CONTENT_LENGTH),
            this.getHeaderValueToSign(request, constants_HeaderConstants.CONTENT_MD5),
            this.getHeaderValueToSign(request, constants_HeaderConstants.CONTENT_TYPE),
            this.getHeaderValueToSign(request, constants_HeaderConstants.DATE),
            this.getHeaderValueToSign(request, constants_HeaderConstants.IF_MODIFIED_SINCE),
            this.getHeaderValueToSign(request, constants_HeaderConstants.IF_MATCH),
            this.getHeaderValueToSign(request, constants_HeaderConstants.IF_NONE_MATCH),
            this.getHeaderValueToSign(request, constants_HeaderConstants.IF_UNMODIFIED_SINCE),
            this.getHeaderValueToSign(request, constants_HeaderConstants.RANGE),
        ].join("\n") +
            "\n" +
            this.getCanonicalizedHeadersString(request) +
            this.getCanonicalizedResourceString(request);
        const signature = this.factory.computeHMACSHA256(stringToSign);
        request.headers.set(constants_HeaderConstants.AUTHORIZATION, `SharedKey ${this.factory.accountName}:${signature}`);
        // console.log(`[URL]:${request.url}`);
        // console.log(`[HEADERS]:${request.headers.toString()}`);
        // console.log(`[STRING TO SIGN]:${JSON.stringify(stringToSign)}`);
        // console.log(`[KEY]: ${request.headers.get(HeaderConstants.AUTHORIZATION)}`);
        return request;
    }
    /**
     * Retrieve header value according to shared key sign rules.
     * @see https://learn.microsoft.com/rest/api/storageservices/authenticate-with-shared-key
     *
     * @param request -
     * @param headerName -
     */
    getHeaderValueToSign(request, headerName) {
        const value = request.headers.get(headerName);
        if (!value) {
            return "";
        }
        // When using version 2015-02-21 or later, if Content-Length is zero, then
        // set the Content-Length part of the StringToSign to an empty string.
        // https://learn.microsoft.com/rest/api/storageservices/authenticate-with-shared-key
        if (headerName === constants_HeaderConstants.CONTENT_LENGTH && value === "0") {
            return "";
        }
        return value;
    }
    /**
     * To construct the CanonicalizedHeaders portion of the signature string, follow these steps:
     * 1. Retrieve all headers for the resource that begin with x-ms-, including the x-ms-date header.
     * 2. Convert each HTTP header name to lowercase.
     * 3. Sort the headers lexicographically by header name, in ascending order.
     *    Each header may appear only once in the string.
     * 4. Replace any linear whitespace in the header value with a single space.
     * 5. Trim any whitespace around the colon in the header.
     * 6. Finally, append a new-line character to each canonicalized header in the resulting list.
     *    Construct the CanonicalizedHeaders string by concatenating all headers in this list into a single string.
     *
     * @param request -
     */
    getCanonicalizedHeadersString(request) {
        let headersArray = request.headers.headersArray().filter((value) => {
            return value.name.toLowerCase().startsWith(constants_HeaderConstants.PREFIX_FOR_STORAGE);
        });
        headersArray.sort((a, b) => {
            return compareHeader(a.name.toLowerCase(), b.name.toLowerCase());
        });
        // Remove duplicate headers
        headersArray = headersArray.filter((value, index, array) => {
            if (index > 0 && value.name.toLowerCase() === array[index - 1].name.toLowerCase()) {
                return false;
            }
            return true;
        });
        let canonicalizedHeadersStringToSign = "";
        headersArray.forEach((header) => {
            canonicalizedHeadersStringToSign += `${header.name
                .toLowerCase()
                .trimRight()}:${header.value.trimLeft()}\n`;
        });
        return canonicalizedHeadersStringToSign;
    }
    /**
     * Retrieves the webResource canonicalized resource string.
     *
     * @param request -
     */
    getCanonicalizedResourceString(request) {
        const path = getURLPath(request.url) || "/";
        let canonicalizedResourceString = "";
        canonicalizedResourceString += `/${this.factory.accountName}${path}`;
        const queries = getURLQueries(request.url);
        const lowercaseQueries = {};
        if (queries) {
            const queryKeys = [];
            for (const key in queries) {
                if (Object.prototype.hasOwnProperty.call(queries, key)) {
                    const lowercaseKey = key.toLowerCase();
                    lowercaseQueries[lowercaseKey] = queries[key];
                    queryKeys.push(lowercaseKey);
                }
            }
            queryKeys.sort();
            for (const key of queryKeys) {
                canonicalizedResourceString += `\n${key}:${decodeURIComponent(lowercaseQueries[key])}`;
            }
        }
        return canonicalizedResourceString;
    }
}
//# sourceMappingURL=StorageSharedKeyCredentialPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/credentials/StorageSharedKeyCredential.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * StorageSharedKeyCredential for account key authorization of Azure Storage service.
 */
class StorageSharedKeyCredential extends Credential {
    /**
     * Azure Storage account name; readonly.
     */
    accountName;
    /**
     * Azure Storage account key; readonly.
     */
    accountKey;
    /**
     * Creates an instance of StorageSharedKeyCredential.
     * @param accountName -
     * @param accountKey -
     */
    constructor(accountName, accountKey) {
        super();
        this.accountName = accountName;
        this.accountKey = Buffer.from(accountKey, "base64");
    }
    /**
     * Creates a StorageSharedKeyCredentialPolicy object.
     *
     * @param nextPolicy -
     * @param options -
     */
    create(nextPolicy, options) {
        return new StorageSharedKeyCredentialPolicy(nextPolicy, options, this);
    }
    /**
     * Generates a hash signature for an HTTP request or for a SAS.
     *
     * @param stringToSign -
     */
    computeHMACSHA256(stringToSign) {
        return (0,external_node_crypto_.createHmac)("sha256", this.accountKey).update(stringToSign, "utf8").digest("base64");
    }
}
//# sourceMappingURL=StorageSharedKeyCredential.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/log.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * The `@azure/logger` configuration for this package.
 */
const storage_common_dist_esm_log_logger = esm_createClientLogger("storage-common");
//# sourceMappingURL=log.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/StorageRetryPolicyType.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * RetryPolicy types.
 */
var StorageRetryPolicyType;
(function (StorageRetryPolicyType) {
    /**
     * Exponential retry. Retry time delay grows exponentially.
     */
    StorageRetryPolicyType[StorageRetryPolicyType["EXPONENTIAL"] = 0] = "EXPONENTIAL";
    /**
     * Linear retry. Retry time delay grows linearly.
     */
    StorageRetryPolicyType[StorageRetryPolicyType["FIXED"] = 1] = "FIXED";
})(StorageRetryPolicyType || (StorageRetryPolicyType = {}));
//# sourceMappingURL=StorageRetryPolicyType.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/StorageRetryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.






/**
 * A factory method used to generated a RetryPolicy factory.
 *
 * @param retryOptions -
 */
function NewRetryPolicyFactory(retryOptions) {
    return {
        create: (nextPolicy, options) => {
            return new StorageRetryPolicy(nextPolicy, options, retryOptions);
        },
    };
}
// Default values of StorageRetryOptions
const DEFAULT_RETRY_OPTIONS = {
    maxRetryDelayInMs: 120 * 1000,
    maxTries: 4,
    retryDelayInMs: 4 * 1000,
    retryPolicyType: StorageRetryPolicyType.EXPONENTIAL,
    secondaryHost: "",
    tryTimeoutInMs: undefined, // Use server side default timeout strategy
};
const RETRY_ABORT_ERROR = new AbortError_AbortError("The operation was aborted.");
/**
 * Retry policy with exponential retry and linear retry implemented.
 */
class StorageRetryPolicy extends BaseRequestPolicy {
    /**
     * RetryOptions.
     */
    retryOptions;
    /**
     * Creates an instance of RetryPolicy.
     *
     * @param nextPolicy -
     * @param options -
     * @param retryOptions -
     */
    constructor(nextPolicy, options, retryOptions = DEFAULT_RETRY_OPTIONS) {
        super(nextPolicy, options);
        // Initialize retry options
        this.retryOptions = {
            retryPolicyType: retryOptions.retryPolicyType
                ? retryOptions.retryPolicyType
                : DEFAULT_RETRY_OPTIONS.retryPolicyType,
            maxTries: retryOptions.maxTries && retryOptions.maxTries >= 1
                ? Math.floor(retryOptions.maxTries)
                : DEFAULT_RETRY_OPTIONS.maxTries,
            tryTimeoutInMs: retryOptions.tryTimeoutInMs && retryOptions.tryTimeoutInMs >= 0
                ? retryOptions.tryTimeoutInMs
                : DEFAULT_RETRY_OPTIONS.tryTimeoutInMs,
            retryDelayInMs: retryOptions.retryDelayInMs && retryOptions.retryDelayInMs >= 0
                ? Math.min(retryOptions.retryDelayInMs, retryOptions.maxRetryDelayInMs
                    ? retryOptions.maxRetryDelayInMs
                    : DEFAULT_RETRY_OPTIONS.maxRetryDelayInMs)
                : DEFAULT_RETRY_OPTIONS.retryDelayInMs,
            maxRetryDelayInMs: retryOptions.maxRetryDelayInMs && retryOptions.maxRetryDelayInMs >= 0
                ? retryOptions.maxRetryDelayInMs
                : DEFAULT_RETRY_OPTIONS.maxRetryDelayInMs,
            secondaryHost: retryOptions.secondaryHost
                ? retryOptions.secondaryHost
                : DEFAULT_RETRY_OPTIONS.secondaryHost,
        };
    }
    /**
     * Sends request.
     *
     * @param request -
     */
    async sendRequest(request) {
        return this.attemptSendRequest(request, false, 1);
    }
    /**
     * Decide and perform next retry. Won't mutate request parameter.
     *
     * @param request -
     * @param secondaryHas404 -  If attempt was against the secondary & it returned a StatusNotFound (404), then
     *                                   the resource was not found. This may be due to replication delay. So, in this
     *                                   case, we'll never try the secondary again for this operation.
     * @param attempt -           How many retries has been attempted to performed, starting from 1, which includes
     *                                   the attempt will be performed by this method call.
     */
    async attemptSendRequest(request, secondaryHas404, attempt) {
        const newRequest = request.clone();
        const isPrimaryRetry = secondaryHas404 ||
            !this.retryOptions.secondaryHost ||
            !(request.method === "GET" || request.method === "HEAD" || request.method === "OPTIONS") ||
            attempt % 2 === 1;
        if (!isPrimaryRetry) {
            newRequest.url = setURLHost(newRequest.url, this.retryOptions.secondaryHost);
        }
        // Set the server-side timeout query parameter "timeout=[seconds]"
        if (this.retryOptions.tryTimeoutInMs) {
            newRequest.url = setURLParameter(newRequest.url, constants_URLConstants.Parameters.TIMEOUT, Math.floor(this.retryOptions.tryTimeoutInMs / 1000).toString());
        }
        let response;
        try {
            storage_common_dist_esm_log_logger.info(`RetryPolicy: =====> Try=${attempt} ${isPrimaryRetry ? "Primary" : "Secondary"}`);
            response = await this._nextPolicy.sendRequest(newRequest);
            if (!this.shouldRetry(isPrimaryRetry, attempt, response)) {
                return response;
            }
            secondaryHas404 = secondaryHas404 || (!isPrimaryRetry && response.status === 404);
        }
        catch (err) {
            storage_common_dist_esm_log_logger.error(`RetryPolicy: Caught error, message: ${err.message}, code: ${err.code}`);
            if (!this.shouldRetry(isPrimaryRetry, attempt, response, err)) {
                throw err;
            }
        }
        await this.delay(isPrimaryRetry, attempt, request.abortSignal);
        return this.attemptSendRequest(request, secondaryHas404, ++attempt);
    }
    /**
     * Decide whether to retry according to last HTTP response and retry counters.
     *
     * @param isPrimaryRetry -
     * @param attempt -
     * @param response -
     * @param err -
     */
    shouldRetry(isPrimaryRetry, attempt, response, err) {
        if (attempt >= this.retryOptions.maxTries) {
            storage_common_dist_esm_log_logger.info(`RetryPolicy: Attempt(s) ${attempt} >= maxTries ${this.retryOptions
                .maxTries}, no further try.`);
            return false;
        }
        // Handle network failures, you may need to customize the list when you implement
        // your own http client
        const retriableErrors = [
            "ETIMEDOUT",
            "ESOCKETTIMEDOUT",
            "ECONNREFUSED",
            "ECONNRESET",
            "ENOENT",
            "ENOTFOUND",
            "TIMEOUT",
            "EPIPE",
            "REQUEST_SEND_ERROR", // For default xhr based http client provided in ms-rest-js
        ];
        if (err) {
            for (const retriableError of retriableErrors) {
                if (err.name.toUpperCase().includes(retriableError) ||
                    err.message.toUpperCase().includes(retriableError) ||
                    (err.code && err.code.toString().toUpperCase() === retriableError)) {
                    storage_common_dist_esm_log_logger.info(`RetryPolicy: Network error ${retriableError} found, will retry.`);
                    return true;
                }
            }
        }
        // If attempt was against the secondary & it returned a StatusNotFound (404), then
        // the resource was not found. This may be due to replication delay. So, in this
        // case, we'll never try the secondary again for this operation.
        if (response || err) {
            const statusCode = response ? response.status : err ? err.statusCode : 0;
            if (!isPrimaryRetry && statusCode === 404) {
                storage_common_dist_esm_log_logger.info(`RetryPolicy: Secondary access with 404, will retry.`);
                return true;
            }
            // Server internal error or server timeout
            if (statusCode === 503 || statusCode === 500) {
                storage_common_dist_esm_log_logger.info(`RetryPolicy: Will retry for status code ${statusCode}.`);
                return true;
            }
        }
        if (response) {
            // Retry select Copy Source Error Codes.
            if (response?.status >= 400) {
                const copySourceError = response.headers.get(constants_HeaderConstants.X_MS_CopySourceErrorCode);
                if (copySourceError !== undefined) {
                    switch (copySourceError) {
                        case "InternalError":
                        case "OperationTimedOut":
                        case "ServerBusy":
                            return true;
                    }
                }
            }
        }
        if (err?.code === "PARSE_ERROR" && err?.message.startsWith(`Error "Error: Unclosed root tag`)) {
            storage_common_dist_esm_log_logger.info("RetryPolicy: Incomplete XML response likely due to service timeout, will retry.");
            return true;
        }
        return false;
    }
    /**
     * Delay a calculated time between retries.
     *
     * @param isPrimaryRetry -
     * @param attempt -
     * @param abortSignal -
     */
    async delay(isPrimaryRetry, attempt, abortSignal) {
        let delayTimeInMs = 0;
        if (isPrimaryRetry) {
            switch (this.retryOptions.retryPolicyType) {
                case StorageRetryPolicyType.EXPONENTIAL:
                    delayTimeInMs = Math.min((Math.pow(2, attempt - 1) - 1) * this.retryOptions.retryDelayInMs, this.retryOptions.maxRetryDelayInMs);
                    break;
                case StorageRetryPolicyType.FIXED:
                    delayTimeInMs = this.retryOptions.retryDelayInMs;
                    break;
            }
        }
        else {
            delayTimeInMs = Math.random() * 1000;
        }
        storage_common_dist_esm_log_logger.info(`RetryPolicy: Delay for ${delayTimeInMs}ms`);
        return utils_common_delay(delayTimeInMs, abortSignal, RETRY_ABORT_ERROR);
    }
}
//# sourceMappingURL=StorageRetryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/StorageRetryPolicyFactory.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * StorageRetryPolicyFactory is a factory class helping generating {@link StorageRetryPolicy} objects.
 */
class StorageRetryPolicyFactory {
    retryOptions;
    /**
     * Creates an instance of StorageRetryPolicyFactory.
     * @param retryOptions -
     */
    constructor(retryOptions) {
        this.retryOptions = retryOptions;
    }
    /**
     * Creates a StorageRetryPolicy object.
     *
     * @param nextPolicy -
     * @param options -
     */
    create(nextPolicy, options) {
        return new StorageRetryPolicy(nextPolicy, options, this.retryOptions);
    }
}
//# sourceMappingURL=StorageRetryPolicyFactory.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/StorageBrowserPolicyV2.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * The programmatic identifier of the StorageBrowserPolicy.
 */
const storageBrowserPolicyName = "storageBrowserPolicy";
/**
 * storageBrowserPolicy is a policy used to prevent browsers from caching requests
 * and to remove cookies and explicit content-length headers.
 */
function storageBrowserPolicy() {
    return {
        name: storageBrowserPolicyName,
        async sendRequest(request, next) {
            if (esm_isNodeLike) {
                return next(request);
            }
            if (request.method === "GET" || request.method === "HEAD") {
                request.url = setURLParameter(request.url, constants_URLConstants.Parameters.FORCE_BROWSER_NO_CACHE, new Date().getTime().toString());
            }
            request.headers.delete(constants_HeaderConstants.COOKIE);
            // According to XHR standards, content-length should be fully controlled by browsers
            request.headers.delete(constants_HeaderConstants.CONTENT_LENGTH);
            return next(request);
        },
    };
}
//# sourceMappingURL=StorageBrowserPolicyV2.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/StorageCorrectContentLengthPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * The programmatic identifier of the storageCorrectContentLengthPolicy.
 */
const storageCorrectContentLengthPolicyName = "StorageCorrectContentLengthPolicy";
/**
 * storageCorrectContentLengthPolicy to correctly set Content-Length header with request body length.
 */
function storageCorrectContentLengthPolicy() {
    function correctContentLength(request) {
        if (request.body &&
            (typeof request.body === "string" || Buffer.isBuffer(request.body)) &&
            request.body.length > 0) {
            request.headers.set(constants_HeaderConstants.CONTENT_LENGTH, Buffer.byteLength(request.body));
        }
    }
    return {
        name: storageCorrectContentLengthPolicyName,
        async sendRequest(request, next) {
            correctContentLength(request);
            return next(request);
        },
    };
}
//# sourceMappingURL=StorageCorrectContentLengthPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/StorageRetryPolicyV2.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.







/**
 * Name of the {@link storageRetryPolicy}
 */
const storageRetryPolicyName = "storageRetryPolicy";
// Default values of StorageRetryOptions
const StorageRetryPolicyV2_DEFAULT_RETRY_OPTIONS = {
    maxRetryDelayInMs: 120 * 1000,
    maxTries: 4,
    retryDelayInMs: 4 * 1000,
    retryPolicyType: StorageRetryPolicyType.EXPONENTIAL,
    secondaryHost: "",
    tryTimeoutInMs: undefined, // Use server side default timeout strategy
};
const retriableErrors = [
    "ETIMEDOUT",
    "ESOCKETTIMEDOUT",
    "ECONNREFUSED",
    "ECONNRESET",
    "ENOENT",
    "ENOTFOUND",
    "TIMEOUT",
    "EPIPE",
    "REQUEST_SEND_ERROR",
];
const StorageRetryPolicyV2_RETRY_ABORT_ERROR = new AbortError_AbortError("The operation was aborted.");
/**
 * Retry policy with exponential retry and linear retry implemented.
 */
function storageRetryPolicy(options = {}) {
    const retryPolicyType = options.retryPolicyType ?? StorageRetryPolicyV2_DEFAULT_RETRY_OPTIONS.retryPolicyType;
    const maxTries = options.maxTries ?? StorageRetryPolicyV2_DEFAULT_RETRY_OPTIONS.maxTries;
    const retryDelayInMs = options.retryDelayInMs ?? StorageRetryPolicyV2_DEFAULT_RETRY_OPTIONS.retryDelayInMs;
    const maxRetryDelayInMs = options.maxRetryDelayInMs ?? StorageRetryPolicyV2_DEFAULT_RETRY_OPTIONS.maxRetryDelayInMs;
    const secondaryHost = options.secondaryHost ?? StorageRetryPolicyV2_DEFAULT_RETRY_OPTIONS.secondaryHost;
    const tryTimeoutInMs = options.tryTimeoutInMs ?? StorageRetryPolicyV2_DEFAULT_RETRY_OPTIONS.tryTimeoutInMs;
    function shouldRetry({ isPrimaryRetry, attempt, response, error, }) {
        if (attempt >= maxTries) {
            storage_common_dist_esm_log_logger.info(`RetryPolicy: Attempt(s) ${attempt} >= maxTries ${maxTries}, no further try.`);
            return false;
        }
        if (error) {
            for (const retriableError of retriableErrors) {
                if (error.name.toUpperCase().includes(retriableError) ||
                    error.message.toUpperCase().includes(retriableError) ||
                    (error.code && error.code.toString().toUpperCase() === retriableError)) {
                    storage_common_dist_esm_log_logger.info(`RetryPolicy: Network error ${retriableError} found, will retry.`);
                    return true;
                }
            }
            if (error?.code === "PARSE_ERROR" &&
                error?.message.startsWith(`Error "Error: Unclosed root tag`)) {
                storage_common_dist_esm_log_logger.info("RetryPolicy: Incomplete XML response likely due to service timeout, will retry.");
                return true;
            }
        }
        // If attempt was against the secondary & it returned a StatusNotFound (404), then
        // the resource was not found. This may be due to replication delay. So, in this
        // case, we'll never try the secondary again for this operation.
        if (response || error) {
            const statusCode = response?.status ?? error?.statusCode ?? 0;
            if (!isPrimaryRetry && statusCode === 404) {
                storage_common_dist_esm_log_logger.info(`RetryPolicy: Secondary access with 404, will retry.`);
                return true;
            }
            // Server internal error or server timeout
            if (statusCode === 503 || statusCode === 500) {
                storage_common_dist_esm_log_logger.info(`RetryPolicy: Will retry for status code ${statusCode}.`);
                return true;
            }
        }
        if (response) {
            // Retry select Copy Source Error Codes.
            if (response?.status >= 400) {
                const copySourceError = response.headers.get(constants_HeaderConstants.X_MS_CopySourceErrorCode);
                if (copySourceError !== undefined) {
                    switch (copySourceError) {
                        case "InternalError":
                        case "OperationTimedOut":
                        case "ServerBusy":
                            return true;
                    }
                }
            }
        }
        return false;
    }
    function calculateDelay(isPrimaryRetry, attempt) {
        let delayTimeInMs = 0;
        if (isPrimaryRetry) {
            switch (retryPolicyType) {
                case StorageRetryPolicyType.EXPONENTIAL:
                    delayTimeInMs = Math.min((Math.pow(2, attempt - 1) - 1) * retryDelayInMs, maxRetryDelayInMs);
                    break;
                case StorageRetryPolicyType.FIXED:
                    delayTimeInMs = retryDelayInMs;
                    break;
            }
        }
        else {
            delayTimeInMs = Math.random() * 1000;
        }
        storage_common_dist_esm_log_logger.info(`RetryPolicy: Delay for ${delayTimeInMs}ms`);
        return delayTimeInMs;
    }
    return {
        name: storageRetryPolicyName,
        async sendRequest(request, next) {
            // Set the server-side timeout query parameter "timeout=[seconds]"
            if (tryTimeoutInMs) {
                request.url = setURLParameter(request.url, constants_URLConstants.Parameters.TIMEOUT, String(Math.floor(tryTimeoutInMs / 1000)));
            }
            const primaryUrl = request.url;
            const secondaryUrl = secondaryHost ? setURLHost(request.url, secondaryHost) : undefined;
            let secondaryHas404 = false;
            let attempt = 1;
            let retryAgain = true;
            let response;
            let error;
            while (retryAgain) {
                const isPrimaryRetry = secondaryHas404 ||
                    !secondaryUrl ||
                    !["GET", "HEAD", "OPTIONS"].includes(request.method) ||
                    attempt % 2 === 1;
                request.url = isPrimaryRetry ? primaryUrl : secondaryUrl;
                response = undefined;
                error = undefined;
                try {
                    storage_common_dist_esm_log_logger.info(`RetryPolicy: =====> Try=${attempt} ${isPrimaryRetry ? "Primary" : "Secondary"}`);
                    response = await next(request);
                    secondaryHas404 = secondaryHas404 || (!isPrimaryRetry && response.status === 404);
                }
                catch (e) {
                    if (esm_restError_isRestError(e)) {
                        storage_common_dist_esm_log_logger.error(`RetryPolicy: Caught error, message: ${e.message}, code: ${e.code}`);
                        error = e;
                    }
                    else {
                        storage_common_dist_esm_log_logger.error(`RetryPolicy: Caught error, message: ${getErrorMessage(e)}`);
                        throw e;
                    }
                }
                retryAgain = shouldRetry({ isPrimaryRetry, attempt, response, error });
                if (retryAgain) {
                    await utils_common_delay(calculateDelay(isPrimaryRetry, attempt), request.abortSignal, StorageRetryPolicyV2_RETRY_ABORT_ERROR);
                }
                attempt++;
            }
            if (response) {
                return response;
            }
            throw error ?? new esm_restError_RestError("RetryPolicy failed without known error.");
        },
    };
}
//# sourceMappingURL=StorageRetryPolicyV2.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/StorageSharedKeyCredentialPolicyV2.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




/**
 * The programmatic identifier of the storageSharedKeyCredentialPolicy.
 */
const storageSharedKeyCredentialPolicyName = "storageSharedKeyCredentialPolicy";
/**
 * storageSharedKeyCredentialPolicy handles signing requests using storage account keys.
 */
function storageSharedKeyCredentialPolicy(options) {
    function signRequest(request) {
        request.headers.set(constants_HeaderConstants.X_MS_DATE, new Date().toUTCString());
        if (request.body &&
            (typeof request.body === "string" || Buffer.isBuffer(request.body)) &&
            request.body.length > 0) {
            request.headers.set(constants_HeaderConstants.CONTENT_LENGTH, Buffer.byteLength(request.body));
        }
        const stringToSign = [
            request.method.toUpperCase(),
            getHeaderValueToSign(request, constants_HeaderConstants.CONTENT_LANGUAGE),
            getHeaderValueToSign(request, constants_HeaderConstants.CONTENT_ENCODING),
            getHeaderValueToSign(request, constants_HeaderConstants.CONTENT_LENGTH),
            getHeaderValueToSign(request, constants_HeaderConstants.CONTENT_MD5),
            getHeaderValueToSign(request, constants_HeaderConstants.CONTENT_TYPE),
            getHeaderValueToSign(request, constants_HeaderConstants.DATE),
            getHeaderValueToSign(request, constants_HeaderConstants.IF_MODIFIED_SINCE),
            getHeaderValueToSign(request, constants_HeaderConstants.IF_MATCH),
            getHeaderValueToSign(request, constants_HeaderConstants.IF_NONE_MATCH),
            getHeaderValueToSign(request, constants_HeaderConstants.IF_UNMODIFIED_SINCE),
            getHeaderValueToSign(request, constants_HeaderConstants.RANGE),
        ].join("\n") +
            "\n" +
            getCanonicalizedHeadersString(request) +
            getCanonicalizedResourceString(request);
        const signature = (0,external_node_crypto_.createHmac)("sha256", options.accountKey)
            .update(stringToSign, "utf8")
            .digest("base64");
        request.headers.set(constants_HeaderConstants.AUTHORIZATION, `SharedKey ${options.accountName}:${signature}`);
        // console.log(`[URL]:${request.url}`);
        // console.log(`[HEADERS]:${request.headers.toString()}`);
        // console.log(`[STRING TO SIGN]:${JSON.stringify(stringToSign)}`);
        // console.log(`[KEY]: ${request.headers.get(HeaderConstants.AUTHORIZATION)}`);
    }
    /**
     * Retrieve header value according to shared key sign rules.
     * @see https://learn.microsoft.com/rest/api/storageservices/authenticate-with-shared-key
     */
    function getHeaderValueToSign(request, headerName) {
        const value = request.headers.get(headerName);
        if (!value) {
            return "";
        }
        // When using version 2015-02-21 or later, if Content-Length is zero, then
        // set the Content-Length part of the StringToSign to an empty string.
        // https://learn.microsoft.com/rest/api/storageservices/authenticate-with-shared-key
        if (headerName === constants_HeaderConstants.CONTENT_LENGTH && value === "0") {
            return "";
        }
        return value;
    }
    /**
     * To construct the CanonicalizedHeaders portion of the signature string, follow these steps:
     * 1. Retrieve all headers for the resource that begin with x-ms-, including the x-ms-date header.
     * 2. Convert each HTTP header name to lowercase.
     * 3. Sort the headers lexicographically by header name, in ascending order.
     *    Each header may appear only once in the string.
     * 4. Replace any linear whitespace in the header value with a single space.
     * 5. Trim any whitespace around the colon in the header.
     * 6. Finally, append a new-line character to each canonicalized header in the resulting list.
     *    Construct the CanonicalizedHeaders string by concatenating all headers in this list into a single string.
     *
     */
    function getCanonicalizedHeadersString(request) {
        let headersArray = [];
        for (const [name, value] of request.headers) {
            if (name.toLowerCase().startsWith(constants_HeaderConstants.PREFIX_FOR_STORAGE)) {
                headersArray.push({ name, value });
            }
        }
        headersArray.sort((a, b) => {
            return compareHeader(a.name.toLowerCase(), b.name.toLowerCase());
        });
        // Remove duplicate headers
        headersArray = headersArray.filter((value, index, array) => {
            if (index > 0 && value.name.toLowerCase() === array[index - 1].name.toLowerCase()) {
                return false;
            }
            return true;
        });
        let canonicalizedHeadersStringToSign = "";
        headersArray.forEach((header) => {
            canonicalizedHeadersStringToSign += `${header.name
                .toLowerCase()
                .trimRight()}:${header.value.trimLeft()}\n`;
        });
        return canonicalizedHeadersStringToSign;
    }
    function getCanonicalizedResourceString(request) {
        const path = getURLPath(request.url) || "/";
        let canonicalizedResourceString = "";
        canonicalizedResourceString += `/${options.accountName}${path}`;
        const queries = getURLQueries(request.url);
        const lowercaseQueries = {};
        if (queries) {
            const queryKeys = [];
            for (const key in queries) {
                if (Object.prototype.hasOwnProperty.call(queries, key)) {
                    const lowercaseKey = key.toLowerCase();
                    lowercaseQueries[lowercaseKey] = queries[key];
                    queryKeys.push(lowercaseKey);
                }
            }
            queryKeys.sort();
            for (const key of queryKeys) {
                canonicalizedResourceString += `\n${key}:${decodeURIComponent(lowercaseQueries[key])}`;
            }
        }
        return canonicalizedResourceString;
    }
    return {
        name: storageSharedKeyCredentialPolicyName,
        async sendRequest(request, next) {
            signRequest(request);
            return next(request);
        },
    };
}
//# sourceMappingURL=StorageSharedKeyCredentialPolicyV2.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/policies/StorageRequestFailureDetailsParserPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * The programmatic identifier of the StorageRequestFailureDetailsParserPolicy.
 */
const storageRequestFailureDetailsParserPolicyName = "storageRequestFailureDetailsParserPolicy";
/**
 * StorageRequestFailureDetailsParserPolicy
 */
function storageRequestFailureDetailsParserPolicy() {
    return {
        name: storageRequestFailureDetailsParserPolicyName,
        async sendRequest(request, next) {
            try {
                const response = await next(request);
                return response;
            }
            catch (err) {
                if (typeof err === "object" &&
                    err !== null &&
                    err.response &&
                    err.response.parsedBody) {
                    if (err.response.parsedBody.code === "InvalidHeaderValue" &&
                        err.response.parsedBody.HeaderName === "x-ms-version") {
                        err.message =
                            "The provided service version is not enabled on this storage account. Please see https://learn.microsoft.com/rest/api/storageservices/versioning-for-the-azure-storage-services for additional information.\n";
                    }
                }
                throw err;
            }
        },
    };
}
//# sourceMappingURL=StorageRequestFailureDetailsParserPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/credentials/UserDelegationKeyCredential.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * UserDelegationKeyCredential is only used for generation of user delegation SAS.
 * @see https://learn.microsoft.com/rest/api/storageservices/create-user-delegation-sas
 */
class UserDelegationKeyCredential {
    /**
     * Azure Storage account name; readonly.
     */
    accountName;
    /**
     * Azure Storage user delegation key; readonly.
     */
    userDelegationKey;
    /**
     * Key value in Buffer type.
     */
    key;
    /**
     * Creates an instance of UserDelegationKeyCredential.
     * @param accountName -
     * @param userDelegationKey -
     */
    constructor(accountName, userDelegationKey) {
        this.accountName = accountName;
        this.userDelegationKey = userDelegationKey;
        this.key = Buffer.from(userDelegationKey.value, "base64");
    }
    /**
     * Generates a hash signature for an HTTP request or for a SAS.
     *
     * @param stringToSign -
     */
    computeHMACSHA256(stringToSign) {
        // console.log(`stringToSign: ${JSON.stringify(stringToSign)}`);
        return (0,external_node_crypto_.createHmac)("sha256", this.key).update(stringToSign, "utf8").digest("base64");
    }
}
//# sourceMappingURL=UserDelegationKeyCredential.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-common/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


















//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/utils/constants.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
const esm_utils_constants_SDK_VERSION = "12.31.0";
const SERVICE_VERSION = "2026-02-06";
const BLOCK_BLOB_MAX_UPLOAD_BLOB_BYTES = 256 * 1024 * 1024; // 256MB
const BLOCK_BLOB_MAX_STAGE_BLOCK_BYTES = 4000 * 1024 * 1024; // 4000MB
const BLOCK_BLOB_MAX_BLOCKS = 50000;
const DEFAULT_BLOCK_BUFFER_SIZE_BYTES = 8 * 1024 * 1024; // 8MB
const DEFAULT_BLOB_DOWNLOAD_BLOCK_BYTES = 4 * 1024 * 1024; // 4MB
const DEFAULT_MAX_DOWNLOAD_RETRY_REQUESTS = 5;
const REQUEST_TIMEOUT = 100 * 1000; // In ms
/**
 * The OAuth scope to use with Azure Storage.
 */
const StorageOAuthScopes = "https://storage.azure.com/.default";
const utils_constants_URLConstants = {
    Parameters: {
        FORCE_BROWSER_NO_CACHE: "_",
        SIGNATURE: "sig",
        SNAPSHOT: "snapshot",
        VERSIONID: "versionid",
        TIMEOUT: "timeout",
    },
};
const HTTPURLConnection = {
    HTTP_ACCEPTED: 202,
    HTTP_CONFLICT: 409,
    HTTP_NOT_FOUND: 404,
    HTTP_PRECON_FAILED: 412,
    HTTP_RANGE_NOT_SATISFIABLE: 416,
};
const utils_constants_HeaderConstants = {
    AUTHORIZATION: "Authorization",
    AUTHORIZATION_SCHEME: "Bearer",
    CONTENT_ENCODING: "Content-Encoding",
    CONTENT_ID: "Content-ID",
    CONTENT_LANGUAGE: "Content-Language",
    CONTENT_LENGTH: "Content-Length",
    CONTENT_MD5: "Content-Md5",
    CONTENT_TRANSFER_ENCODING: "Content-Transfer-Encoding",
    CONTENT_TYPE: "Content-Type",
    COOKIE: "Cookie",
    DATE: "date",
    IF_MATCH: "if-match",
    IF_MODIFIED_SINCE: "if-modified-since",
    IF_NONE_MATCH: "if-none-match",
    IF_UNMODIFIED_SINCE: "if-unmodified-since",
    PREFIX_FOR_STORAGE: "x-ms-",
    RANGE: "Range",
    USER_AGENT: "User-Agent",
    X_MS_CLIENT_REQUEST_ID: "x-ms-client-request-id",
    X_MS_COPY_SOURCE: "x-ms-copy-source",
    X_MS_DATE: "x-ms-date",
    X_MS_ERROR_CODE: "x-ms-error-code",
    X_MS_VERSION: "x-ms-version",
    X_MS_CopySourceErrorCode: "x-ms-copy-source-error-code",
};
const ETagNone = "";
const ETagAny = "*";
const SIZE_1_MB = 1 * 1024 * 1024;
const BATCH_MAX_REQUEST = 256;
const BATCH_MAX_PAYLOAD_IN_BYTES = 4 * SIZE_1_MB;
const HTTP_LINE_ENDING = "\r\n";
const HTTP_VERSION_1_1 = "HTTP/1.1";
const EncryptionAlgorithmAES25 = "AES256";
const utils_constants_DevelopmentConnectionString = `DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;`;
const StorageBlobLoggingAllowedHeaderNames = [
    "Access-Control-Allow-Origin",
    "Cache-Control",
    "Content-Length",
    "Content-Type",
    "Date",
    "Request-Id",
    "traceparent",
    "Transfer-Encoding",
    "User-Agent",
    "x-ms-client-request-id",
    "x-ms-date",
    "x-ms-error-code",
    "x-ms-request-id",
    "x-ms-return-client-request-id",
    "x-ms-version",
    "Accept-Ranges",
    "Content-Disposition",
    "Content-Encoding",
    "Content-Language",
    "Content-MD5",
    "Content-Range",
    "ETag",
    "Last-Modified",
    "Server",
    "Vary",
    "x-ms-content-crc64",
    "x-ms-copy-action",
    "x-ms-copy-completion-time",
    "x-ms-copy-id",
    "x-ms-copy-progress",
    "x-ms-copy-status",
    "x-ms-has-immutability-policy",
    "x-ms-has-legal-hold",
    "x-ms-lease-state",
    "x-ms-lease-status",
    "x-ms-range",
    "x-ms-request-server-encrypted",
    "x-ms-server-encrypted",
    "x-ms-snapshot",
    "x-ms-source-range",
    "If-Match",
    "If-Modified-Since",
    "If-None-Match",
    "If-Unmodified-Since",
    "x-ms-access-tier",
    "x-ms-access-tier-change-time",
    "x-ms-access-tier-inferred",
    "x-ms-account-kind",
    "x-ms-archive-status",
    "x-ms-blob-append-offset",
    "x-ms-blob-cache-control",
    "x-ms-blob-committed-block-count",
    "x-ms-blob-condition-appendpos",
    "x-ms-blob-condition-maxsize",
    "x-ms-blob-content-disposition",
    "x-ms-blob-content-encoding",
    "x-ms-blob-content-language",
    "x-ms-blob-content-length",
    "x-ms-blob-content-md5",
    "x-ms-blob-content-type",
    "x-ms-blob-public-access",
    "x-ms-blob-sequence-number",
    "x-ms-blob-type",
    "x-ms-copy-destination-snapshot",
    "x-ms-creation-time",
    "x-ms-default-encryption-scope",
    "x-ms-delete-snapshots",
    "x-ms-delete-type-permanent",
    "x-ms-deny-encryption-scope-override",
    "x-ms-encryption-algorithm",
    "x-ms-if-sequence-number-eq",
    "x-ms-if-sequence-number-le",
    "x-ms-if-sequence-number-lt",
    "x-ms-incremental-copy",
    "x-ms-lease-action",
    "x-ms-lease-break-period",
    "x-ms-lease-duration",
    "x-ms-lease-id",
    "x-ms-lease-time",
    "x-ms-page-write",
    "x-ms-proposed-lease-id",
    "x-ms-range-get-content-md5",
    "x-ms-rehydrate-priority",
    "x-ms-sequence-number-action",
    "x-ms-sku-name",
    "x-ms-source-content-md5",
    "x-ms-source-if-match",
    "x-ms-source-if-modified-since",
    "x-ms-source-if-none-match",
    "x-ms-source-if-unmodified-since",
    "x-ms-tag-count",
    "x-ms-encryption-key-sha256",
    "x-ms-copy-source-error-code",
    "x-ms-copy-source-status-code",
    "x-ms-if-tags",
    "x-ms-source-if-tags",
];
const StorageBlobLoggingAllowedQueryParameters = [
    "comp",
    "maxresults",
    "rscc",
    "rscd",
    "rsce",
    "rscl",
    "rsct",
    "se",
    "si",
    "sip",
    "sp",
    "spr",
    "sr",
    "srt",
    "ss",
    "st",
    "sv",
    "include",
    "marker",
    "prefix",
    "copyid",
    "restype",
    "blockid",
    "blocklisttype",
    "delimiter",
    "prevsnapshot",
    "ske",
    "skoid",
    "sks",
    "skt",
    "sktid",
    "skv",
    "snapshot",
];
const BlobUsesCustomerSpecifiedEncryptionMsg = "BlobUsesCustomerSpecifiedEncryption";
const BlobDoesNotUseCustomerSpecifiedEncryption = "BlobDoesNotUseCustomerSpecifiedEncryption";
/// List of ports used for path style addressing.
/// Path style addressing means that storage account is put in URI's Path segment in instead of in host.
const utils_constants_PathStylePorts = [
    "10000",
    "10001",
    "10002",
    "10003",
    "10004",
    "10100",
    "10101",
    "10102",
    "10103",
    "10104",
    "11000",
    "11001",
    "11002",
    "11003",
    "11004",
    "11100",
    "11101",
    "11102",
    "11103",
    "11104",
];
//# sourceMappingURL=constants.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/Pipeline.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.








// Export following interfaces and types for customers who want to implement their
// own RequestPolicy or HTTPClient

/**
 * A helper to decide if a given argument satisfies the Pipeline contract
 * @param pipeline - An argument that may be a Pipeline
 * @returns true when the argument satisfies the Pipeline contract
 */
function isPipelineLike(pipeline) {
    if (!pipeline || typeof pipeline !== "object") {
        return false;
    }
    const castPipeline = pipeline;
    return (Array.isArray(castPipeline.factories) &&
        typeof castPipeline.options === "object" &&
        typeof castPipeline.toServiceClientOptions === "function");
}
/**
 * A Pipeline class containing HTTP request policies.
 * You can create a default Pipeline by calling {@link newPipeline}.
 * Or you can create a Pipeline with your own policies by the constructor of Pipeline.
 *
 * Refer to {@link newPipeline} and provided policies before implementing your
 * customized Pipeline.
 */
class Pipeline {
    /**
     * A list of chained request policy factories.
     */
    factories;
    /**
     * Configures pipeline logger and HTTP client.
     */
    options;
    /**
     * Creates an instance of Pipeline. Customize HTTPClient by implementing IHttpClient interface.
     *
     * @param factories -
     * @param options -
     */
    constructor(factories, options = {}) {
        this.factories = factories;
        this.options = options;
    }
    /**
     * Transfer Pipeline object to ServiceClientOptions object which is required by
     * ServiceClient constructor.
     *
     * @returns The ServiceClientOptions object from this Pipeline.
     */
    toServiceClientOptions() {
        return {
            httpClient: this.options.httpClient,
            requestPolicyFactories: this.factories,
        };
    }
}
/**
 * Creates a new Pipeline object with Credential provided.
 *
 * @param credential -  Such as AnonymousCredential, StorageSharedKeyCredential or any credential from the `@azure/identity` package to authenticate requests to the service. You can also provide an object that implements the TokenCredential interface. If not specified, AnonymousCredential is used.
 * @param pipelineOptions - Optional. Options.
 * @returns A new Pipeline object.
 */
function newPipeline(credential, pipelineOptions = {}) {
    if (!credential) {
        credential = new AnonymousCredential();
    }
    const pipeline = new Pipeline([], pipelineOptions);
    pipeline._credential = credential;
    return pipeline;
}
function processDownlevelPipeline(pipeline) {
    const knownFactoryFunctions = [
        isAnonymousCredential,
        isStorageSharedKeyCredential,
        isCoreHttpBearerTokenFactory,
        isStorageBrowserPolicyFactory,
        isStorageRetryPolicyFactory,
        isStorageTelemetryPolicyFactory,
        isCoreHttpPolicyFactory,
    ];
    if (pipeline.factories.length) {
        const novelFactories = pipeline.factories.filter((factory) => {
            return !knownFactoryFunctions.some((knownFactory) => knownFactory(factory));
        });
        if (novelFactories.length) {
            const hasInjector = novelFactories.some((factory) => isInjectorPolicyFactory(factory));
            // if there are any left over, wrap in a requestPolicyFactoryPolicy
            return {
                wrappedPolicies: createRequestPolicyFactoryPolicy(novelFactories),
                afterRetry: hasInjector,
            };
        }
    }
    return undefined;
}
function getCoreClientOptions(pipeline) {
    const { httpClient: v1Client, ...restOptions } = pipeline.options;
    let httpClient = pipeline._coreHttpClient;
    if (!httpClient) {
        httpClient = v1Client ? convertHttpClient(v1Client) : cache_getCachedDefaultHttpClient();
        pipeline._coreHttpClient = httpClient;
    }
    let corePipeline = pipeline._corePipeline;
    if (!corePipeline) {
        const packageDetails = `azsdk-js-azure-storage-blob/${esm_utils_constants_SDK_VERSION}`;
        const userAgentPrefix = restOptions.userAgentOptions && restOptions.userAgentOptions.userAgentPrefix
            ? `${restOptions.userAgentOptions.userAgentPrefix} ${packageDetails}`
            : `${packageDetails}`;
        corePipeline = createClientPipeline({
            ...restOptions,
            loggingOptions: {
                additionalAllowedHeaderNames: StorageBlobLoggingAllowedHeaderNames,
                additionalAllowedQueryParameters: StorageBlobLoggingAllowedQueryParameters,
                logger: storage_blob_dist_esm_log_logger.info,
            },
            userAgentOptions: {
                userAgentPrefix,
            },
            serializationOptions: {
                stringifyXML: stringifyXML,
                serializerOptions: {
                    xml: {
                        // Use customized XML char key of "#" so we can deserialize metadata
                        // with "_" key
                        xmlCharKey: "#",
                    },
                },
            },
            deserializationOptions: {
                parseXML: parseXML,
                serializerOptions: {
                    xml: {
                        // Use customized XML char key of "#" so we can deserialize metadata
                        // with "_" key
                        xmlCharKey: "#",
                    },
                },
            },
        });
        corePipeline.removePolicy({ phase: "Retry" });
        corePipeline.removePolicy({ name: decompressResponsePolicy_decompressResponsePolicyName });
        corePipeline.addPolicy(storageCorrectContentLengthPolicy());
        corePipeline.addPolicy(storageRetryPolicy(restOptions.retryOptions), { phase: "Retry" });
        corePipeline.addPolicy(storageRequestFailureDetailsParserPolicy());
        corePipeline.addPolicy(storageBrowserPolicy());
        const downlevelResults = processDownlevelPipeline(pipeline);
        if (downlevelResults) {
            corePipeline.addPolicy(downlevelResults.wrappedPolicies, downlevelResults.afterRetry ? { afterPhase: "Retry" } : undefined);
        }
        const credential = getCredentialFromPipeline(pipeline);
        if (isTokenCredential(credential)) {
            corePipeline.addPolicy(bearerTokenAuthenticationPolicy({
                credential,
                scopes: restOptions.audience ?? StorageOAuthScopes,
                challengeCallbacks: { authorizeRequestOnChallenge: authorizeRequestOnTenantChallenge },
            }), { phase: "Sign" });
        }
        else if (credential instanceof StorageSharedKeyCredential) {
            corePipeline.addPolicy(storageSharedKeyCredentialPolicy({
                accountName: credential.accountName,
                accountKey: credential.accountKey,
            }), { phase: "Sign" });
        }
        pipeline._corePipeline = corePipeline;
    }
    return {
        ...restOptions,
        allowInsecureConnection: true,
        httpClient,
        pipeline: corePipeline,
    };
}
function getCredentialFromPipeline(pipeline) {
    // see if we squirreled one away on the type itself
    if (pipeline._credential) {
        return pipeline._credential;
    }
    // if it came from another package, loop over the factories and look for one like before
    let credential = new AnonymousCredential();
    for (const factory of pipeline.factories) {
        if (isTokenCredential(factory.credential)) {
            // Only works if the factory has been attached a "credential" property.
            // We do that in newPipeline() when using TokenCredential.
            credential = factory.credential;
        }
        else if (isStorageSharedKeyCredential(factory)) {
            return factory;
        }
    }
    return credential;
}
function isStorageSharedKeyCredential(factory) {
    if (factory instanceof StorageSharedKeyCredential) {
        return true;
    }
    return factory.constructor.name === "StorageSharedKeyCredential";
}
function isAnonymousCredential(factory) {
    if (factory instanceof AnonymousCredential) {
        return true;
    }
    return factory.constructor.name === "AnonymousCredential";
}
function isCoreHttpBearerTokenFactory(factory) {
    return isTokenCredential(factory.credential);
}
function isStorageBrowserPolicyFactory(factory) {
    if (factory instanceof StorageBrowserPolicyFactory) {
        return true;
    }
    return factory.constructor.name === "StorageBrowserPolicyFactory";
}
function isStorageRetryPolicyFactory(factory) {
    if (factory instanceof StorageRetryPolicyFactory) {
        return true;
    }
    return factory.constructor.name === "StorageRetryPolicyFactory";
}
function isStorageTelemetryPolicyFactory(factory) {
    return factory.constructor.name === "TelemetryPolicyFactory";
}
function isInjectorPolicyFactory(factory) {
    return factory.constructor.name === "InjectorPolicyFactory";
}
function isCoreHttpPolicyFactory(factory) {
    const knownPolicies = [
        "GenerateClientRequestIdPolicy",
        "TracingPolicy",
        "LogPolicy",
        "ProxyPolicy",
        "DisableResponseDecompressionPolicy",
        "KeepAlivePolicy",
        "DeserializationPolicy",
    ];
    const mockHttpClient = {
        sendRequest: async (request) => {
            return {
                request,
                headers: request.headers.clone(),
                status: 500,
            };
        },
    };
    const mockRequestPolicyOptions = {
        log(_logLevel, _message) {
            /* do nothing */
        },
        shouldLog(_logLevel) {
            return false;
        },
    };
    const policyInstance = factory.create(mockHttpClient, mockRequestPolicyOptions);
    const policyName = policyInstance.constructor.name;
    // bundlers sometimes add a custom suffix to the class name to make it unique
    return knownPolicies.some((knownPolicyName) => {
        return policyName.startsWith(knownPolicyName);
    });
}
//# sourceMappingURL=Pipeline.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/models/index.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */
/** Known values of {@link EncryptionAlgorithmType} that the service accepts. */
var KnownEncryptionAlgorithmType;
(function (KnownEncryptionAlgorithmType) {
    /** AES256 */
    KnownEncryptionAlgorithmType["AES256"] = "AES256";
})(KnownEncryptionAlgorithmType || (KnownEncryptionAlgorithmType = {}));
/** Known values of {@link FileShareTokenIntent} that the service accepts. */
var KnownFileShareTokenIntent;
(function (KnownFileShareTokenIntent) {
    /** Backup */
    KnownFileShareTokenIntent["Backup"] = "backup";
})(KnownFileShareTokenIntent || (KnownFileShareTokenIntent = {}));
/** Known values of {@link BlobExpiryOptions} that the service accepts. */
var KnownBlobExpiryOptions;
(function (KnownBlobExpiryOptions) {
    /** NeverExpire */
    KnownBlobExpiryOptions["NeverExpire"] = "NeverExpire";
    /** RelativeToCreation */
    KnownBlobExpiryOptions["RelativeToCreation"] = "RelativeToCreation";
    /** RelativeToNow */
    KnownBlobExpiryOptions["RelativeToNow"] = "RelativeToNow";
    /** Absolute */
    KnownBlobExpiryOptions["Absolute"] = "Absolute";
})(KnownBlobExpiryOptions || (KnownBlobExpiryOptions = {}));
/** Known values of {@link StorageErrorCode} that the service accepts. */
var KnownStorageErrorCode;
(function (KnownStorageErrorCode) {
    /** AccountAlreadyExists */
    KnownStorageErrorCode["AccountAlreadyExists"] = "AccountAlreadyExists";
    /** AccountBeingCreated */
    KnownStorageErrorCode["AccountBeingCreated"] = "AccountBeingCreated";
    /** AccountIsDisabled */
    KnownStorageErrorCode["AccountIsDisabled"] = "AccountIsDisabled";
    /** AuthenticationFailed */
    KnownStorageErrorCode["AuthenticationFailed"] = "AuthenticationFailed";
    /** AuthorizationFailure */
    KnownStorageErrorCode["AuthorizationFailure"] = "AuthorizationFailure";
    /** ConditionHeadersNotSupported */
    KnownStorageErrorCode["ConditionHeadersNotSupported"] = "ConditionHeadersNotSupported";
    /** ConditionNotMet */
    KnownStorageErrorCode["ConditionNotMet"] = "ConditionNotMet";
    /** EmptyMetadataKey */
    KnownStorageErrorCode["EmptyMetadataKey"] = "EmptyMetadataKey";
    /** InsufficientAccountPermissions */
    KnownStorageErrorCode["InsufficientAccountPermissions"] = "InsufficientAccountPermissions";
    /** InternalError */
    KnownStorageErrorCode["InternalError"] = "InternalError";
    /** InvalidAuthenticationInfo */
    KnownStorageErrorCode["InvalidAuthenticationInfo"] = "InvalidAuthenticationInfo";
    /** InvalidHeaderValue */
    KnownStorageErrorCode["InvalidHeaderValue"] = "InvalidHeaderValue";
    /** InvalidHttpVerb */
    KnownStorageErrorCode["InvalidHttpVerb"] = "InvalidHttpVerb";
    /** InvalidInput */
    KnownStorageErrorCode["InvalidInput"] = "InvalidInput";
    /** InvalidMd5 */
    KnownStorageErrorCode["InvalidMd5"] = "InvalidMd5";
    /** InvalidMetadata */
    KnownStorageErrorCode["InvalidMetadata"] = "InvalidMetadata";
    /** InvalidQueryParameterValue */
    KnownStorageErrorCode["InvalidQueryParameterValue"] = "InvalidQueryParameterValue";
    /** InvalidRange */
    KnownStorageErrorCode["InvalidRange"] = "InvalidRange";
    /** InvalidResourceName */
    KnownStorageErrorCode["InvalidResourceName"] = "InvalidResourceName";
    /** InvalidUri */
    KnownStorageErrorCode["InvalidUri"] = "InvalidUri";
    /** InvalidXmlDocument */
    KnownStorageErrorCode["InvalidXmlDocument"] = "InvalidXmlDocument";
    /** InvalidXmlNodeValue */
    KnownStorageErrorCode["InvalidXmlNodeValue"] = "InvalidXmlNodeValue";
    /** Md5Mismatch */
    KnownStorageErrorCode["Md5Mismatch"] = "Md5Mismatch";
    /** MetadataTooLarge */
    KnownStorageErrorCode["MetadataTooLarge"] = "MetadataTooLarge";
    /** MissingContentLengthHeader */
    KnownStorageErrorCode["MissingContentLengthHeader"] = "MissingContentLengthHeader";
    /** MissingRequiredQueryParameter */
    KnownStorageErrorCode["MissingRequiredQueryParameter"] = "MissingRequiredQueryParameter";
    /** MissingRequiredHeader */
    KnownStorageErrorCode["MissingRequiredHeader"] = "MissingRequiredHeader";
    /** MissingRequiredXmlNode */
    KnownStorageErrorCode["MissingRequiredXmlNode"] = "MissingRequiredXmlNode";
    /** MultipleConditionHeadersNotSupported */
    KnownStorageErrorCode["MultipleConditionHeadersNotSupported"] = "MultipleConditionHeadersNotSupported";
    /** OperationTimedOut */
    KnownStorageErrorCode["OperationTimedOut"] = "OperationTimedOut";
    /** OutOfRangeInput */
    KnownStorageErrorCode["OutOfRangeInput"] = "OutOfRangeInput";
    /** OutOfRangeQueryParameterValue */
    KnownStorageErrorCode["OutOfRangeQueryParameterValue"] = "OutOfRangeQueryParameterValue";
    /** RequestBodyTooLarge */
    KnownStorageErrorCode["RequestBodyTooLarge"] = "RequestBodyTooLarge";
    /** ResourceTypeMismatch */
    KnownStorageErrorCode["ResourceTypeMismatch"] = "ResourceTypeMismatch";
    /** RequestUrlFailedToParse */
    KnownStorageErrorCode["RequestUrlFailedToParse"] = "RequestUrlFailedToParse";
    /** ResourceAlreadyExists */
    KnownStorageErrorCode["ResourceAlreadyExists"] = "ResourceAlreadyExists";
    /** ResourceNotFound */
    KnownStorageErrorCode["ResourceNotFound"] = "ResourceNotFound";
    /** ServerBusy */
    KnownStorageErrorCode["ServerBusy"] = "ServerBusy";
    /** UnsupportedHeader */
    KnownStorageErrorCode["UnsupportedHeader"] = "UnsupportedHeader";
    /** UnsupportedXmlNode */
    KnownStorageErrorCode["UnsupportedXmlNode"] = "UnsupportedXmlNode";
    /** UnsupportedQueryParameter */
    KnownStorageErrorCode["UnsupportedQueryParameter"] = "UnsupportedQueryParameter";
    /** UnsupportedHttpVerb */
    KnownStorageErrorCode["UnsupportedHttpVerb"] = "UnsupportedHttpVerb";
    /** AppendPositionConditionNotMet */
    KnownStorageErrorCode["AppendPositionConditionNotMet"] = "AppendPositionConditionNotMet";
    /** BlobAlreadyExists */
    KnownStorageErrorCode["BlobAlreadyExists"] = "BlobAlreadyExists";
    /** BlobImmutableDueToPolicy */
    KnownStorageErrorCode["BlobImmutableDueToPolicy"] = "BlobImmutableDueToPolicy";
    /** BlobNotFound */
    KnownStorageErrorCode["BlobNotFound"] = "BlobNotFound";
    /** BlobOverwritten */
    KnownStorageErrorCode["BlobOverwritten"] = "BlobOverwritten";
    /** BlobTierInadequateForContentLength */
    KnownStorageErrorCode["BlobTierInadequateForContentLength"] = "BlobTierInadequateForContentLength";
    /** BlobUsesCustomerSpecifiedEncryption */
    KnownStorageErrorCode["BlobUsesCustomerSpecifiedEncryption"] = "BlobUsesCustomerSpecifiedEncryption";
    /** BlockCountExceedsLimit */
    KnownStorageErrorCode["BlockCountExceedsLimit"] = "BlockCountExceedsLimit";
    /** BlockListTooLong */
    KnownStorageErrorCode["BlockListTooLong"] = "BlockListTooLong";
    /** CannotChangeToLowerTier */
    KnownStorageErrorCode["CannotChangeToLowerTier"] = "CannotChangeToLowerTier";
    /** CannotVerifyCopySource */
    KnownStorageErrorCode["CannotVerifyCopySource"] = "CannotVerifyCopySource";
    /** ContainerAlreadyExists */
    KnownStorageErrorCode["ContainerAlreadyExists"] = "ContainerAlreadyExists";
    /** ContainerBeingDeleted */
    KnownStorageErrorCode["ContainerBeingDeleted"] = "ContainerBeingDeleted";
    /** ContainerDisabled */
    KnownStorageErrorCode["ContainerDisabled"] = "ContainerDisabled";
    /** ContainerNotFound */
    KnownStorageErrorCode["ContainerNotFound"] = "ContainerNotFound";
    /** ContentLengthLargerThanTierLimit */
    KnownStorageErrorCode["ContentLengthLargerThanTierLimit"] = "ContentLengthLargerThanTierLimit";
    /** CopyAcrossAccountsNotSupported */
    KnownStorageErrorCode["CopyAcrossAccountsNotSupported"] = "CopyAcrossAccountsNotSupported";
    /** CopyIdMismatch */
    KnownStorageErrorCode["CopyIdMismatch"] = "CopyIdMismatch";
    /** FeatureVersionMismatch */
    KnownStorageErrorCode["FeatureVersionMismatch"] = "FeatureVersionMismatch";
    /** IncrementalCopyBlobMismatch */
    KnownStorageErrorCode["IncrementalCopyBlobMismatch"] = "IncrementalCopyBlobMismatch";
    /** IncrementalCopyOfEarlierVersionSnapshotNotAllowed */
    KnownStorageErrorCode["IncrementalCopyOfEarlierVersionSnapshotNotAllowed"] = "IncrementalCopyOfEarlierVersionSnapshotNotAllowed";
    /** IncrementalCopySourceMustBeSnapshot */
    KnownStorageErrorCode["IncrementalCopySourceMustBeSnapshot"] = "IncrementalCopySourceMustBeSnapshot";
    /** InfiniteLeaseDurationRequired */
    KnownStorageErrorCode["InfiniteLeaseDurationRequired"] = "InfiniteLeaseDurationRequired";
    /** InvalidBlobOrBlock */
    KnownStorageErrorCode["InvalidBlobOrBlock"] = "InvalidBlobOrBlock";
    /** InvalidBlobTier */
    KnownStorageErrorCode["InvalidBlobTier"] = "InvalidBlobTier";
    /** InvalidBlobType */
    KnownStorageErrorCode["InvalidBlobType"] = "InvalidBlobType";
    /** InvalidBlockId */
    KnownStorageErrorCode["InvalidBlockId"] = "InvalidBlockId";
    /** InvalidBlockList */
    KnownStorageErrorCode["InvalidBlockList"] = "InvalidBlockList";
    /** InvalidOperation */
    KnownStorageErrorCode["InvalidOperation"] = "InvalidOperation";
    /** InvalidPageRange */
    KnownStorageErrorCode["InvalidPageRange"] = "InvalidPageRange";
    /** InvalidSourceBlobType */
    KnownStorageErrorCode["InvalidSourceBlobType"] = "InvalidSourceBlobType";
    /** InvalidSourceBlobUrl */
    KnownStorageErrorCode["InvalidSourceBlobUrl"] = "InvalidSourceBlobUrl";
    /** InvalidVersionForPageBlobOperation */
    KnownStorageErrorCode["InvalidVersionForPageBlobOperation"] = "InvalidVersionForPageBlobOperation";
    /** LeaseAlreadyPresent */
    KnownStorageErrorCode["LeaseAlreadyPresent"] = "LeaseAlreadyPresent";
    /** LeaseAlreadyBroken */
    KnownStorageErrorCode["LeaseAlreadyBroken"] = "LeaseAlreadyBroken";
    /** LeaseIdMismatchWithBlobOperation */
    KnownStorageErrorCode["LeaseIdMismatchWithBlobOperation"] = "LeaseIdMismatchWithBlobOperation";
    /** LeaseIdMismatchWithContainerOperation */
    KnownStorageErrorCode["LeaseIdMismatchWithContainerOperation"] = "LeaseIdMismatchWithContainerOperation";
    /** LeaseIdMismatchWithLeaseOperation */
    KnownStorageErrorCode["LeaseIdMismatchWithLeaseOperation"] = "LeaseIdMismatchWithLeaseOperation";
    /** LeaseIdMissing */
    KnownStorageErrorCode["LeaseIdMissing"] = "LeaseIdMissing";
    /** LeaseIsBreakingAndCannotBeAcquired */
    KnownStorageErrorCode["LeaseIsBreakingAndCannotBeAcquired"] = "LeaseIsBreakingAndCannotBeAcquired";
    /** LeaseIsBreakingAndCannotBeChanged */
    KnownStorageErrorCode["LeaseIsBreakingAndCannotBeChanged"] = "LeaseIsBreakingAndCannotBeChanged";
    /** LeaseIsBrokenAndCannotBeRenewed */
    KnownStorageErrorCode["LeaseIsBrokenAndCannotBeRenewed"] = "LeaseIsBrokenAndCannotBeRenewed";
    /** LeaseLost */
    KnownStorageErrorCode["LeaseLost"] = "LeaseLost";
    /** LeaseNotPresentWithBlobOperation */
    KnownStorageErrorCode["LeaseNotPresentWithBlobOperation"] = "LeaseNotPresentWithBlobOperation";
    /** LeaseNotPresentWithContainerOperation */
    KnownStorageErrorCode["LeaseNotPresentWithContainerOperation"] = "LeaseNotPresentWithContainerOperation";
    /** LeaseNotPresentWithLeaseOperation */
    KnownStorageErrorCode["LeaseNotPresentWithLeaseOperation"] = "LeaseNotPresentWithLeaseOperation";
    /** MaxBlobSizeConditionNotMet */
    KnownStorageErrorCode["MaxBlobSizeConditionNotMet"] = "MaxBlobSizeConditionNotMet";
    /** NoAuthenticationInformation */
    KnownStorageErrorCode["NoAuthenticationInformation"] = "NoAuthenticationInformation";
    /** NoPendingCopyOperation */
    KnownStorageErrorCode["NoPendingCopyOperation"] = "NoPendingCopyOperation";
    /** OperationNotAllowedOnIncrementalCopyBlob */
    KnownStorageErrorCode["OperationNotAllowedOnIncrementalCopyBlob"] = "OperationNotAllowedOnIncrementalCopyBlob";
    /** PendingCopyOperation */
    KnownStorageErrorCode["PendingCopyOperation"] = "PendingCopyOperation";
    /** PreviousSnapshotCannotBeNewer */
    KnownStorageErrorCode["PreviousSnapshotCannotBeNewer"] = "PreviousSnapshotCannotBeNewer";
    /** PreviousSnapshotNotFound */
    KnownStorageErrorCode["PreviousSnapshotNotFound"] = "PreviousSnapshotNotFound";
    /** PreviousSnapshotOperationNotSupported */
    KnownStorageErrorCode["PreviousSnapshotOperationNotSupported"] = "PreviousSnapshotOperationNotSupported";
    /** SequenceNumberConditionNotMet */
    KnownStorageErrorCode["SequenceNumberConditionNotMet"] = "SequenceNumberConditionNotMet";
    /** SequenceNumberIncrementTooLarge */
    KnownStorageErrorCode["SequenceNumberIncrementTooLarge"] = "SequenceNumberIncrementTooLarge";
    /** SnapshotCountExceeded */
    KnownStorageErrorCode["SnapshotCountExceeded"] = "SnapshotCountExceeded";
    /** SnapshotOperationRateExceeded */
    KnownStorageErrorCode["SnapshotOperationRateExceeded"] = "SnapshotOperationRateExceeded";
    /** SnapshotsPresent */
    KnownStorageErrorCode["SnapshotsPresent"] = "SnapshotsPresent";
    /** SourceConditionNotMet */
    KnownStorageErrorCode["SourceConditionNotMet"] = "SourceConditionNotMet";
    /** SystemInUse */
    KnownStorageErrorCode["SystemInUse"] = "SystemInUse";
    /** TargetConditionNotMet */
    KnownStorageErrorCode["TargetConditionNotMet"] = "TargetConditionNotMet";
    /** UnauthorizedBlobOverwrite */
    KnownStorageErrorCode["UnauthorizedBlobOverwrite"] = "UnauthorizedBlobOverwrite";
    /** BlobBeingRehydrated */
    KnownStorageErrorCode["BlobBeingRehydrated"] = "BlobBeingRehydrated";
    /** BlobArchived */
    KnownStorageErrorCode["BlobArchived"] = "BlobArchived";
    /** BlobNotArchived */
    KnownStorageErrorCode["BlobNotArchived"] = "BlobNotArchived";
    /** AuthorizationSourceIPMismatch */
    KnownStorageErrorCode["AuthorizationSourceIPMismatch"] = "AuthorizationSourceIPMismatch";
    /** AuthorizationProtocolMismatch */
    KnownStorageErrorCode["AuthorizationProtocolMismatch"] = "AuthorizationProtocolMismatch";
    /** AuthorizationPermissionMismatch */
    KnownStorageErrorCode["AuthorizationPermissionMismatch"] = "AuthorizationPermissionMismatch";
    /** AuthorizationServiceMismatch */
    KnownStorageErrorCode["AuthorizationServiceMismatch"] = "AuthorizationServiceMismatch";
    /** AuthorizationResourceTypeMismatch */
    KnownStorageErrorCode["AuthorizationResourceTypeMismatch"] = "AuthorizationResourceTypeMismatch";
    /** BlobAccessTierNotSupportedForAccountType */
    KnownStorageErrorCode["BlobAccessTierNotSupportedForAccountType"] = "BlobAccessTierNotSupportedForAccountType";
})(KnownStorageErrorCode || (KnownStorageErrorCode = {}));
//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/models/mappers.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */
const BlobServiceProperties = {
    serializedName: "BlobServiceProperties",
    xmlName: "StorageServiceProperties",
    type: {
        name: "Composite",
        className: "BlobServiceProperties",
        modelProperties: {
            blobAnalyticsLogging: {
                serializedName: "Logging",
                xmlName: "Logging",
                type: {
                    name: "Composite",
                    className: "Logging",
                },
            },
            hourMetrics: {
                serializedName: "HourMetrics",
                xmlName: "HourMetrics",
                type: {
                    name: "Composite",
                    className: "Metrics",
                },
            },
            minuteMetrics: {
                serializedName: "MinuteMetrics",
                xmlName: "MinuteMetrics",
                type: {
                    name: "Composite",
                    className: "Metrics",
                },
            },
            cors: {
                serializedName: "Cors",
                xmlName: "Cors",
                xmlIsWrapped: true,
                xmlElementName: "CorsRule",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "CorsRule",
                        },
                    },
                },
            },
            defaultServiceVersion: {
                serializedName: "DefaultServiceVersion",
                xmlName: "DefaultServiceVersion",
                type: {
                    name: "String",
                },
            },
            deleteRetentionPolicy: {
                serializedName: "DeleteRetentionPolicy",
                xmlName: "DeleteRetentionPolicy",
                type: {
                    name: "Composite",
                    className: "RetentionPolicy",
                },
            },
            staticWebsite: {
                serializedName: "StaticWebsite",
                xmlName: "StaticWebsite",
                type: {
                    name: "Composite",
                    className: "StaticWebsite",
                },
            },
        },
    },
};
const Logging = {
    serializedName: "Logging",
    type: {
        name: "Composite",
        className: "Logging",
        modelProperties: {
            version: {
                serializedName: "Version",
                required: true,
                xmlName: "Version",
                type: {
                    name: "String",
                },
            },
            deleteProperty: {
                serializedName: "Delete",
                required: true,
                xmlName: "Delete",
                type: {
                    name: "Boolean",
                },
            },
            read: {
                serializedName: "Read",
                required: true,
                xmlName: "Read",
                type: {
                    name: "Boolean",
                },
            },
            write: {
                serializedName: "Write",
                required: true,
                xmlName: "Write",
                type: {
                    name: "Boolean",
                },
            },
            retentionPolicy: {
                serializedName: "RetentionPolicy",
                xmlName: "RetentionPolicy",
                type: {
                    name: "Composite",
                    className: "RetentionPolicy",
                },
            },
        },
    },
};
const RetentionPolicy = {
    serializedName: "RetentionPolicy",
    type: {
        name: "Composite",
        className: "RetentionPolicy",
        modelProperties: {
            enabled: {
                serializedName: "Enabled",
                required: true,
                xmlName: "Enabled",
                type: {
                    name: "Boolean",
                },
            },
            days: {
                constraints: {
                    InclusiveMinimum: 1,
                },
                serializedName: "Days",
                xmlName: "Days",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const Metrics = {
    serializedName: "Metrics",
    type: {
        name: "Composite",
        className: "Metrics",
        modelProperties: {
            version: {
                serializedName: "Version",
                xmlName: "Version",
                type: {
                    name: "String",
                },
            },
            enabled: {
                serializedName: "Enabled",
                required: true,
                xmlName: "Enabled",
                type: {
                    name: "Boolean",
                },
            },
            includeAPIs: {
                serializedName: "IncludeAPIs",
                xmlName: "IncludeAPIs",
                type: {
                    name: "Boolean",
                },
            },
            retentionPolicy: {
                serializedName: "RetentionPolicy",
                xmlName: "RetentionPolicy",
                type: {
                    name: "Composite",
                    className: "RetentionPolicy",
                },
            },
        },
    },
};
const CorsRule = {
    serializedName: "CorsRule",
    type: {
        name: "Composite",
        className: "CorsRule",
        modelProperties: {
            allowedOrigins: {
                serializedName: "AllowedOrigins",
                required: true,
                xmlName: "AllowedOrigins",
                type: {
                    name: "String",
                },
            },
            allowedMethods: {
                serializedName: "AllowedMethods",
                required: true,
                xmlName: "AllowedMethods",
                type: {
                    name: "String",
                },
            },
            allowedHeaders: {
                serializedName: "AllowedHeaders",
                required: true,
                xmlName: "AllowedHeaders",
                type: {
                    name: "String",
                },
            },
            exposedHeaders: {
                serializedName: "ExposedHeaders",
                required: true,
                xmlName: "ExposedHeaders",
                type: {
                    name: "String",
                },
            },
            maxAgeInSeconds: {
                constraints: {
                    InclusiveMinimum: 0,
                },
                serializedName: "MaxAgeInSeconds",
                required: true,
                xmlName: "MaxAgeInSeconds",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const StaticWebsite = {
    serializedName: "StaticWebsite",
    type: {
        name: "Composite",
        className: "StaticWebsite",
        modelProperties: {
            enabled: {
                serializedName: "Enabled",
                required: true,
                xmlName: "Enabled",
                type: {
                    name: "Boolean",
                },
            },
            indexDocument: {
                serializedName: "IndexDocument",
                xmlName: "IndexDocument",
                type: {
                    name: "String",
                },
            },
            errorDocument404Path: {
                serializedName: "ErrorDocument404Path",
                xmlName: "ErrorDocument404Path",
                type: {
                    name: "String",
                },
            },
            defaultIndexDocumentPath: {
                serializedName: "DefaultIndexDocumentPath",
                xmlName: "DefaultIndexDocumentPath",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const StorageError = {
    serializedName: "StorageError",
    type: {
        name: "Composite",
        className: "StorageError",
        modelProperties: {
            message: {
                serializedName: "Message",
                xmlName: "Message",
                type: {
                    name: "String",
                },
            },
            copySourceStatusCode: {
                serializedName: "CopySourceStatusCode",
                xmlName: "CopySourceStatusCode",
                type: {
                    name: "Number",
                },
            },
            copySourceErrorCode: {
                serializedName: "CopySourceErrorCode",
                xmlName: "CopySourceErrorCode",
                type: {
                    name: "String",
                },
            },
            copySourceErrorMessage: {
                serializedName: "CopySourceErrorMessage",
                xmlName: "CopySourceErrorMessage",
                type: {
                    name: "String",
                },
            },
            code: {
                serializedName: "Code",
                xmlName: "Code",
                type: {
                    name: "String",
                },
            },
            authenticationErrorDetail: {
                serializedName: "AuthenticationErrorDetail",
                xmlName: "AuthenticationErrorDetail",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobServiceStatistics = {
    serializedName: "BlobServiceStatistics",
    xmlName: "StorageServiceStats",
    type: {
        name: "Composite",
        className: "BlobServiceStatistics",
        modelProperties: {
            geoReplication: {
                serializedName: "GeoReplication",
                xmlName: "GeoReplication",
                type: {
                    name: "Composite",
                    className: "GeoReplication",
                },
            },
        },
    },
};
const GeoReplication = {
    serializedName: "GeoReplication",
    type: {
        name: "Composite",
        className: "GeoReplication",
        modelProperties: {
            status: {
                serializedName: "Status",
                required: true,
                xmlName: "Status",
                type: {
                    name: "Enum",
                    allowedValues: ["live", "bootstrap", "unavailable"],
                },
            },
            lastSyncOn: {
                serializedName: "LastSyncTime",
                required: true,
                xmlName: "LastSyncTime",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const ListContainersSegmentResponse = {
    serializedName: "ListContainersSegmentResponse",
    xmlName: "EnumerationResults",
    type: {
        name: "Composite",
        className: "ListContainersSegmentResponse",
        modelProperties: {
            serviceEndpoint: {
                serializedName: "ServiceEndpoint",
                required: true,
                xmlName: "ServiceEndpoint",
                xmlIsAttribute: true,
                type: {
                    name: "String",
                },
            },
            prefix: {
                serializedName: "Prefix",
                xmlName: "Prefix",
                type: {
                    name: "String",
                },
            },
            marker: {
                serializedName: "Marker",
                xmlName: "Marker",
                type: {
                    name: "String",
                },
            },
            maxPageSize: {
                serializedName: "MaxResults",
                xmlName: "MaxResults",
                type: {
                    name: "Number",
                },
            },
            containerItems: {
                serializedName: "ContainerItems",
                required: true,
                xmlName: "Containers",
                xmlIsWrapped: true,
                xmlElementName: "Container",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "ContainerItem",
                        },
                    },
                },
            },
            continuationToken: {
                serializedName: "NextMarker",
                xmlName: "NextMarker",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerItem = {
    serializedName: "ContainerItem",
    xmlName: "Container",
    type: {
        name: "Composite",
        className: "ContainerItem",
        modelProperties: {
            name: {
                serializedName: "Name",
                required: true,
                xmlName: "Name",
                type: {
                    name: "String",
                },
            },
            deleted: {
                serializedName: "Deleted",
                xmlName: "Deleted",
                type: {
                    name: "Boolean",
                },
            },
            version: {
                serializedName: "Version",
                xmlName: "Version",
                type: {
                    name: "String",
                },
            },
            properties: {
                serializedName: "Properties",
                xmlName: "Properties",
                type: {
                    name: "Composite",
                    className: "ContainerProperties",
                },
            },
            metadata: {
                serializedName: "Metadata",
                xmlName: "Metadata",
                type: {
                    name: "Dictionary",
                    value: { type: { name: "String" } },
                },
            },
        },
    },
};
const ContainerProperties = {
    serializedName: "ContainerProperties",
    type: {
        name: "Composite",
        className: "ContainerProperties",
        modelProperties: {
            lastModified: {
                serializedName: "Last-Modified",
                required: true,
                xmlName: "Last-Modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            etag: {
                serializedName: "Etag",
                required: true,
                xmlName: "Etag",
                type: {
                    name: "String",
                },
            },
            leaseStatus: {
                serializedName: "LeaseStatus",
                xmlName: "LeaseStatus",
                type: {
                    name: "Enum",
                    allowedValues: ["locked", "unlocked"],
                },
            },
            leaseState: {
                serializedName: "LeaseState",
                xmlName: "LeaseState",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "available",
                        "leased",
                        "expired",
                        "breaking",
                        "broken",
                    ],
                },
            },
            leaseDuration: {
                serializedName: "LeaseDuration",
                xmlName: "LeaseDuration",
                type: {
                    name: "Enum",
                    allowedValues: ["infinite", "fixed"],
                },
            },
            publicAccess: {
                serializedName: "PublicAccess",
                xmlName: "PublicAccess",
                type: {
                    name: "Enum",
                    allowedValues: ["container", "blob"],
                },
            },
            hasImmutabilityPolicy: {
                serializedName: "HasImmutabilityPolicy",
                xmlName: "HasImmutabilityPolicy",
                type: {
                    name: "Boolean",
                },
            },
            hasLegalHold: {
                serializedName: "HasLegalHold",
                xmlName: "HasLegalHold",
                type: {
                    name: "Boolean",
                },
            },
            defaultEncryptionScope: {
                serializedName: "DefaultEncryptionScope",
                xmlName: "DefaultEncryptionScope",
                type: {
                    name: "String",
                },
            },
            preventEncryptionScopeOverride: {
                serializedName: "DenyEncryptionScopeOverride",
                xmlName: "DenyEncryptionScopeOverride",
                type: {
                    name: "Boolean",
                },
            },
            deletedOn: {
                serializedName: "DeletedTime",
                xmlName: "DeletedTime",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            remainingRetentionDays: {
                serializedName: "RemainingRetentionDays",
                xmlName: "RemainingRetentionDays",
                type: {
                    name: "Number",
                },
            },
            isImmutableStorageWithVersioningEnabled: {
                serializedName: "ImmutableStorageWithVersioningEnabled",
                xmlName: "ImmutableStorageWithVersioningEnabled",
                type: {
                    name: "Boolean",
                },
            },
        },
    },
};
const KeyInfo = {
    serializedName: "KeyInfo",
    type: {
        name: "Composite",
        className: "KeyInfo",
        modelProperties: {
            startsOn: {
                serializedName: "Start",
                required: true,
                xmlName: "Start",
                type: {
                    name: "String",
                },
            },
            expiresOn: {
                serializedName: "Expiry",
                required: true,
                xmlName: "Expiry",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const UserDelegationKey = {
    serializedName: "UserDelegationKey",
    type: {
        name: "Composite",
        className: "UserDelegationKey",
        modelProperties: {
            signedObjectId: {
                serializedName: "SignedOid",
                required: true,
                xmlName: "SignedOid",
                type: {
                    name: "String",
                },
            },
            signedTenantId: {
                serializedName: "SignedTid",
                required: true,
                xmlName: "SignedTid",
                type: {
                    name: "String",
                },
            },
            signedStartsOn: {
                serializedName: "SignedStart",
                required: true,
                xmlName: "SignedStart",
                type: {
                    name: "String",
                },
            },
            signedExpiresOn: {
                serializedName: "SignedExpiry",
                required: true,
                xmlName: "SignedExpiry",
                type: {
                    name: "String",
                },
            },
            signedService: {
                serializedName: "SignedService",
                required: true,
                xmlName: "SignedService",
                type: {
                    name: "String",
                },
            },
            signedVersion: {
                serializedName: "SignedVersion",
                required: true,
                xmlName: "SignedVersion",
                type: {
                    name: "String",
                },
            },
            value: {
                serializedName: "Value",
                required: true,
                xmlName: "Value",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const FilterBlobSegment = {
    serializedName: "FilterBlobSegment",
    xmlName: "EnumerationResults",
    type: {
        name: "Composite",
        className: "FilterBlobSegment",
        modelProperties: {
            serviceEndpoint: {
                serializedName: "ServiceEndpoint",
                required: true,
                xmlName: "ServiceEndpoint",
                xmlIsAttribute: true,
                type: {
                    name: "String",
                },
            },
            where: {
                serializedName: "Where",
                required: true,
                xmlName: "Where",
                type: {
                    name: "String",
                },
            },
            blobs: {
                serializedName: "Blobs",
                required: true,
                xmlName: "Blobs",
                xmlIsWrapped: true,
                xmlElementName: "Blob",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "FilterBlobItem",
                        },
                    },
                },
            },
            continuationToken: {
                serializedName: "NextMarker",
                xmlName: "NextMarker",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const FilterBlobItem = {
    serializedName: "FilterBlobItem",
    xmlName: "Blob",
    type: {
        name: "Composite",
        className: "FilterBlobItem",
        modelProperties: {
            name: {
                serializedName: "Name",
                required: true,
                xmlName: "Name",
                type: {
                    name: "String",
                },
            },
            containerName: {
                serializedName: "ContainerName",
                required: true,
                xmlName: "ContainerName",
                type: {
                    name: "String",
                },
            },
            tags: {
                serializedName: "Tags",
                xmlName: "Tags",
                type: {
                    name: "Composite",
                    className: "BlobTags",
                },
            },
        },
    },
};
const BlobTags = {
    serializedName: "BlobTags",
    xmlName: "Tags",
    type: {
        name: "Composite",
        className: "BlobTags",
        modelProperties: {
            blobTagSet: {
                serializedName: "BlobTagSet",
                required: true,
                xmlName: "TagSet",
                xmlIsWrapped: true,
                xmlElementName: "Tag",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "BlobTag",
                        },
                    },
                },
            },
        },
    },
};
const BlobTag = {
    serializedName: "BlobTag",
    xmlName: "Tag",
    type: {
        name: "Composite",
        className: "BlobTag",
        modelProperties: {
            key: {
                serializedName: "Key",
                required: true,
                xmlName: "Key",
                type: {
                    name: "String",
                },
            },
            value: {
                serializedName: "Value",
                required: true,
                xmlName: "Value",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const SignedIdentifier = {
    serializedName: "SignedIdentifier",
    xmlName: "SignedIdentifier",
    type: {
        name: "Composite",
        className: "SignedIdentifier",
        modelProperties: {
            id: {
                serializedName: "Id",
                required: true,
                xmlName: "Id",
                type: {
                    name: "String",
                },
            },
            accessPolicy: {
                serializedName: "AccessPolicy",
                xmlName: "AccessPolicy",
                type: {
                    name: "Composite",
                    className: "AccessPolicy",
                },
            },
        },
    },
};
const AccessPolicy = {
    serializedName: "AccessPolicy",
    type: {
        name: "Composite",
        className: "AccessPolicy",
        modelProperties: {
            startsOn: {
                serializedName: "Start",
                xmlName: "Start",
                type: {
                    name: "String",
                },
            },
            expiresOn: {
                serializedName: "Expiry",
                xmlName: "Expiry",
                type: {
                    name: "String",
                },
            },
            permissions: {
                serializedName: "Permission",
                xmlName: "Permission",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ListBlobsFlatSegmentResponse = {
    serializedName: "ListBlobsFlatSegmentResponse",
    xmlName: "EnumerationResults",
    type: {
        name: "Composite",
        className: "ListBlobsFlatSegmentResponse",
        modelProperties: {
            serviceEndpoint: {
                serializedName: "ServiceEndpoint",
                required: true,
                xmlName: "ServiceEndpoint",
                xmlIsAttribute: true,
                type: {
                    name: "String",
                },
            },
            containerName: {
                serializedName: "ContainerName",
                required: true,
                xmlName: "ContainerName",
                xmlIsAttribute: true,
                type: {
                    name: "String",
                },
            },
            prefix: {
                serializedName: "Prefix",
                xmlName: "Prefix",
                type: {
                    name: "String",
                },
            },
            marker: {
                serializedName: "Marker",
                xmlName: "Marker",
                type: {
                    name: "String",
                },
            },
            maxPageSize: {
                serializedName: "MaxResults",
                xmlName: "MaxResults",
                type: {
                    name: "Number",
                },
            },
            segment: {
                serializedName: "Segment",
                xmlName: "Blobs",
                type: {
                    name: "Composite",
                    className: "BlobFlatListSegment",
                },
            },
            continuationToken: {
                serializedName: "NextMarker",
                xmlName: "NextMarker",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobFlatListSegment = {
    serializedName: "BlobFlatListSegment",
    xmlName: "Blobs",
    type: {
        name: "Composite",
        className: "BlobFlatListSegment",
        modelProperties: {
            blobItems: {
                serializedName: "BlobItems",
                required: true,
                xmlName: "BlobItems",
                xmlElementName: "Blob",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "BlobItemInternal",
                        },
                    },
                },
            },
        },
    },
};
const BlobItemInternal = {
    serializedName: "BlobItemInternal",
    xmlName: "Blob",
    type: {
        name: "Composite",
        className: "BlobItemInternal",
        modelProperties: {
            name: {
                serializedName: "Name",
                xmlName: "Name",
                type: {
                    name: "Composite",
                    className: "BlobName",
                },
            },
            deleted: {
                serializedName: "Deleted",
                required: true,
                xmlName: "Deleted",
                type: {
                    name: "Boolean",
                },
            },
            snapshot: {
                serializedName: "Snapshot",
                required: true,
                xmlName: "Snapshot",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "VersionId",
                xmlName: "VersionId",
                type: {
                    name: "String",
                },
            },
            isCurrentVersion: {
                serializedName: "IsCurrentVersion",
                xmlName: "IsCurrentVersion",
                type: {
                    name: "Boolean",
                },
            },
            properties: {
                serializedName: "Properties",
                xmlName: "Properties",
                type: {
                    name: "Composite",
                    className: "BlobPropertiesInternal",
                },
            },
            metadata: {
                serializedName: "Metadata",
                xmlName: "Metadata",
                type: {
                    name: "Dictionary",
                    value: { type: { name: "String" } },
                },
            },
            blobTags: {
                serializedName: "BlobTags",
                xmlName: "Tags",
                type: {
                    name: "Composite",
                    className: "BlobTags",
                },
            },
            objectReplicationMetadata: {
                serializedName: "ObjectReplicationMetadata",
                xmlName: "OrMetadata",
                type: {
                    name: "Dictionary",
                    value: { type: { name: "String" } },
                },
            },
            hasVersionsOnly: {
                serializedName: "HasVersionsOnly",
                xmlName: "HasVersionsOnly",
                type: {
                    name: "Boolean",
                },
            },
        },
    },
};
const BlobName = {
    serializedName: "BlobName",
    type: {
        name: "Composite",
        className: "BlobName",
        modelProperties: {
            encoded: {
                serializedName: "Encoded",
                xmlName: "Encoded",
                xmlIsAttribute: true,
                type: {
                    name: "Boolean",
                },
            },
            content: {
                serializedName: "content",
                xmlName: "content",
                xmlIsMsText: true,
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobPropertiesInternal = {
    serializedName: "BlobPropertiesInternal",
    xmlName: "Properties",
    type: {
        name: "Composite",
        className: "BlobPropertiesInternal",
        modelProperties: {
            createdOn: {
                serializedName: "Creation-Time",
                xmlName: "Creation-Time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            lastModified: {
                serializedName: "Last-Modified",
                required: true,
                xmlName: "Last-Modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            etag: {
                serializedName: "Etag",
                required: true,
                xmlName: "Etag",
                type: {
                    name: "String",
                },
            },
            contentLength: {
                serializedName: "Content-Length",
                xmlName: "Content-Length",
                type: {
                    name: "Number",
                },
            },
            contentType: {
                serializedName: "Content-Type",
                xmlName: "Content-Type",
                type: {
                    name: "String",
                },
            },
            contentEncoding: {
                serializedName: "Content-Encoding",
                xmlName: "Content-Encoding",
                type: {
                    name: "String",
                },
            },
            contentLanguage: {
                serializedName: "Content-Language",
                xmlName: "Content-Language",
                type: {
                    name: "String",
                },
            },
            contentMD5: {
                serializedName: "Content-MD5",
                xmlName: "Content-MD5",
                type: {
                    name: "ByteArray",
                },
            },
            contentDisposition: {
                serializedName: "Content-Disposition",
                xmlName: "Content-Disposition",
                type: {
                    name: "String",
                },
            },
            cacheControl: {
                serializedName: "Cache-Control",
                xmlName: "Cache-Control",
                type: {
                    name: "String",
                },
            },
            blobSequenceNumber: {
                serializedName: "x-ms-blob-sequence-number",
                xmlName: "x-ms-blob-sequence-number",
                type: {
                    name: "Number",
                },
            },
            blobType: {
                serializedName: "BlobType",
                xmlName: "BlobType",
                type: {
                    name: "Enum",
                    allowedValues: ["BlockBlob", "PageBlob", "AppendBlob"],
                },
            },
            leaseStatus: {
                serializedName: "LeaseStatus",
                xmlName: "LeaseStatus",
                type: {
                    name: "Enum",
                    allowedValues: ["locked", "unlocked"],
                },
            },
            leaseState: {
                serializedName: "LeaseState",
                xmlName: "LeaseState",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "available",
                        "leased",
                        "expired",
                        "breaking",
                        "broken",
                    ],
                },
            },
            leaseDuration: {
                serializedName: "LeaseDuration",
                xmlName: "LeaseDuration",
                type: {
                    name: "Enum",
                    allowedValues: ["infinite", "fixed"],
                },
            },
            copyId: {
                serializedName: "CopyId",
                xmlName: "CopyId",
                type: {
                    name: "String",
                },
            },
            copyStatus: {
                serializedName: "CopyStatus",
                xmlName: "CopyStatus",
                type: {
                    name: "Enum",
                    allowedValues: ["pending", "success", "aborted", "failed"],
                },
            },
            copySource: {
                serializedName: "CopySource",
                xmlName: "CopySource",
                type: {
                    name: "String",
                },
            },
            copyProgress: {
                serializedName: "CopyProgress",
                xmlName: "CopyProgress",
                type: {
                    name: "String",
                },
            },
            copyCompletedOn: {
                serializedName: "CopyCompletionTime",
                xmlName: "CopyCompletionTime",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            copyStatusDescription: {
                serializedName: "CopyStatusDescription",
                xmlName: "CopyStatusDescription",
                type: {
                    name: "String",
                },
            },
            serverEncrypted: {
                serializedName: "ServerEncrypted",
                xmlName: "ServerEncrypted",
                type: {
                    name: "Boolean",
                },
            },
            incrementalCopy: {
                serializedName: "IncrementalCopy",
                xmlName: "IncrementalCopy",
                type: {
                    name: "Boolean",
                },
            },
            destinationSnapshot: {
                serializedName: "DestinationSnapshot",
                xmlName: "DestinationSnapshot",
                type: {
                    name: "String",
                },
            },
            deletedOn: {
                serializedName: "DeletedTime",
                xmlName: "DeletedTime",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            remainingRetentionDays: {
                serializedName: "RemainingRetentionDays",
                xmlName: "RemainingRetentionDays",
                type: {
                    name: "Number",
                },
            },
            accessTier: {
                serializedName: "AccessTier",
                xmlName: "AccessTier",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "P4",
                        "P6",
                        "P10",
                        "P15",
                        "P20",
                        "P30",
                        "P40",
                        "P50",
                        "P60",
                        "P70",
                        "P80",
                        "Hot",
                        "Cool",
                        "Archive",
                        "Cold",
                    ],
                },
            },
            accessTierInferred: {
                serializedName: "AccessTierInferred",
                xmlName: "AccessTierInferred",
                type: {
                    name: "Boolean",
                },
            },
            archiveStatus: {
                serializedName: "ArchiveStatus",
                xmlName: "ArchiveStatus",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "rehydrate-pending-to-hot",
                        "rehydrate-pending-to-cool",
                        "rehydrate-pending-to-cold",
                    ],
                },
            },
            customerProvidedKeySha256: {
                serializedName: "CustomerProvidedKeySha256",
                xmlName: "CustomerProvidedKeySha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "EncryptionScope",
                xmlName: "EncryptionScope",
                type: {
                    name: "String",
                },
            },
            accessTierChangedOn: {
                serializedName: "AccessTierChangeTime",
                xmlName: "AccessTierChangeTime",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            tagCount: {
                serializedName: "TagCount",
                xmlName: "TagCount",
                type: {
                    name: "Number",
                },
            },
            expiresOn: {
                serializedName: "Expiry-Time",
                xmlName: "Expiry-Time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isSealed: {
                serializedName: "Sealed",
                xmlName: "Sealed",
                type: {
                    name: "Boolean",
                },
            },
            rehydratePriority: {
                serializedName: "RehydratePriority",
                xmlName: "RehydratePriority",
                type: {
                    name: "Enum",
                    allowedValues: ["High", "Standard"],
                },
            },
            lastAccessedOn: {
                serializedName: "LastAccessTime",
                xmlName: "LastAccessTime",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            immutabilityPolicyExpiresOn: {
                serializedName: "ImmutabilityPolicyUntilDate",
                xmlName: "ImmutabilityPolicyUntilDate",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            immutabilityPolicyMode: {
                serializedName: "ImmutabilityPolicyMode",
                xmlName: "ImmutabilityPolicyMode",
                type: {
                    name: "Enum",
                    allowedValues: ["Mutable", "Unlocked", "Locked"],
                },
            },
            legalHold: {
                serializedName: "LegalHold",
                xmlName: "LegalHold",
                type: {
                    name: "Boolean",
                },
            },
        },
    },
};
const ListBlobsHierarchySegmentResponse = {
    serializedName: "ListBlobsHierarchySegmentResponse",
    xmlName: "EnumerationResults",
    type: {
        name: "Composite",
        className: "ListBlobsHierarchySegmentResponse",
        modelProperties: {
            serviceEndpoint: {
                serializedName: "ServiceEndpoint",
                required: true,
                xmlName: "ServiceEndpoint",
                xmlIsAttribute: true,
                type: {
                    name: "String",
                },
            },
            containerName: {
                serializedName: "ContainerName",
                required: true,
                xmlName: "ContainerName",
                xmlIsAttribute: true,
                type: {
                    name: "String",
                },
            },
            prefix: {
                serializedName: "Prefix",
                xmlName: "Prefix",
                type: {
                    name: "String",
                },
            },
            marker: {
                serializedName: "Marker",
                xmlName: "Marker",
                type: {
                    name: "String",
                },
            },
            maxPageSize: {
                serializedName: "MaxResults",
                xmlName: "MaxResults",
                type: {
                    name: "Number",
                },
            },
            delimiter: {
                serializedName: "Delimiter",
                xmlName: "Delimiter",
                type: {
                    name: "String",
                },
            },
            segment: {
                serializedName: "Segment",
                xmlName: "Blobs",
                type: {
                    name: "Composite",
                    className: "BlobHierarchyListSegment",
                },
            },
            continuationToken: {
                serializedName: "NextMarker",
                xmlName: "NextMarker",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobHierarchyListSegment = {
    serializedName: "BlobHierarchyListSegment",
    xmlName: "Blobs",
    type: {
        name: "Composite",
        className: "BlobHierarchyListSegment",
        modelProperties: {
            blobPrefixes: {
                serializedName: "BlobPrefixes",
                xmlName: "BlobPrefixes",
                xmlElementName: "BlobPrefix",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "BlobPrefix",
                        },
                    },
                },
            },
            blobItems: {
                serializedName: "BlobItems",
                required: true,
                xmlName: "BlobItems",
                xmlElementName: "Blob",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "BlobItemInternal",
                        },
                    },
                },
            },
        },
    },
};
const BlobPrefix = {
    serializedName: "BlobPrefix",
    type: {
        name: "Composite",
        className: "BlobPrefix",
        modelProperties: {
            name: {
                serializedName: "Name",
                xmlName: "Name",
                type: {
                    name: "Composite",
                    className: "BlobName",
                },
            },
        },
    },
};
const BlockLookupList = {
    serializedName: "BlockLookupList",
    xmlName: "BlockList",
    type: {
        name: "Composite",
        className: "BlockLookupList",
        modelProperties: {
            committed: {
                serializedName: "Committed",
                xmlName: "Committed",
                xmlElementName: "Committed",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "String",
                        },
                    },
                },
            },
            uncommitted: {
                serializedName: "Uncommitted",
                xmlName: "Uncommitted",
                xmlElementName: "Uncommitted",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "String",
                        },
                    },
                },
            },
            latest: {
                serializedName: "Latest",
                xmlName: "Latest",
                xmlElementName: "Latest",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "String",
                        },
                    },
                },
            },
        },
    },
};
const BlockList = {
    serializedName: "BlockList",
    type: {
        name: "Composite",
        className: "BlockList",
        modelProperties: {
            committedBlocks: {
                serializedName: "CommittedBlocks",
                xmlName: "CommittedBlocks",
                xmlIsWrapped: true,
                xmlElementName: "Block",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "Block",
                        },
                    },
                },
            },
            uncommittedBlocks: {
                serializedName: "UncommittedBlocks",
                xmlName: "UncommittedBlocks",
                xmlIsWrapped: true,
                xmlElementName: "Block",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "Block",
                        },
                    },
                },
            },
        },
    },
};
const Block = {
    serializedName: "Block",
    type: {
        name: "Composite",
        className: "Block",
        modelProperties: {
            name: {
                serializedName: "Name",
                required: true,
                xmlName: "Name",
                type: {
                    name: "String",
                },
            },
            size: {
                serializedName: "Size",
                required: true,
                xmlName: "Size",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const PageList = {
    serializedName: "PageList",
    type: {
        name: "Composite",
        className: "PageList",
        modelProperties: {
            pageRange: {
                serializedName: "PageRange",
                xmlName: "PageRange",
                xmlElementName: "PageRange",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "PageRange",
                        },
                    },
                },
            },
            clearRange: {
                serializedName: "ClearRange",
                xmlName: "ClearRange",
                xmlElementName: "ClearRange",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "ClearRange",
                        },
                    },
                },
            },
            continuationToken: {
                serializedName: "NextMarker",
                xmlName: "NextMarker",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageRange = {
    serializedName: "PageRange",
    xmlName: "PageRange",
    type: {
        name: "Composite",
        className: "PageRange",
        modelProperties: {
            start: {
                serializedName: "Start",
                required: true,
                xmlName: "Start",
                type: {
                    name: "Number",
                },
            },
            end: {
                serializedName: "End",
                required: true,
                xmlName: "End",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const ClearRange = {
    serializedName: "ClearRange",
    xmlName: "ClearRange",
    type: {
        name: "Composite",
        className: "ClearRange",
        modelProperties: {
            start: {
                serializedName: "Start",
                required: true,
                xmlName: "Start",
                type: {
                    name: "Number",
                },
            },
            end: {
                serializedName: "End",
                required: true,
                xmlName: "End",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const QueryRequest = {
    serializedName: "QueryRequest",
    xmlName: "QueryRequest",
    type: {
        name: "Composite",
        className: "QueryRequest",
        modelProperties: {
            queryType: {
                serializedName: "QueryType",
                required: true,
                xmlName: "QueryType",
                type: {
                    name: "String",
                },
            },
            expression: {
                serializedName: "Expression",
                required: true,
                xmlName: "Expression",
                type: {
                    name: "String",
                },
            },
            inputSerialization: {
                serializedName: "InputSerialization",
                xmlName: "InputSerialization",
                type: {
                    name: "Composite",
                    className: "QuerySerialization",
                },
            },
            outputSerialization: {
                serializedName: "OutputSerialization",
                xmlName: "OutputSerialization",
                type: {
                    name: "Composite",
                    className: "QuerySerialization",
                },
            },
        },
    },
};
const QuerySerialization = {
    serializedName: "QuerySerialization",
    type: {
        name: "Composite",
        className: "QuerySerialization",
        modelProperties: {
            format: {
                serializedName: "Format",
                xmlName: "Format",
                type: {
                    name: "Composite",
                    className: "QueryFormat",
                },
            },
        },
    },
};
const QueryFormat = {
    serializedName: "QueryFormat",
    type: {
        name: "Composite",
        className: "QueryFormat",
        modelProperties: {
            type: {
                serializedName: "Type",
                required: true,
                xmlName: "Type",
                type: {
                    name: "Enum",
                    allowedValues: ["delimited", "json", "arrow", "parquet"],
                },
            },
            delimitedTextConfiguration: {
                serializedName: "DelimitedTextConfiguration",
                xmlName: "DelimitedTextConfiguration",
                type: {
                    name: "Composite",
                    className: "DelimitedTextConfiguration",
                },
            },
            jsonTextConfiguration: {
                serializedName: "JsonTextConfiguration",
                xmlName: "JsonTextConfiguration",
                type: {
                    name: "Composite",
                    className: "JsonTextConfiguration",
                },
            },
            arrowConfiguration: {
                serializedName: "ArrowConfiguration",
                xmlName: "ArrowConfiguration",
                type: {
                    name: "Composite",
                    className: "ArrowConfiguration",
                },
            },
            parquetTextConfiguration: {
                serializedName: "ParquetTextConfiguration",
                xmlName: "ParquetTextConfiguration",
                type: {
                    name: "Dictionary",
                    value: { type: { name: "any" } },
                },
            },
        },
    },
};
const DelimitedTextConfiguration = {
    serializedName: "DelimitedTextConfiguration",
    xmlName: "DelimitedTextConfiguration",
    type: {
        name: "Composite",
        className: "DelimitedTextConfiguration",
        modelProperties: {
            columnSeparator: {
                serializedName: "ColumnSeparator",
                xmlName: "ColumnSeparator",
                type: {
                    name: "String",
                },
            },
            fieldQuote: {
                serializedName: "FieldQuote",
                xmlName: "FieldQuote",
                type: {
                    name: "String",
                },
            },
            recordSeparator: {
                serializedName: "RecordSeparator",
                xmlName: "RecordSeparator",
                type: {
                    name: "String",
                },
            },
            escapeChar: {
                serializedName: "EscapeChar",
                xmlName: "EscapeChar",
                type: {
                    name: "String",
                },
            },
            headersPresent: {
                serializedName: "HeadersPresent",
                xmlName: "HasHeaders",
                type: {
                    name: "Boolean",
                },
            },
        },
    },
};
const JsonTextConfiguration = {
    serializedName: "JsonTextConfiguration",
    xmlName: "JsonTextConfiguration",
    type: {
        name: "Composite",
        className: "JsonTextConfiguration",
        modelProperties: {
            recordSeparator: {
                serializedName: "RecordSeparator",
                xmlName: "RecordSeparator",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ArrowConfiguration = {
    serializedName: "ArrowConfiguration",
    xmlName: "ArrowConfiguration",
    type: {
        name: "Composite",
        className: "ArrowConfiguration",
        modelProperties: {
            schema: {
                serializedName: "Schema",
                required: true,
                xmlName: "Schema",
                xmlIsWrapped: true,
                xmlElementName: "Field",
                type: {
                    name: "Sequence",
                    element: {
                        type: {
                            name: "Composite",
                            className: "ArrowField",
                        },
                    },
                },
            },
        },
    },
};
const ArrowField = {
    serializedName: "ArrowField",
    xmlName: "Field",
    type: {
        name: "Composite",
        className: "ArrowField",
        modelProperties: {
            type: {
                serializedName: "Type",
                required: true,
                xmlName: "Type",
                type: {
                    name: "String",
                },
            },
            name: {
                serializedName: "Name",
                xmlName: "Name",
                type: {
                    name: "String",
                },
            },
            precision: {
                serializedName: "Precision",
                xmlName: "Precision",
                type: {
                    name: "Number",
                },
            },
            scale: {
                serializedName: "Scale",
                xmlName: "Scale",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const ServiceSetPropertiesHeaders = {
    serializedName: "Service_setPropertiesHeaders",
    type: {
        name: "Composite",
        className: "ServiceSetPropertiesHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceSetPropertiesExceptionHeaders = {
    serializedName: "Service_setPropertiesExceptionHeaders",
    type: {
        name: "Composite",
        className: "ServiceSetPropertiesExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceGetPropertiesHeaders = {
    serializedName: "Service_getPropertiesHeaders",
    type: {
        name: "Composite",
        className: "ServiceGetPropertiesHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceGetPropertiesExceptionHeaders = {
    serializedName: "Service_getPropertiesExceptionHeaders",
    type: {
        name: "Composite",
        className: "ServiceGetPropertiesExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceGetStatisticsHeaders = {
    serializedName: "Service_getStatisticsHeaders",
    type: {
        name: "Composite",
        className: "ServiceGetStatisticsHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceGetStatisticsExceptionHeaders = {
    serializedName: "Service_getStatisticsExceptionHeaders",
    type: {
        name: "Composite",
        className: "ServiceGetStatisticsExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceListContainersSegmentHeaders = {
    serializedName: "Service_listContainersSegmentHeaders",
    type: {
        name: "Composite",
        className: "ServiceListContainersSegmentHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceListContainersSegmentExceptionHeaders = {
    serializedName: "Service_listContainersSegmentExceptionHeaders",
    type: {
        name: "Composite",
        className: "ServiceListContainersSegmentExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceGetUserDelegationKeyHeaders = {
    serializedName: "Service_getUserDelegationKeyHeaders",
    type: {
        name: "Composite",
        className: "ServiceGetUserDelegationKeyHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceGetUserDelegationKeyExceptionHeaders = {
    serializedName: "Service_getUserDelegationKeyExceptionHeaders",
    type: {
        name: "Composite",
        className: "ServiceGetUserDelegationKeyExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceGetAccountInfoHeaders = {
    serializedName: "Service_getAccountInfoHeaders",
    type: {
        name: "Composite",
        className: "ServiceGetAccountInfoHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            skuName: {
                serializedName: "x-ms-sku-name",
                xmlName: "x-ms-sku-name",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "Standard_LRS",
                        "Standard_GRS",
                        "Standard_RAGRS",
                        "Standard_ZRS",
                        "Premium_LRS",
                    ],
                },
            },
            accountKind: {
                serializedName: "x-ms-account-kind",
                xmlName: "x-ms-account-kind",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "Storage",
                        "BlobStorage",
                        "StorageV2",
                        "FileStorage",
                        "BlockBlobStorage",
                    ],
                },
            },
            isHierarchicalNamespaceEnabled: {
                serializedName: "x-ms-is-hns-enabled",
                xmlName: "x-ms-is-hns-enabled",
                type: {
                    name: "Boolean",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceGetAccountInfoExceptionHeaders = {
    serializedName: "Service_getAccountInfoExceptionHeaders",
    type: {
        name: "Composite",
        className: "ServiceGetAccountInfoExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceSubmitBatchHeaders = {
    serializedName: "Service_submitBatchHeaders",
    type: {
        name: "Composite",
        className: "ServiceSubmitBatchHeaders",
        modelProperties: {
            contentType: {
                serializedName: "content-type",
                xmlName: "content-type",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceSubmitBatchExceptionHeaders = {
    serializedName: "Service_submitBatchExceptionHeaders",
    type: {
        name: "Composite",
        className: "ServiceSubmitBatchExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceFilterBlobsHeaders = {
    serializedName: "Service_filterBlobsHeaders",
    type: {
        name: "Composite",
        className: "ServiceFilterBlobsHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ServiceFilterBlobsExceptionHeaders = {
    serializedName: "Service_filterBlobsExceptionHeaders",
    type: {
        name: "Composite",
        className: "ServiceFilterBlobsExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerCreateHeaders = {
    serializedName: "Container_createHeaders",
    type: {
        name: "Composite",
        className: "ContainerCreateHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerCreateExceptionHeaders = {
    serializedName: "Container_createExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerCreateExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerGetPropertiesHeaders = {
    serializedName: "Container_getPropertiesHeaders",
    type: {
        name: "Composite",
        className: "ContainerGetPropertiesHeaders",
        modelProperties: {
            metadata: {
                serializedName: "x-ms-meta",
                headerCollectionPrefix: "x-ms-meta-",
                xmlName: "x-ms-meta",
                type: {
                    name: "Dictionary",
                    value: { type: { name: "String" } },
                },
            },
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            leaseDuration: {
                serializedName: "x-ms-lease-duration",
                xmlName: "x-ms-lease-duration",
                type: {
                    name: "Enum",
                    allowedValues: ["infinite", "fixed"],
                },
            },
            leaseState: {
                serializedName: "x-ms-lease-state",
                xmlName: "x-ms-lease-state",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "available",
                        "leased",
                        "expired",
                        "breaking",
                        "broken",
                    ],
                },
            },
            leaseStatus: {
                serializedName: "x-ms-lease-status",
                xmlName: "x-ms-lease-status",
                type: {
                    name: "Enum",
                    allowedValues: ["locked", "unlocked"],
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            blobPublicAccess: {
                serializedName: "x-ms-blob-public-access",
                xmlName: "x-ms-blob-public-access",
                type: {
                    name: "Enum",
                    allowedValues: ["container", "blob"],
                },
            },
            hasImmutabilityPolicy: {
                serializedName: "x-ms-has-immutability-policy",
                xmlName: "x-ms-has-immutability-policy",
                type: {
                    name: "Boolean",
                },
            },
            hasLegalHold: {
                serializedName: "x-ms-has-legal-hold",
                xmlName: "x-ms-has-legal-hold",
                type: {
                    name: "Boolean",
                },
            },
            defaultEncryptionScope: {
                serializedName: "x-ms-default-encryption-scope",
                xmlName: "x-ms-default-encryption-scope",
                type: {
                    name: "String",
                },
            },
            denyEncryptionScopeOverride: {
                serializedName: "x-ms-deny-encryption-scope-override",
                xmlName: "x-ms-deny-encryption-scope-override",
                type: {
                    name: "Boolean",
                },
            },
            isImmutableStorageWithVersioningEnabled: {
                serializedName: "x-ms-immutable-storage-with-versioning-enabled",
                xmlName: "x-ms-immutable-storage-with-versioning-enabled",
                type: {
                    name: "Boolean",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerGetPropertiesExceptionHeaders = {
    serializedName: "Container_getPropertiesExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerGetPropertiesExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerDeleteHeaders = {
    serializedName: "Container_deleteHeaders",
    type: {
        name: "Composite",
        className: "ContainerDeleteHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerDeleteExceptionHeaders = {
    serializedName: "Container_deleteExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerDeleteExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerSetMetadataHeaders = {
    serializedName: "Container_setMetadataHeaders",
    type: {
        name: "Composite",
        className: "ContainerSetMetadataHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerSetMetadataExceptionHeaders = {
    serializedName: "Container_setMetadataExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerSetMetadataExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerGetAccessPolicyHeaders = {
    serializedName: "Container_getAccessPolicyHeaders",
    type: {
        name: "Composite",
        className: "ContainerGetAccessPolicyHeaders",
        modelProperties: {
            blobPublicAccess: {
                serializedName: "x-ms-blob-public-access",
                xmlName: "x-ms-blob-public-access",
                type: {
                    name: "Enum",
                    allowedValues: ["container", "blob"],
                },
            },
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerGetAccessPolicyExceptionHeaders = {
    serializedName: "Container_getAccessPolicyExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerGetAccessPolicyExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerSetAccessPolicyHeaders = {
    serializedName: "Container_setAccessPolicyHeaders",
    type: {
        name: "Composite",
        className: "ContainerSetAccessPolicyHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerSetAccessPolicyExceptionHeaders = {
    serializedName: "Container_setAccessPolicyExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerSetAccessPolicyExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerRestoreHeaders = {
    serializedName: "Container_restoreHeaders",
    type: {
        name: "Composite",
        className: "ContainerRestoreHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerRestoreExceptionHeaders = {
    serializedName: "Container_restoreExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerRestoreExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerRenameHeaders = {
    serializedName: "Container_renameHeaders",
    type: {
        name: "Composite",
        className: "ContainerRenameHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerRenameExceptionHeaders = {
    serializedName: "Container_renameExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerRenameExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerSubmitBatchHeaders = {
    serializedName: "Container_submitBatchHeaders",
    type: {
        name: "Composite",
        className: "ContainerSubmitBatchHeaders",
        modelProperties: {
            contentType: {
                serializedName: "content-type",
                xmlName: "content-type",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerSubmitBatchExceptionHeaders = {
    serializedName: "Container_submitBatchExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerSubmitBatchExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerFilterBlobsHeaders = {
    serializedName: "Container_filterBlobsHeaders",
    type: {
        name: "Composite",
        className: "ContainerFilterBlobsHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const ContainerFilterBlobsExceptionHeaders = {
    serializedName: "Container_filterBlobsExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerFilterBlobsExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerAcquireLeaseHeaders = {
    serializedName: "Container_acquireLeaseHeaders",
    type: {
        name: "Composite",
        className: "ContainerAcquireLeaseHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            leaseId: {
                serializedName: "x-ms-lease-id",
                xmlName: "x-ms-lease-id",
                type: {
                    name: "String",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const ContainerAcquireLeaseExceptionHeaders = {
    serializedName: "Container_acquireLeaseExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerAcquireLeaseExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerReleaseLeaseHeaders = {
    serializedName: "Container_releaseLeaseHeaders",
    type: {
        name: "Composite",
        className: "ContainerReleaseLeaseHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const ContainerReleaseLeaseExceptionHeaders = {
    serializedName: "Container_releaseLeaseExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerReleaseLeaseExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerRenewLeaseHeaders = {
    serializedName: "Container_renewLeaseHeaders",
    type: {
        name: "Composite",
        className: "ContainerRenewLeaseHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            leaseId: {
                serializedName: "x-ms-lease-id",
                xmlName: "x-ms-lease-id",
                type: {
                    name: "String",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const ContainerRenewLeaseExceptionHeaders = {
    serializedName: "Container_renewLeaseExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerRenewLeaseExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerBreakLeaseHeaders = {
    serializedName: "Container_breakLeaseHeaders",
    type: {
        name: "Composite",
        className: "ContainerBreakLeaseHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            leaseTime: {
                serializedName: "x-ms-lease-time",
                xmlName: "x-ms-lease-time",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const ContainerBreakLeaseExceptionHeaders = {
    serializedName: "Container_breakLeaseExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerBreakLeaseExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerChangeLeaseHeaders = {
    serializedName: "Container_changeLeaseHeaders",
    type: {
        name: "Composite",
        className: "ContainerChangeLeaseHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            leaseId: {
                serializedName: "x-ms-lease-id",
                xmlName: "x-ms-lease-id",
                type: {
                    name: "String",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const ContainerChangeLeaseExceptionHeaders = {
    serializedName: "Container_changeLeaseExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerChangeLeaseExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerListBlobFlatSegmentHeaders = {
    serializedName: "Container_listBlobFlatSegmentHeaders",
    type: {
        name: "Composite",
        className: "ContainerListBlobFlatSegmentHeaders",
        modelProperties: {
            contentType: {
                serializedName: "content-type",
                xmlName: "content-type",
                type: {
                    name: "String",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerListBlobFlatSegmentExceptionHeaders = {
    serializedName: "Container_listBlobFlatSegmentExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerListBlobFlatSegmentExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerListBlobHierarchySegmentHeaders = {
    serializedName: "Container_listBlobHierarchySegmentHeaders",
    type: {
        name: "Composite",
        className: "ContainerListBlobHierarchySegmentHeaders",
        modelProperties: {
            contentType: {
                serializedName: "content-type",
                xmlName: "content-type",
                type: {
                    name: "String",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerListBlobHierarchySegmentExceptionHeaders = {
    serializedName: "Container_listBlobHierarchySegmentExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerListBlobHierarchySegmentExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const ContainerGetAccountInfoHeaders = {
    serializedName: "Container_getAccountInfoHeaders",
    type: {
        name: "Composite",
        className: "ContainerGetAccountInfoHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            skuName: {
                serializedName: "x-ms-sku-name",
                xmlName: "x-ms-sku-name",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "Standard_LRS",
                        "Standard_GRS",
                        "Standard_RAGRS",
                        "Standard_ZRS",
                        "Premium_LRS",
                    ],
                },
            },
            accountKind: {
                serializedName: "x-ms-account-kind",
                xmlName: "x-ms-account-kind",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "Storage",
                        "BlobStorage",
                        "StorageV2",
                        "FileStorage",
                        "BlockBlobStorage",
                    ],
                },
            },
            isHierarchicalNamespaceEnabled: {
                serializedName: "x-ms-is-hns-enabled",
                xmlName: "x-ms-is-hns-enabled",
                type: {
                    name: "Boolean",
                },
            },
        },
    },
};
const ContainerGetAccountInfoExceptionHeaders = {
    serializedName: "Container_getAccountInfoExceptionHeaders",
    type: {
        name: "Composite",
        className: "ContainerGetAccountInfoExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobDownloadHeaders = {
    serializedName: "Blob_downloadHeaders",
    type: {
        name: "Composite",
        className: "BlobDownloadHeaders",
        modelProperties: {
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            createdOn: {
                serializedName: "x-ms-creation-time",
                xmlName: "x-ms-creation-time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            metadata: {
                serializedName: "x-ms-meta",
                headerCollectionPrefix: "x-ms-meta-",
                xmlName: "x-ms-meta",
                type: {
                    name: "Dictionary",
                    value: { type: { name: "String" } },
                },
            },
            objectReplicationPolicyId: {
                serializedName: "x-ms-or-policy-id",
                xmlName: "x-ms-or-policy-id",
                type: {
                    name: "String",
                },
            },
            objectReplicationRules: {
                serializedName: "x-ms-or",
                headerCollectionPrefix: "x-ms-or-",
                xmlName: "x-ms-or",
                type: {
                    name: "Dictionary",
                    value: { type: { name: "String" } },
                },
            },
            contentLength: {
                serializedName: "content-length",
                xmlName: "content-length",
                type: {
                    name: "Number",
                },
            },
            contentType: {
                serializedName: "content-type",
                xmlName: "content-type",
                type: {
                    name: "String",
                },
            },
            contentRange: {
                serializedName: "content-range",
                xmlName: "content-range",
                type: {
                    name: "String",
                },
            },
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            contentEncoding: {
                serializedName: "content-encoding",
                xmlName: "content-encoding",
                type: {
                    name: "String",
                },
            },
            cacheControl: {
                serializedName: "cache-control",
                xmlName: "cache-control",
                type: {
                    name: "String",
                },
            },
            contentDisposition: {
                serializedName: "content-disposition",
                xmlName: "content-disposition",
                type: {
                    name: "String",
                },
            },
            contentLanguage: {
                serializedName: "content-language",
                xmlName: "content-language",
                type: {
                    name: "String",
                },
            },
            blobSequenceNumber: {
                serializedName: "x-ms-blob-sequence-number",
                xmlName: "x-ms-blob-sequence-number",
                type: {
                    name: "Number",
                },
            },
            blobType: {
                serializedName: "x-ms-blob-type",
                xmlName: "x-ms-blob-type",
                type: {
                    name: "Enum",
                    allowedValues: ["BlockBlob", "PageBlob", "AppendBlob"],
                },
            },
            copyCompletedOn: {
                serializedName: "x-ms-copy-completion-time",
                xmlName: "x-ms-copy-completion-time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            copyStatusDescription: {
                serializedName: "x-ms-copy-status-description",
                xmlName: "x-ms-copy-status-description",
                type: {
                    name: "String",
                },
            },
            copyId: {
                serializedName: "x-ms-copy-id",
                xmlName: "x-ms-copy-id",
                type: {
                    name: "String",
                },
            },
            copyProgress: {
                serializedName: "x-ms-copy-progress",
                xmlName: "x-ms-copy-progress",
                type: {
                    name: "String",
                },
            },
            copySource: {
                serializedName: "x-ms-copy-source",
                xmlName: "x-ms-copy-source",
                type: {
                    name: "String",
                },
            },
            copyStatus: {
                serializedName: "x-ms-copy-status",
                xmlName: "x-ms-copy-status",
                type: {
                    name: "Enum",
                    allowedValues: ["pending", "success", "aborted", "failed"],
                },
            },
            leaseDuration: {
                serializedName: "x-ms-lease-duration",
                xmlName: "x-ms-lease-duration",
                type: {
                    name: "Enum",
                    allowedValues: ["infinite", "fixed"],
                },
            },
            leaseState: {
                serializedName: "x-ms-lease-state",
                xmlName: "x-ms-lease-state",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "available",
                        "leased",
                        "expired",
                        "breaking",
                        "broken",
                    ],
                },
            },
            leaseStatus: {
                serializedName: "x-ms-lease-status",
                xmlName: "x-ms-lease-status",
                type: {
                    name: "Enum",
                    allowedValues: ["locked", "unlocked"],
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            isCurrentVersion: {
                serializedName: "x-ms-is-current-version",
                xmlName: "x-ms-is-current-version",
                type: {
                    name: "Boolean",
                },
            },
            acceptRanges: {
                serializedName: "accept-ranges",
                xmlName: "accept-ranges",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            blobCommittedBlockCount: {
                serializedName: "x-ms-blob-committed-block-count",
                xmlName: "x-ms-blob-committed-block-count",
                type: {
                    name: "Number",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-server-encrypted",
                xmlName: "x-ms-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            blobContentMD5: {
                serializedName: "x-ms-blob-content-md5",
                xmlName: "x-ms-blob-content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            tagCount: {
                serializedName: "x-ms-tag-count",
                xmlName: "x-ms-tag-count",
                type: {
                    name: "Number",
                },
            },
            isSealed: {
                serializedName: "x-ms-blob-sealed",
                xmlName: "x-ms-blob-sealed",
                type: {
                    name: "Boolean",
                },
            },
            lastAccessed: {
                serializedName: "x-ms-last-access-time",
                xmlName: "x-ms-last-access-time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            immutabilityPolicyExpiresOn: {
                serializedName: "x-ms-immutability-policy-until-date",
                xmlName: "x-ms-immutability-policy-until-date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            immutabilityPolicyMode: {
                serializedName: "x-ms-immutability-policy-mode",
                xmlName: "x-ms-immutability-policy-mode",
                type: {
                    name: "Enum",
                    allowedValues: ["Mutable", "Unlocked", "Locked"],
                },
            },
            legalHold: {
                serializedName: "x-ms-legal-hold",
                xmlName: "x-ms-legal-hold",
                type: {
                    name: "Boolean",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
            contentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
        },
    },
};
const BlobDownloadExceptionHeaders = {
    serializedName: "Blob_downloadExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobDownloadExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobGetPropertiesHeaders = {
    serializedName: "Blob_getPropertiesHeaders",
    type: {
        name: "Composite",
        className: "BlobGetPropertiesHeaders",
        modelProperties: {
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            createdOn: {
                serializedName: "x-ms-creation-time",
                xmlName: "x-ms-creation-time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            metadata: {
                serializedName: "x-ms-meta",
                headerCollectionPrefix: "x-ms-meta-",
                xmlName: "x-ms-meta",
                type: {
                    name: "Dictionary",
                    value: { type: { name: "String" } },
                },
            },
            objectReplicationPolicyId: {
                serializedName: "x-ms-or-policy-id",
                xmlName: "x-ms-or-policy-id",
                type: {
                    name: "String",
                },
            },
            objectReplicationRules: {
                serializedName: "x-ms-or",
                headerCollectionPrefix: "x-ms-or-",
                xmlName: "x-ms-or",
                type: {
                    name: "Dictionary",
                    value: { type: { name: "String" } },
                },
            },
            blobType: {
                serializedName: "x-ms-blob-type",
                xmlName: "x-ms-blob-type",
                type: {
                    name: "Enum",
                    allowedValues: ["BlockBlob", "PageBlob", "AppendBlob"],
                },
            },
            copyCompletedOn: {
                serializedName: "x-ms-copy-completion-time",
                xmlName: "x-ms-copy-completion-time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            copyStatusDescription: {
                serializedName: "x-ms-copy-status-description",
                xmlName: "x-ms-copy-status-description",
                type: {
                    name: "String",
                },
            },
            copyId: {
                serializedName: "x-ms-copy-id",
                xmlName: "x-ms-copy-id",
                type: {
                    name: "String",
                },
            },
            copyProgress: {
                serializedName: "x-ms-copy-progress",
                xmlName: "x-ms-copy-progress",
                type: {
                    name: "String",
                },
            },
            copySource: {
                serializedName: "x-ms-copy-source",
                xmlName: "x-ms-copy-source",
                type: {
                    name: "String",
                },
            },
            copyStatus: {
                serializedName: "x-ms-copy-status",
                xmlName: "x-ms-copy-status",
                type: {
                    name: "Enum",
                    allowedValues: ["pending", "success", "aborted", "failed"],
                },
            },
            isIncrementalCopy: {
                serializedName: "x-ms-incremental-copy",
                xmlName: "x-ms-incremental-copy",
                type: {
                    name: "Boolean",
                },
            },
            destinationSnapshot: {
                serializedName: "x-ms-copy-destination-snapshot",
                xmlName: "x-ms-copy-destination-snapshot",
                type: {
                    name: "String",
                },
            },
            leaseDuration: {
                serializedName: "x-ms-lease-duration",
                xmlName: "x-ms-lease-duration",
                type: {
                    name: "Enum",
                    allowedValues: ["infinite", "fixed"],
                },
            },
            leaseState: {
                serializedName: "x-ms-lease-state",
                xmlName: "x-ms-lease-state",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "available",
                        "leased",
                        "expired",
                        "breaking",
                        "broken",
                    ],
                },
            },
            leaseStatus: {
                serializedName: "x-ms-lease-status",
                xmlName: "x-ms-lease-status",
                type: {
                    name: "Enum",
                    allowedValues: ["locked", "unlocked"],
                },
            },
            contentLength: {
                serializedName: "content-length",
                xmlName: "content-length",
                type: {
                    name: "Number",
                },
            },
            contentType: {
                serializedName: "content-type",
                xmlName: "content-type",
                type: {
                    name: "String",
                },
            },
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            contentEncoding: {
                serializedName: "content-encoding",
                xmlName: "content-encoding",
                type: {
                    name: "String",
                },
            },
            contentDisposition: {
                serializedName: "content-disposition",
                xmlName: "content-disposition",
                type: {
                    name: "String",
                },
            },
            contentLanguage: {
                serializedName: "content-language",
                xmlName: "content-language",
                type: {
                    name: "String",
                },
            },
            cacheControl: {
                serializedName: "cache-control",
                xmlName: "cache-control",
                type: {
                    name: "String",
                },
            },
            blobSequenceNumber: {
                serializedName: "x-ms-blob-sequence-number",
                xmlName: "x-ms-blob-sequence-number",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            acceptRanges: {
                serializedName: "accept-ranges",
                xmlName: "accept-ranges",
                type: {
                    name: "String",
                },
            },
            blobCommittedBlockCount: {
                serializedName: "x-ms-blob-committed-block-count",
                xmlName: "x-ms-blob-committed-block-count",
                type: {
                    name: "Number",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-server-encrypted",
                xmlName: "x-ms-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            accessTier: {
                serializedName: "x-ms-access-tier",
                xmlName: "x-ms-access-tier",
                type: {
                    name: "String",
                },
            },
            accessTierInferred: {
                serializedName: "x-ms-access-tier-inferred",
                xmlName: "x-ms-access-tier-inferred",
                type: {
                    name: "Boolean",
                },
            },
            archiveStatus: {
                serializedName: "x-ms-archive-status",
                xmlName: "x-ms-archive-status",
                type: {
                    name: "String",
                },
            },
            accessTierChangedOn: {
                serializedName: "x-ms-access-tier-change-time",
                xmlName: "x-ms-access-tier-change-time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            isCurrentVersion: {
                serializedName: "x-ms-is-current-version",
                xmlName: "x-ms-is-current-version",
                type: {
                    name: "Boolean",
                },
            },
            tagCount: {
                serializedName: "x-ms-tag-count",
                xmlName: "x-ms-tag-count",
                type: {
                    name: "Number",
                },
            },
            expiresOn: {
                serializedName: "x-ms-expiry-time",
                xmlName: "x-ms-expiry-time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isSealed: {
                serializedName: "x-ms-blob-sealed",
                xmlName: "x-ms-blob-sealed",
                type: {
                    name: "Boolean",
                },
            },
            rehydratePriority: {
                serializedName: "x-ms-rehydrate-priority",
                xmlName: "x-ms-rehydrate-priority",
                type: {
                    name: "Enum",
                    allowedValues: ["High", "Standard"],
                },
            },
            lastAccessed: {
                serializedName: "x-ms-last-access-time",
                xmlName: "x-ms-last-access-time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            immutabilityPolicyExpiresOn: {
                serializedName: "x-ms-immutability-policy-until-date",
                xmlName: "x-ms-immutability-policy-until-date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            immutabilityPolicyMode: {
                serializedName: "x-ms-immutability-policy-mode",
                xmlName: "x-ms-immutability-policy-mode",
                type: {
                    name: "Enum",
                    allowedValues: ["Mutable", "Unlocked", "Locked"],
                },
            },
            legalHold: {
                serializedName: "x-ms-legal-hold",
                xmlName: "x-ms-legal-hold",
                type: {
                    name: "Boolean",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobGetPropertiesExceptionHeaders = {
    serializedName: "Blob_getPropertiesExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobGetPropertiesExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobDeleteHeaders = {
    serializedName: "Blob_deleteHeaders",
    type: {
        name: "Composite",
        className: "BlobDeleteHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobDeleteExceptionHeaders = {
    serializedName: "Blob_deleteExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobDeleteExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobUndeleteHeaders = {
    serializedName: "Blob_undeleteHeaders",
    type: {
        name: "Composite",
        className: "BlobUndeleteHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobUndeleteExceptionHeaders = {
    serializedName: "Blob_undeleteExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobUndeleteExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetExpiryHeaders = {
    serializedName: "Blob_setExpiryHeaders",
    type: {
        name: "Composite",
        className: "BlobSetExpiryHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const BlobSetExpiryExceptionHeaders = {
    serializedName: "Blob_setExpiryExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobSetExpiryExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetHttpHeadersHeaders = {
    serializedName: "Blob_setHttpHeadersHeaders",
    type: {
        name: "Composite",
        className: "BlobSetHttpHeadersHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            blobSequenceNumber: {
                serializedName: "x-ms-blob-sequence-number",
                xmlName: "x-ms-blob-sequence-number",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetHttpHeadersExceptionHeaders = {
    serializedName: "Blob_setHttpHeadersExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobSetHttpHeadersExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetImmutabilityPolicyHeaders = {
    serializedName: "Blob_setImmutabilityPolicyHeaders",
    type: {
        name: "Composite",
        className: "BlobSetImmutabilityPolicyHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            immutabilityPolicyExpiry: {
                serializedName: "x-ms-immutability-policy-until-date",
                xmlName: "x-ms-immutability-policy-until-date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            immutabilityPolicyMode: {
                serializedName: "x-ms-immutability-policy-mode",
                xmlName: "x-ms-immutability-policy-mode",
                type: {
                    name: "Enum",
                    allowedValues: ["Mutable", "Unlocked", "Locked"],
                },
            },
        },
    },
};
const BlobSetImmutabilityPolicyExceptionHeaders = {
    serializedName: "Blob_setImmutabilityPolicyExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobSetImmutabilityPolicyExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobDeleteImmutabilityPolicyHeaders = {
    serializedName: "Blob_deleteImmutabilityPolicyHeaders",
    type: {
        name: "Composite",
        className: "BlobDeleteImmutabilityPolicyHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const BlobDeleteImmutabilityPolicyExceptionHeaders = {
    serializedName: "Blob_deleteImmutabilityPolicyExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobDeleteImmutabilityPolicyExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetLegalHoldHeaders = {
    serializedName: "Blob_setLegalHoldHeaders",
    type: {
        name: "Composite",
        className: "BlobSetLegalHoldHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            legalHold: {
                serializedName: "x-ms-legal-hold",
                xmlName: "x-ms-legal-hold",
                type: {
                    name: "Boolean",
                },
            },
        },
    },
};
const BlobSetLegalHoldExceptionHeaders = {
    serializedName: "Blob_setLegalHoldExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobSetLegalHoldExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetMetadataHeaders = {
    serializedName: "Blob_setMetadataHeaders",
    type: {
        name: "Composite",
        className: "BlobSetMetadataHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetMetadataExceptionHeaders = {
    serializedName: "Blob_setMetadataExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobSetMetadataExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobAcquireLeaseHeaders = {
    serializedName: "Blob_acquireLeaseHeaders",
    type: {
        name: "Composite",
        className: "BlobAcquireLeaseHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            leaseId: {
                serializedName: "x-ms-lease-id",
                xmlName: "x-ms-lease-id",
                type: {
                    name: "String",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const BlobAcquireLeaseExceptionHeaders = {
    serializedName: "Blob_acquireLeaseExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobAcquireLeaseExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobReleaseLeaseHeaders = {
    serializedName: "Blob_releaseLeaseHeaders",
    type: {
        name: "Composite",
        className: "BlobReleaseLeaseHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const BlobReleaseLeaseExceptionHeaders = {
    serializedName: "Blob_releaseLeaseExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobReleaseLeaseExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobRenewLeaseHeaders = {
    serializedName: "Blob_renewLeaseHeaders",
    type: {
        name: "Composite",
        className: "BlobRenewLeaseHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            leaseId: {
                serializedName: "x-ms-lease-id",
                xmlName: "x-ms-lease-id",
                type: {
                    name: "String",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const BlobRenewLeaseExceptionHeaders = {
    serializedName: "Blob_renewLeaseExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobRenewLeaseExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobChangeLeaseHeaders = {
    serializedName: "Blob_changeLeaseHeaders",
    type: {
        name: "Composite",
        className: "BlobChangeLeaseHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            leaseId: {
                serializedName: "x-ms-lease-id",
                xmlName: "x-ms-lease-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const BlobChangeLeaseExceptionHeaders = {
    serializedName: "Blob_changeLeaseExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobChangeLeaseExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobBreakLeaseHeaders = {
    serializedName: "Blob_breakLeaseHeaders",
    type: {
        name: "Composite",
        className: "BlobBreakLeaseHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            leaseTime: {
                serializedName: "x-ms-lease-time",
                xmlName: "x-ms-lease-time",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
        },
    },
};
const BlobBreakLeaseExceptionHeaders = {
    serializedName: "Blob_breakLeaseExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobBreakLeaseExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobCreateSnapshotHeaders = {
    serializedName: "Blob_createSnapshotHeaders",
    type: {
        name: "Composite",
        className: "BlobCreateSnapshotHeaders",
        modelProperties: {
            snapshot: {
                serializedName: "x-ms-snapshot",
                xmlName: "x-ms-snapshot",
                type: {
                    name: "String",
                },
            },
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobCreateSnapshotExceptionHeaders = {
    serializedName: "Blob_createSnapshotExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobCreateSnapshotExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobStartCopyFromURLHeaders = {
    serializedName: "Blob_startCopyFromURLHeaders",
    type: {
        name: "Composite",
        className: "BlobStartCopyFromURLHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            copyId: {
                serializedName: "x-ms-copy-id",
                xmlName: "x-ms-copy-id",
                type: {
                    name: "String",
                },
            },
            copyStatus: {
                serializedName: "x-ms-copy-status",
                xmlName: "x-ms-copy-status",
                type: {
                    name: "Enum",
                    allowedValues: ["pending", "success", "aborted", "failed"],
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobStartCopyFromURLExceptionHeaders = {
    serializedName: "Blob_startCopyFromURLExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobStartCopyFromURLExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceErrorCode: {
                serializedName: "x-ms-copy-source-error-code",
                xmlName: "x-ms-copy-source-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceStatusCode: {
                serializedName: "x-ms-copy-source-status-code",
                xmlName: "x-ms-copy-source-status-code",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const BlobCopyFromURLHeaders = {
    serializedName: "Blob_copyFromURLHeaders",
    type: {
        name: "Composite",
        className: "BlobCopyFromURLHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            copyId: {
                serializedName: "x-ms-copy-id",
                xmlName: "x-ms-copy-id",
                type: {
                    name: "String",
                },
            },
            copyStatus: {
                defaultValue: "success",
                isConstant: true,
                serializedName: "x-ms-copy-status",
                type: {
                    name: "String",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            xMsContentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobCopyFromURLExceptionHeaders = {
    serializedName: "Blob_copyFromURLExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobCopyFromURLExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceErrorCode: {
                serializedName: "x-ms-copy-source-error-code",
                xmlName: "x-ms-copy-source-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceStatusCode: {
                serializedName: "x-ms-copy-source-status-code",
                xmlName: "x-ms-copy-source-status-code",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const BlobAbortCopyFromURLHeaders = {
    serializedName: "Blob_abortCopyFromURLHeaders",
    type: {
        name: "Composite",
        className: "BlobAbortCopyFromURLHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobAbortCopyFromURLExceptionHeaders = {
    serializedName: "Blob_abortCopyFromURLExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobAbortCopyFromURLExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetTierHeaders = {
    serializedName: "Blob_setTierHeaders",
    type: {
        name: "Composite",
        className: "BlobSetTierHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetTierExceptionHeaders = {
    serializedName: "Blob_setTierExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobSetTierExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobGetAccountInfoHeaders = {
    serializedName: "Blob_getAccountInfoHeaders",
    type: {
        name: "Composite",
        className: "BlobGetAccountInfoHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            skuName: {
                serializedName: "x-ms-sku-name",
                xmlName: "x-ms-sku-name",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "Standard_LRS",
                        "Standard_GRS",
                        "Standard_RAGRS",
                        "Standard_ZRS",
                        "Premium_LRS",
                    ],
                },
            },
            accountKind: {
                serializedName: "x-ms-account-kind",
                xmlName: "x-ms-account-kind",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "Storage",
                        "BlobStorage",
                        "StorageV2",
                        "FileStorage",
                        "BlockBlobStorage",
                    ],
                },
            },
            isHierarchicalNamespaceEnabled: {
                serializedName: "x-ms-is-hns-enabled",
                xmlName: "x-ms-is-hns-enabled",
                type: {
                    name: "Boolean",
                },
            },
        },
    },
};
const BlobGetAccountInfoExceptionHeaders = {
    serializedName: "Blob_getAccountInfoExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobGetAccountInfoExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobQueryHeaders = {
    serializedName: "Blob_queryHeaders",
    type: {
        name: "Composite",
        className: "BlobQueryHeaders",
        modelProperties: {
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            metadata: {
                serializedName: "x-ms-meta",
                headerCollectionPrefix: "x-ms-meta-",
                xmlName: "x-ms-meta",
                type: {
                    name: "Dictionary",
                    value: { type: { name: "String" } },
                },
            },
            contentLength: {
                serializedName: "content-length",
                xmlName: "content-length",
                type: {
                    name: "Number",
                },
            },
            contentType: {
                serializedName: "content-type",
                xmlName: "content-type",
                type: {
                    name: "String",
                },
            },
            contentRange: {
                serializedName: "content-range",
                xmlName: "content-range",
                type: {
                    name: "String",
                },
            },
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            contentEncoding: {
                serializedName: "content-encoding",
                xmlName: "content-encoding",
                type: {
                    name: "String",
                },
            },
            cacheControl: {
                serializedName: "cache-control",
                xmlName: "cache-control",
                type: {
                    name: "String",
                },
            },
            contentDisposition: {
                serializedName: "content-disposition",
                xmlName: "content-disposition",
                type: {
                    name: "String",
                },
            },
            contentLanguage: {
                serializedName: "content-language",
                xmlName: "content-language",
                type: {
                    name: "String",
                },
            },
            blobSequenceNumber: {
                serializedName: "x-ms-blob-sequence-number",
                xmlName: "x-ms-blob-sequence-number",
                type: {
                    name: "Number",
                },
            },
            blobType: {
                serializedName: "x-ms-blob-type",
                xmlName: "x-ms-blob-type",
                type: {
                    name: "Enum",
                    allowedValues: ["BlockBlob", "PageBlob", "AppendBlob"],
                },
            },
            copyCompletionTime: {
                serializedName: "x-ms-copy-completion-time",
                xmlName: "x-ms-copy-completion-time",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            copyStatusDescription: {
                serializedName: "x-ms-copy-status-description",
                xmlName: "x-ms-copy-status-description",
                type: {
                    name: "String",
                },
            },
            copyId: {
                serializedName: "x-ms-copy-id",
                xmlName: "x-ms-copy-id",
                type: {
                    name: "String",
                },
            },
            copyProgress: {
                serializedName: "x-ms-copy-progress",
                xmlName: "x-ms-copy-progress",
                type: {
                    name: "String",
                },
            },
            copySource: {
                serializedName: "x-ms-copy-source",
                xmlName: "x-ms-copy-source",
                type: {
                    name: "String",
                },
            },
            copyStatus: {
                serializedName: "x-ms-copy-status",
                xmlName: "x-ms-copy-status",
                type: {
                    name: "Enum",
                    allowedValues: ["pending", "success", "aborted", "failed"],
                },
            },
            leaseDuration: {
                serializedName: "x-ms-lease-duration",
                xmlName: "x-ms-lease-duration",
                type: {
                    name: "Enum",
                    allowedValues: ["infinite", "fixed"],
                },
            },
            leaseState: {
                serializedName: "x-ms-lease-state",
                xmlName: "x-ms-lease-state",
                type: {
                    name: "Enum",
                    allowedValues: [
                        "available",
                        "leased",
                        "expired",
                        "breaking",
                        "broken",
                    ],
                },
            },
            leaseStatus: {
                serializedName: "x-ms-lease-status",
                xmlName: "x-ms-lease-status",
                type: {
                    name: "Enum",
                    allowedValues: ["locked", "unlocked"],
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            acceptRanges: {
                serializedName: "accept-ranges",
                xmlName: "accept-ranges",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            blobCommittedBlockCount: {
                serializedName: "x-ms-blob-committed-block-count",
                xmlName: "x-ms-blob-committed-block-count",
                type: {
                    name: "Number",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-server-encrypted",
                xmlName: "x-ms-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            blobContentMD5: {
                serializedName: "x-ms-blob-content-md5",
                xmlName: "x-ms-blob-content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
            contentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
        },
    },
};
const BlobQueryExceptionHeaders = {
    serializedName: "Blob_queryExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobQueryExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobGetTagsHeaders = {
    serializedName: "Blob_getTagsHeaders",
    type: {
        name: "Composite",
        className: "BlobGetTagsHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobGetTagsExceptionHeaders = {
    serializedName: "Blob_getTagsExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobGetTagsExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetTagsHeaders = {
    serializedName: "Blob_setTagsHeaders",
    type: {
        name: "Composite",
        className: "BlobSetTagsHeaders",
        modelProperties: {
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlobSetTagsExceptionHeaders = {
    serializedName: "Blob_setTagsExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlobSetTagsExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobCreateHeaders = {
    serializedName: "PageBlob_createHeaders",
    type: {
        name: "Composite",
        className: "PageBlobCreateHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobCreateExceptionHeaders = {
    serializedName: "PageBlob_createExceptionHeaders",
    type: {
        name: "Composite",
        className: "PageBlobCreateExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobUploadPagesHeaders = {
    serializedName: "PageBlob_uploadPagesHeaders",
    type: {
        name: "Composite",
        className: "PageBlobUploadPagesHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            xMsContentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
            blobSequenceNumber: {
                serializedName: "x-ms-blob-sequence-number",
                xmlName: "x-ms-blob-sequence-number",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobUploadPagesExceptionHeaders = {
    serializedName: "PageBlob_uploadPagesExceptionHeaders",
    type: {
        name: "Composite",
        className: "PageBlobUploadPagesExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobClearPagesHeaders = {
    serializedName: "PageBlob_clearPagesHeaders",
    type: {
        name: "Composite",
        className: "PageBlobClearPagesHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            xMsContentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
            blobSequenceNumber: {
                serializedName: "x-ms-blob-sequence-number",
                xmlName: "x-ms-blob-sequence-number",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobClearPagesExceptionHeaders = {
    serializedName: "PageBlob_clearPagesExceptionHeaders",
    type: {
        name: "Composite",
        className: "PageBlobClearPagesExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobUploadPagesFromURLHeaders = {
    serializedName: "PageBlob_uploadPagesFromURLHeaders",
    type: {
        name: "Composite",
        className: "PageBlobUploadPagesFromURLHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            xMsContentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
            blobSequenceNumber: {
                serializedName: "x-ms-blob-sequence-number",
                xmlName: "x-ms-blob-sequence-number",
                type: {
                    name: "Number",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobUploadPagesFromURLExceptionHeaders = {
    serializedName: "PageBlob_uploadPagesFromURLExceptionHeaders",
    type: {
        name: "Composite",
        className: "PageBlobUploadPagesFromURLExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceErrorCode: {
                serializedName: "x-ms-copy-source-error-code",
                xmlName: "x-ms-copy-source-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceStatusCode: {
                serializedName: "x-ms-copy-source-status-code",
                xmlName: "x-ms-copy-source-status-code",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const PageBlobGetPageRangesHeaders = {
    serializedName: "PageBlob_getPageRangesHeaders",
    type: {
        name: "Composite",
        className: "PageBlobGetPageRangesHeaders",
        modelProperties: {
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            blobContentLength: {
                serializedName: "x-ms-blob-content-length",
                xmlName: "x-ms-blob-content-length",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobGetPageRangesExceptionHeaders = {
    serializedName: "PageBlob_getPageRangesExceptionHeaders",
    type: {
        name: "Composite",
        className: "PageBlobGetPageRangesExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobGetPageRangesDiffHeaders = {
    serializedName: "PageBlob_getPageRangesDiffHeaders",
    type: {
        name: "Composite",
        className: "PageBlobGetPageRangesDiffHeaders",
        modelProperties: {
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            blobContentLength: {
                serializedName: "x-ms-blob-content-length",
                xmlName: "x-ms-blob-content-length",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobGetPageRangesDiffExceptionHeaders = {
    serializedName: "PageBlob_getPageRangesDiffExceptionHeaders",
    type: {
        name: "Composite",
        className: "PageBlobGetPageRangesDiffExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobResizeHeaders = {
    serializedName: "PageBlob_resizeHeaders",
    type: {
        name: "Composite",
        className: "PageBlobResizeHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            blobSequenceNumber: {
                serializedName: "x-ms-blob-sequence-number",
                xmlName: "x-ms-blob-sequence-number",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobResizeExceptionHeaders = {
    serializedName: "PageBlob_resizeExceptionHeaders",
    type: {
        name: "Composite",
        className: "PageBlobResizeExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobUpdateSequenceNumberHeaders = {
    serializedName: "PageBlob_updateSequenceNumberHeaders",
    type: {
        name: "Composite",
        className: "PageBlobUpdateSequenceNumberHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            blobSequenceNumber: {
                serializedName: "x-ms-blob-sequence-number",
                xmlName: "x-ms-blob-sequence-number",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobUpdateSequenceNumberExceptionHeaders = {
    serializedName: "PageBlob_updateSequenceNumberExceptionHeaders",
    type: {
        name: "Composite",
        className: "PageBlobUpdateSequenceNumberExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobCopyIncrementalHeaders = {
    serializedName: "PageBlob_copyIncrementalHeaders",
    type: {
        name: "Composite",
        className: "PageBlobCopyIncrementalHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            copyId: {
                serializedName: "x-ms-copy-id",
                xmlName: "x-ms-copy-id",
                type: {
                    name: "String",
                },
            },
            copyStatus: {
                serializedName: "x-ms-copy-status",
                xmlName: "x-ms-copy-status",
                type: {
                    name: "Enum",
                    allowedValues: ["pending", "success", "aborted", "failed"],
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const PageBlobCopyIncrementalExceptionHeaders = {
    serializedName: "PageBlob_copyIncrementalExceptionHeaders",
    type: {
        name: "Composite",
        className: "PageBlobCopyIncrementalExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const AppendBlobCreateHeaders = {
    serializedName: "AppendBlob_createHeaders",
    type: {
        name: "Composite",
        className: "AppendBlobCreateHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const AppendBlobCreateExceptionHeaders = {
    serializedName: "AppendBlob_createExceptionHeaders",
    type: {
        name: "Composite",
        className: "AppendBlobCreateExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const AppendBlobAppendBlockHeaders = {
    serializedName: "AppendBlob_appendBlockHeaders",
    type: {
        name: "Composite",
        className: "AppendBlobAppendBlockHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            xMsContentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            blobAppendOffset: {
                serializedName: "x-ms-blob-append-offset",
                xmlName: "x-ms-blob-append-offset",
                type: {
                    name: "String",
                },
            },
            blobCommittedBlockCount: {
                serializedName: "x-ms-blob-committed-block-count",
                xmlName: "x-ms-blob-committed-block-count",
                type: {
                    name: "Number",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const AppendBlobAppendBlockExceptionHeaders = {
    serializedName: "AppendBlob_appendBlockExceptionHeaders",
    type: {
        name: "Composite",
        className: "AppendBlobAppendBlockExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const AppendBlobAppendBlockFromUrlHeaders = {
    serializedName: "AppendBlob_appendBlockFromUrlHeaders",
    type: {
        name: "Composite",
        className: "AppendBlobAppendBlockFromUrlHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            xMsContentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            blobAppendOffset: {
                serializedName: "x-ms-blob-append-offset",
                xmlName: "x-ms-blob-append-offset",
                type: {
                    name: "String",
                },
            },
            blobCommittedBlockCount: {
                serializedName: "x-ms-blob-committed-block-count",
                xmlName: "x-ms-blob-committed-block-count",
                type: {
                    name: "Number",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const AppendBlobAppendBlockFromUrlExceptionHeaders = {
    serializedName: "AppendBlob_appendBlockFromUrlExceptionHeaders",
    type: {
        name: "Composite",
        className: "AppendBlobAppendBlockFromUrlExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceErrorCode: {
                serializedName: "x-ms-copy-source-error-code",
                xmlName: "x-ms-copy-source-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceStatusCode: {
                serializedName: "x-ms-copy-source-status-code",
                xmlName: "x-ms-copy-source-status-code",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const AppendBlobSealHeaders = {
    serializedName: "AppendBlob_sealHeaders",
    type: {
        name: "Composite",
        className: "AppendBlobSealHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isSealed: {
                serializedName: "x-ms-blob-sealed",
                xmlName: "x-ms-blob-sealed",
                type: {
                    name: "Boolean",
                },
            },
        },
    },
};
const AppendBlobSealExceptionHeaders = {
    serializedName: "AppendBlob_sealExceptionHeaders",
    type: {
        name: "Composite",
        className: "AppendBlobSealExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlockBlobUploadHeaders = {
    serializedName: "BlockBlob_uploadHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobUploadHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlockBlobUploadExceptionHeaders = {
    serializedName: "BlockBlob_uploadExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobUploadExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlockBlobPutBlobFromUrlHeaders = {
    serializedName: "BlockBlob_putBlobFromUrlHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobPutBlobFromUrlHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlockBlobPutBlobFromUrlExceptionHeaders = {
    serializedName: "BlockBlob_putBlobFromUrlExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobPutBlobFromUrlExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceErrorCode: {
                serializedName: "x-ms-copy-source-error-code",
                xmlName: "x-ms-copy-source-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceStatusCode: {
                serializedName: "x-ms-copy-source-status-code",
                xmlName: "x-ms-copy-source-status-code",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const BlockBlobStageBlockHeaders = {
    serializedName: "BlockBlob_stageBlockHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobStageBlockHeaders",
        modelProperties: {
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            xMsContentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlockBlobStageBlockExceptionHeaders = {
    serializedName: "BlockBlob_stageBlockExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobStageBlockExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlockBlobStageBlockFromURLHeaders = {
    serializedName: "BlockBlob_stageBlockFromURLHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobStageBlockFromURLHeaders",
        modelProperties: {
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            xMsContentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlockBlobStageBlockFromURLExceptionHeaders = {
    serializedName: "BlockBlob_stageBlockFromURLExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobStageBlockFromURLExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceErrorCode: {
                serializedName: "x-ms-copy-source-error-code",
                xmlName: "x-ms-copy-source-error-code",
                type: {
                    name: "String",
                },
            },
            copySourceStatusCode: {
                serializedName: "x-ms-copy-source-status-code",
                xmlName: "x-ms-copy-source-status-code",
                type: {
                    name: "Number",
                },
            },
        },
    },
};
const BlockBlobCommitBlockListHeaders = {
    serializedName: "BlockBlob_commitBlockListHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobCommitBlockListHeaders",
        modelProperties: {
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            contentMD5: {
                serializedName: "content-md5",
                xmlName: "content-md5",
                type: {
                    name: "ByteArray",
                },
            },
            xMsContentCrc64: {
                serializedName: "x-ms-content-crc64",
                xmlName: "x-ms-content-crc64",
                type: {
                    name: "ByteArray",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            versionId: {
                serializedName: "x-ms-version-id",
                xmlName: "x-ms-version-id",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            isServerEncrypted: {
                serializedName: "x-ms-request-server-encrypted",
                xmlName: "x-ms-request-server-encrypted",
                type: {
                    name: "Boolean",
                },
            },
            encryptionKeySha256: {
                serializedName: "x-ms-encryption-key-sha256",
                xmlName: "x-ms-encryption-key-sha256",
                type: {
                    name: "String",
                },
            },
            encryptionScope: {
                serializedName: "x-ms-encryption-scope",
                xmlName: "x-ms-encryption-scope",
                type: {
                    name: "String",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlockBlobCommitBlockListExceptionHeaders = {
    serializedName: "BlockBlob_commitBlockListExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobCommitBlockListExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlockBlobGetBlockListHeaders = {
    serializedName: "BlockBlob_getBlockListHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobGetBlockListHeaders",
        modelProperties: {
            lastModified: {
                serializedName: "last-modified",
                xmlName: "last-modified",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            etag: {
                serializedName: "etag",
                xmlName: "etag",
                type: {
                    name: "String",
                },
            },
            contentType: {
                serializedName: "content-type",
                xmlName: "content-type",
                type: {
                    name: "String",
                },
            },
            blobContentLength: {
                serializedName: "x-ms-blob-content-length",
                xmlName: "x-ms-blob-content-length",
                type: {
                    name: "Number",
                },
            },
            clientRequestId: {
                serializedName: "x-ms-client-request-id",
                xmlName: "x-ms-client-request-id",
                type: {
                    name: "String",
                },
            },
            requestId: {
                serializedName: "x-ms-request-id",
                xmlName: "x-ms-request-id",
                type: {
                    name: "String",
                },
            },
            version: {
                serializedName: "x-ms-version",
                xmlName: "x-ms-version",
                type: {
                    name: "String",
                },
            },
            date: {
                serializedName: "date",
                xmlName: "date",
                type: {
                    name: "DateTimeRfc1123",
                },
            },
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
const BlockBlobGetBlockListExceptionHeaders = {
    serializedName: "BlockBlob_getBlockListExceptionHeaders",
    type: {
        name: "Composite",
        className: "BlockBlobGetBlockListExceptionHeaders",
        modelProperties: {
            errorCode: {
                serializedName: "x-ms-error-code",
                xmlName: "x-ms-error-code",
                type: {
                    name: "String",
                },
            },
        },
    },
};
//# sourceMappingURL=mappers.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/models/parameters.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */

const contentType = {
    parameterPath: ["options", "contentType"],
    mapper: {
        defaultValue: "application/xml",
        isConstant: true,
        serializedName: "Content-Type",
        type: {
            name: "String",
        },
    },
};
const blobServiceProperties = {
    parameterPath: "blobServiceProperties",
    mapper: BlobServiceProperties,
};
const accept = {
    parameterPath: "accept",
    mapper: {
        defaultValue: "application/xml",
        isConstant: true,
        serializedName: "Accept",
        type: {
            name: "String",
        },
    },
};
const url = {
    parameterPath: "url",
    mapper: {
        serializedName: "url",
        required: true,
        xmlName: "url",
        type: {
            name: "String",
        },
    },
    skipEncoding: true,
};
const restype = {
    parameterPath: "restype",
    mapper: {
        defaultValue: "service",
        isConstant: true,
        serializedName: "restype",
        type: {
            name: "String",
        },
    },
};
const comp = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "properties",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const timeoutInSeconds = {
    parameterPath: ["options", "timeoutInSeconds"],
    mapper: {
        constraints: {
            InclusiveMinimum: 0,
        },
        serializedName: "timeout",
        xmlName: "timeout",
        type: {
            name: "Number",
        },
    },
};
const version = {
    parameterPath: "version",
    mapper: {
        defaultValue: "2026-02-06",
        isConstant: true,
        serializedName: "x-ms-version",
        type: {
            name: "String",
        },
    },
};
const requestId = {
    parameterPath: ["options", "requestId"],
    mapper: {
        serializedName: "x-ms-client-request-id",
        xmlName: "x-ms-client-request-id",
        type: {
            name: "String",
        },
    },
};
const accept1 = {
    parameterPath: "accept",
    mapper: {
        defaultValue: "application/xml",
        isConstant: true,
        serializedName: "Accept",
        type: {
            name: "String",
        },
    },
};
const comp1 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "stats",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const comp2 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "list",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const prefix = {
    parameterPath: ["options", "prefix"],
    mapper: {
        serializedName: "prefix",
        xmlName: "prefix",
        type: {
            name: "String",
        },
    },
};
const marker = {
    parameterPath: ["options", "marker"],
    mapper: {
        serializedName: "marker",
        xmlName: "marker",
        type: {
            name: "String",
        },
    },
};
const maxPageSize = {
    parameterPath: ["options", "maxPageSize"],
    mapper: {
        constraints: {
            InclusiveMinimum: 1,
        },
        serializedName: "maxresults",
        xmlName: "maxresults",
        type: {
            name: "Number",
        },
    },
};
const include = {
    parameterPath: ["options", "include"],
    mapper: {
        serializedName: "include",
        xmlName: "include",
        xmlElementName: "ListContainersIncludeType",
        type: {
            name: "Sequence",
            element: {
                type: {
                    name: "Enum",
                    allowedValues: ["metadata", "deleted", "system"],
                },
            },
        },
    },
    collectionFormat: "CSV",
};
const keyInfo = {
    parameterPath: "keyInfo",
    mapper: KeyInfo,
};
const comp3 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "userdelegationkey",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const restype1 = {
    parameterPath: "restype",
    mapper: {
        defaultValue: "account",
        isConstant: true,
        serializedName: "restype",
        type: {
            name: "String",
        },
    },
};
const body = {
    parameterPath: "body",
    mapper: {
        serializedName: "body",
        required: true,
        xmlName: "body",
        type: {
            name: "Stream",
        },
    },
};
const comp4 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "batch",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const contentLength = {
    parameterPath: "contentLength",
    mapper: {
        serializedName: "Content-Length",
        required: true,
        xmlName: "Content-Length",
        type: {
            name: "Number",
        },
    },
};
const multipartContentType = {
    parameterPath: "multipartContentType",
    mapper: {
        serializedName: "Content-Type",
        required: true,
        xmlName: "Content-Type",
        type: {
            name: "String",
        },
    },
};
const comp5 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "blobs",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const where = {
    parameterPath: ["options", "where"],
    mapper: {
        serializedName: "where",
        xmlName: "where",
        type: {
            name: "String",
        },
    },
};
const restype2 = {
    parameterPath: "restype",
    mapper: {
        defaultValue: "container",
        isConstant: true,
        serializedName: "restype",
        type: {
            name: "String",
        },
    },
};
const metadata = {
    parameterPath: ["options", "metadata"],
    mapper: {
        serializedName: "x-ms-meta",
        xmlName: "x-ms-meta",
        headerCollectionPrefix: "x-ms-meta-",
        type: {
            name: "Dictionary",
            value: { type: { name: "String" } },
        },
    },
};
const parameters_access = {
    parameterPath: ["options", "access"],
    mapper: {
        serializedName: "x-ms-blob-public-access",
        xmlName: "x-ms-blob-public-access",
        type: {
            name: "Enum",
            allowedValues: ["container", "blob"],
        },
    },
};
const defaultEncryptionScope = {
    parameterPath: [
        "options",
        "containerEncryptionScope",
        "defaultEncryptionScope",
    ],
    mapper: {
        serializedName: "x-ms-default-encryption-scope",
        xmlName: "x-ms-default-encryption-scope",
        type: {
            name: "String",
        },
    },
};
const preventEncryptionScopeOverride = {
    parameterPath: [
        "options",
        "containerEncryptionScope",
        "preventEncryptionScopeOverride",
    ],
    mapper: {
        serializedName: "x-ms-deny-encryption-scope-override",
        xmlName: "x-ms-deny-encryption-scope-override",
        type: {
            name: "Boolean",
        },
    },
};
const leaseId = {
    parameterPath: ["options", "leaseAccessConditions", "leaseId"],
    mapper: {
        serializedName: "x-ms-lease-id",
        xmlName: "x-ms-lease-id",
        type: {
            name: "String",
        },
    },
};
const ifModifiedSince = {
    parameterPath: ["options", "modifiedAccessConditions", "ifModifiedSince"],
    mapper: {
        serializedName: "If-Modified-Since",
        xmlName: "If-Modified-Since",
        type: {
            name: "DateTimeRfc1123",
        },
    },
};
const ifUnmodifiedSince = {
    parameterPath: ["options", "modifiedAccessConditions", "ifUnmodifiedSince"],
    mapper: {
        serializedName: "If-Unmodified-Since",
        xmlName: "If-Unmodified-Since",
        type: {
            name: "DateTimeRfc1123",
        },
    },
};
const comp6 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "metadata",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const comp7 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "acl",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const containerAcl = {
    parameterPath: ["options", "containerAcl"],
    mapper: {
        serializedName: "containerAcl",
        xmlName: "SignedIdentifiers",
        xmlIsWrapped: true,
        xmlElementName: "SignedIdentifier",
        type: {
            name: "Sequence",
            element: {
                type: {
                    name: "Composite",
                    className: "SignedIdentifier",
                },
            },
        },
    },
};
const comp8 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "undelete",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const deletedContainerName = {
    parameterPath: ["options", "deletedContainerName"],
    mapper: {
        serializedName: "x-ms-deleted-container-name",
        xmlName: "x-ms-deleted-container-name",
        type: {
            name: "String",
        },
    },
};
const deletedContainerVersion = {
    parameterPath: ["options", "deletedContainerVersion"],
    mapper: {
        serializedName: "x-ms-deleted-container-version",
        xmlName: "x-ms-deleted-container-version",
        type: {
            name: "String",
        },
    },
};
const comp9 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "rename",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const sourceContainerName = {
    parameterPath: "sourceContainerName",
    mapper: {
        serializedName: "x-ms-source-container-name",
        required: true,
        xmlName: "x-ms-source-container-name",
        type: {
            name: "String",
        },
    },
};
const sourceLeaseId = {
    parameterPath: ["options", "sourceLeaseId"],
    mapper: {
        serializedName: "x-ms-source-lease-id",
        xmlName: "x-ms-source-lease-id",
        type: {
            name: "String",
        },
    },
};
const comp10 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "lease",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const action = {
    parameterPath: "action",
    mapper: {
        defaultValue: "acquire",
        isConstant: true,
        serializedName: "x-ms-lease-action",
        type: {
            name: "String",
        },
    },
};
const duration = {
    parameterPath: ["options", "duration"],
    mapper: {
        serializedName: "x-ms-lease-duration",
        xmlName: "x-ms-lease-duration",
        type: {
            name: "Number",
        },
    },
};
const proposedLeaseId = {
    parameterPath: ["options", "proposedLeaseId"],
    mapper: {
        serializedName: "x-ms-proposed-lease-id",
        xmlName: "x-ms-proposed-lease-id",
        type: {
            name: "String",
        },
    },
};
const action1 = {
    parameterPath: "action",
    mapper: {
        defaultValue: "release",
        isConstant: true,
        serializedName: "x-ms-lease-action",
        type: {
            name: "String",
        },
    },
};
const leaseId1 = {
    parameterPath: "leaseId",
    mapper: {
        serializedName: "x-ms-lease-id",
        required: true,
        xmlName: "x-ms-lease-id",
        type: {
            name: "String",
        },
    },
};
const action2 = {
    parameterPath: "action",
    mapper: {
        defaultValue: "renew",
        isConstant: true,
        serializedName: "x-ms-lease-action",
        type: {
            name: "String",
        },
    },
};
const action3 = {
    parameterPath: "action",
    mapper: {
        defaultValue: "break",
        isConstant: true,
        serializedName: "x-ms-lease-action",
        type: {
            name: "String",
        },
    },
};
const breakPeriod = {
    parameterPath: ["options", "breakPeriod"],
    mapper: {
        serializedName: "x-ms-lease-break-period",
        xmlName: "x-ms-lease-break-period",
        type: {
            name: "Number",
        },
    },
};
const action4 = {
    parameterPath: "action",
    mapper: {
        defaultValue: "change",
        isConstant: true,
        serializedName: "x-ms-lease-action",
        type: {
            name: "String",
        },
    },
};
const proposedLeaseId1 = {
    parameterPath: "proposedLeaseId",
    mapper: {
        serializedName: "x-ms-proposed-lease-id",
        required: true,
        xmlName: "x-ms-proposed-lease-id",
        type: {
            name: "String",
        },
    },
};
const include1 = {
    parameterPath: ["options", "include"],
    mapper: {
        serializedName: "include",
        xmlName: "include",
        xmlElementName: "ListBlobsIncludeItem",
        type: {
            name: "Sequence",
            element: {
                type: {
                    name: "Enum",
                    allowedValues: [
                        "copy",
                        "deleted",
                        "metadata",
                        "snapshots",
                        "uncommittedblobs",
                        "versions",
                        "tags",
                        "immutabilitypolicy",
                        "legalhold",
                        "deletedwithversions",
                    ],
                },
            },
        },
    },
    collectionFormat: "CSV",
};
const startFrom = {
    parameterPath: ["options", "startFrom"],
    mapper: {
        serializedName: "startFrom",
        xmlName: "startFrom",
        type: {
            name: "String",
        },
    },
};
const delimiter = {
    parameterPath: "delimiter",
    mapper: {
        serializedName: "delimiter",
        required: true,
        xmlName: "delimiter",
        type: {
            name: "String",
        },
    },
};
const snapshot = {
    parameterPath: ["options", "snapshot"],
    mapper: {
        serializedName: "snapshot",
        xmlName: "snapshot",
        type: {
            name: "String",
        },
    },
};
const versionId = {
    parameterPath: ["options", "versionId"],
    mapper: {
        serializedName: "versionid",
        xmlName: "versionid",
        type: {
            name: "String",
        },
    },
};
const range = {
    parameterPath: ["options", "range"],
    mapper: {
        serializedName: "x-ms-range",
        xmlName: "x-ms-range",
        type: {
            name: "String",
        },
    },
};
const rangeGetContentMD5 = {
    parameterPath: ["options", "rangeGetContentMD5"],
    mapper: {
        serializedName: "x-ms-range-get-content-md5",
        xmlName: "x-ms-range-get-content-md5",
        type: {
            name: "Boolean",
        },
    },
};
const rangeGetContentCRC64 = {
    parameterPath: ["options", "rangeGetContentCRC64"],
    mapper: {
        serializedName: "x-ms-range-get-content-crc64",
        xmlName: "x-ms-range-get-content-crc64",
        type: {
            name: "Boolean",
        },
    },
};
const encryptionKey = {
    parameterPath: ["options", "cpkInfo", "encryptionKey"],
    mapper: {
        serializedName: "x-ms-encryption-key",
        xmlName: "x-ms-encryption-key",
        type: {
            name: "String",
        },
    },
};
const encryptionKeySha256 = {
    parameterPath: ["options", "cpkInfo", "encryptionKeySha256"],
    mapper: {
        serializedName: "x-ms-encryption-key-sha256",
        xmlName: "x-ms-encryption-key-sha256",
        type: {
            name: "String",
        },
    },
};
const encryptionAlgorithm = {
    parameterPath: ["options", "cpkInfo", "encryptionAlgorithm"],
    mapper: {
        serializedName: "x-ms-encryption-algorithm",
        xmlName: "x-ms-encryption-algorithm",
        type: {
            name: "String",
        },
    },
};
const ifMatch = {
    parameterPath: ["options", "modifiedAccessConditions", "ifMatch"],
    mapper: {
        serializedName: "If-Match",
        xmlName: "If-Match",
        type: {
            name: "String",
        },
    },
};
const ifNoneMatch = {
    parameterPath: ["options", "modifiedAccessConditions", "ifNoneMatch"],
    mapper: {
        serializedName: "If-None-Match",
        xmlName: "If-None-Match",
        type: {
            name: "String",
        },
    },
};
const ifTags = {
    parameterPath: ["options", "modifiedAccessConditions", "ifTags"],
    mapper: {
        serializedName: "x-ms-if-tags",
        xmlName: "x-ms-if-tags",
        type: {
            name: "String",
        },
    },
};
const deleteSnapshots = {
    parameterPath: ["options", "deleteSnapshots"],
    mapper: {
        serializedName: "x-ms-delete-snapshots",
        xmlName: "x-ms-delete-snapshots",
        type: {
            name: "Enum",
            allowedValues: ["include", "only"],
        },
    },
};
const blobDeleteType = {
    parameterPath: ["options", "blobDeleteType"],
    mapper: {
        serializedName: "deletetype",
        xmlName: "deletetype",
        type: {
            name: "String",
        },
    },
};
const comp11 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "expiry",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const expiryOptions = {
    parameterPath: "expiryOptions",
    mapper: {
        serializedName: "x-ms-expiry-option",
        required: true,
        xmlName: "x-ms-expiry-option",
        type: {
            name: "String",
        },
    },
};
const expiresOn = {
    parameterPath: ["options", "expiresOn"],
    mapper: {
        serializedName: "x-ms-expiry-time",
        xmlName: "x-ms-expiry-time",
        type: {
            name: "String",
        },
    },
};
const blobCacheControl = {
    parameterPath: ["options", "blobHttpHeaders", "blobCacheControl"],
    mapper: {
        serializedName: "x-ms-blob-cache-control",
        xmlName: "x-ms-blob-cache-control",
        type: {
            name: "String",
        },
    },
};
const blobContentType = {
    parameterPath: ["options", "blobHttpHeaders", "blobContentType"],
    mapper: {
        serializedName: "x-ms-blob-content-type",
        xmlName: "x-ms-blob-content-type",
        type: {
            name: "String",
        },
    },
};
const blobContentMD5 = {
    parameterPath: ["options", "blobHttpHeaders", "blobContentMD5"],
    mapper: {
        serializedName: "x-ms-blob-content-md5",
        xmlName: "x-ms-blob-content-md5",
        type: {
            name: "ByteArray",
        },
    },
};
const blobContentEncoding = {
    parameterPath: ["options", "blobHttpHeaders", "blobContentEncoding"],
    mapper: {
        serializedName: "x-ms-blob-content-encoding",
        xmlName: "x-ms-blob-content-encoding",
        type: {
            name: "String",
        },
    },
};
const blobContentLanguage = {
    parameterPath: ["options", "blobHttpHeaders", "blobContentLanguage"],
    mapper: {
        serializedName: "x-ms-blob-content-language",
        xmlName: "x-ms-blob-content-language",
        type: {
            name: "String",
        },
    },
};
const blobContentDisposition = {
    parameterPath: ["options", "blobHttpHeaders", "blobContentDisposition"],
    mapper: {
        serializedName: "x-ms-blob-content-disposition",
        xmlName: "x-ms-blob-content-disposition",
        type: {
            name: "String",
        },
    },
};
const comp12 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "immutabilityPolicies",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const immutabilityPolicyExpiry = {
    parameterPath: ["options", "immutabilityPolicyExpiry"],
    mapper: {
        serializedName: "x-ms-immutability-policy-until-date",
        xmlName: "x-ms-immutability-policy-until-date",
        type: {
            name: "DateTimeRfc1123",
        },
    },
};
const immutabilityPolicyMode = {
    parameterPath: ["options", "immutabilityPolicyMode"],
    mapper: {
        serializedName: "x-ms-immutability-policy-mode",
        xmlName: "x-ms-immutability-policy-mode",
        type: {
            name: "Enum",
            allowedValues: ["Mutable", "Unlocked", "Locked"],
        },
    },
};
const comp13 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "legalhold",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const legalHold = {
    parameterPath: "legalHold",
    mapper: {
        serializedName: "x-ms-legal-hold",
        required: true,
        xmlName: "x-ms-legal-hold",
        type: {
            name: "Boolean",
        },
    },
};
const encryptionScope = {
    parameterPath: ["options", "encryptionScope"],
    mapper: {
        serializedName: "x-ms-encryption-scope",
        xmlName: "x-ms-encryption-scope",
        type: {
            name: "String",
        },
    },
};
const comp14 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "snapshot",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const tier = {
    parameterPath: ["options", "tier"],
    mapper: {
        serializedName: "x-ms-access-tier",
        xmlName: "x-ms-access-tier",
        type: {
            name: "Enum",
            allowedValues: [
                "P4",
                "P6",
                "P10",
                "P15",
                "P20",
                "P30",
                "P40",
                "P50",
                "P60",
                "P70",
                "P80",
                "Hot",
                "Cool",
                "Archive",
                "Cold",
            ],
        },
    },
};
const rehydratePriority = {
    parameterPath: ["options", "rehydratePriority"],
    mapper: {
        serializedName: "x-ms-rehydrate-priority",
        xmlName: "x-ms-rehydrate-priority",
        type: {
            name: "Enum",
            allowedValues: ["High", "Standard"],
        },
    },
};
const sourceIfModifiedSince = {
    parameterPath: [
        "options",
        "sourceModifiedAccessConditions",
        "sourceIfModifiedSince",
    ],
    mapper: {
        serializedName: "x-ms-source-if-modified-since",
        xmlName: "x-ms-source-if-modified-since",
        type: {
            name: "DateTimeRfc1123",
        },
    },
};
const sourceIfUnmodifiedSince = {
    parameterPath: [
        "options",
        "sourceModifiedAccessConditions",
        "sourceIfUnmodifiedSince",
    ],
    mapper: {
        serializedName: "x-ms-source-if-unmodified-since",
        xmlName: "x-ms-source-if-unmodified-since",
        type: {
            name: "DateTimeRfc1123",
        },
    },
};
const sourceIfMatch = {
    parameterPath: ["options", "sourceModifiedAccessConditions", "sourceIfMatch"],
    mapper: {
        serializedName: "x-ms-source-if-match",
        xmlName: "x-ms-source-if-match",
        type: {
            name: "String",
        },
    },
};
const sourceIfNoneMatch = {
    parameterPath: [
        "options",
        "sourceModifiedAccessConditions",
        "sourceIfNoneMatch",
    ],
    mapper: {
        serializedName: "x-ms-source-if-none-match",
        xmlName: "x-ms-source-if-none-match",
        type: {
            name: "String",
        },
    },
};
const sourceIfTags = {
    parameterPath: ["options", "sourceModifiedAccessConditions", "sourceIfTags"],
    mapper: {
        serializedName: "x-ms-source-if-tags",
        xmlName: "x-ms-source-if-tags",
        type: {
            name: "String",
        },
    },
};
const copySource = {
    parameterPath: "copySource",
    mapper: {
        serializedName: "x-ms-copy-source",
        required: true,
        xmlName: "x-ms-copy-source",
        type: {
            name: "String",
        },
    },
};
const blobTagsString = {
    parameterPath: ["options", "blobTagsString"],
    mapper: {
        serializedName: "x-ms-tags",
        xmlName: "x-ms-tags",
        type: {
            name: "String",
        },
    },
};
const sealBlob = {
    parameterPath: ["options", "sealBlob"],
    mapper: {
        serializedName: "x-ms-seal-blob",
        xmlName: "x-ms-seal-blob",
        type: {
            name: "Boolean",
        },
    },
};
const legalHold1 = {
    parameterPath: ["options", "legalHold"],
    mapper: {
        serializedName: "x-ms-legal-hold",
        xmlName: "x-ms-legal-hold",
        type: {
            name: "Boolean",
        },
    },
};
const xMsRequiresSync = {
    parameterPath: "xMsRequiresSync",
    mapper: {
        defaultValue: "true",
        isConstant: true,
        serializedName: "x-ms-requires-sync",
        type: {
            name: "String",
        },
    },
};
const sourceContentMD5 = {
    parameterPath: ["options", "sourceContentMD5"],
    mapper: {
        serializedName: "x-ms-source-content-md5",
        xmlName: "x-ms-source-content-md5",
        type: {
            name: "ByteArray",
        },
    },
};
const copySourceAuthorization = {
    parameterPath: ["options", "copySourceAuthorization"],
    mapper: {
        serializedName: "x-ms-copy-source-authorization",
        xmlName: "x-ms-copy-source-authorization",
        type: {
            name: "String",
        },
    },
};
const copySourceTags = {
    parameterPath: ["options", "copySourceTags"],
    mapper: {
        serializedName: "x-ms-copy-source-tag-option",
        xmlName: "x-ms-copy-source-tag-option",
        type: {
            name: "Enum",
            allowedValues: ["REPLACE", "COPY"],
        },
    },
};
const fileRequestIntent = {
    parameterPath: ["options", "fileRequestIntent"],
    mapper: {
        serializedName: "x-ms-file-request-intent",
        xmlName: "x-ms-file-request-intent",
        type: {
            name: "String",
        },
    },
};
const comp15 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "copy",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const copyActionAbortConstant = {
    parameterPath: "copyActionAbortConstant",
    mapper: {
        defaultValue: "abort",
        isConstant: true,
        serializedName: "x-ms-copy-action",
        type: {
            name: "String",
        },
    },
};
const copyId = {
    parameterPath: "copyId",
    mapper: {
        serializedName: "copyid",
        required: true,
        xmlName: "copyid",
        type: {
            name: "String",
        },
    },
};
const comp16 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "tier",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const tier1 = {
    parameterPath: "tier",
    mapper: {
        serializedName: "x-ms-access-tier",
        required: true,
        xmlName: "x-ms-access-tier",
        type: {
            name: "Enum",
            allowedValues: [
                "P4",
                "P6",
                "P10",
                "P15",
                "P20",
                "P30",
                "P40",
                "P50",
                "P60",
                "P70",
                "P80",
                "Hot",
                "Cool",
                "Archive",
                "Cold",
            ],
        },
    },
};
const queryRequest = {
    parameterPath: ["options", "queryRequest"],
    mapper: QueryRequest,
};
const comp17 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "query",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const comp18 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "tags",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const ifModifiedSince1 = {
    parameterPath: ["options", "blobModifiedAccessConditions", "ifModifiedSince"],
    mapper: {
        serializedName: "x-ms-blob-if-modified-since",
        xmlName: "x-ms-blob-if-modified-since",
        type: {
            name: "DateTimeRfc1123",
        },
    },
};
const ifUnmodifiedSince1 = {
    parameterPath: [
        "options",
        "blobModifiedAccessConditions",
        "ifUnmodifiedSince",
    ],
    mapper: {
        serializedName: "x-ms-blob-if-unmodified-since",
        xmlName: "x-ms-blob-if-unmodified-since",
        type: {
            name: "DateTimeRfc1123",
        },
    },
};
const ifMatch1 = {
    parameterPath: ["options", "blobModifiedAccessConditions", "ifMatch"],
    mapper: {
        serializedName: "x-ms-blob-if-match",
        xmlName: "x-ms-blob-if-match",
        type: {
            name: "String",
        },
    },
};
const ifNoneMatch1 = {
    parameterPath: ["options", "blobModifiedAccessConditions", "ifNoneMatch"],
    mapper: {
        serializedName: "x-ms-blob-if-none-match",
        xmlName: "x-ms-blob-if-none-match",
        type: {
            name: "String",
        },
    },
};
const tags = {
    parameterPath: ["options", "tags"],
    mapper: BlobTags,
};
const transactionalContentMD5 = {
    parameterPath: ["options", "transactionalContentMD5"],
    mapper: {
        serializedName: "Content-MD5",
        xmlName: "Content-MD5",
        type: {
            name: "ByteArray",
        },
    },
};
const transactionalContentCrc64 = {
    parameterPath: ["options", "transactionalContentCrc64"],
    mapper: {
        serializedName: "x-ms-content-crc64",
        xmlName: "x-ms-content-crc64",
        type: {
            name: "ByteArray",
        },
    },
};
const blobType = {
    parameterPath: "blobType",
    mapper: {
        defaultValue: "PageBlob",
        isConstant: true,
        serializedName: "x-ms-blob-type",
        type: {
            name: "String",
        },
    },
};
const blobContentLength = {
    parameterPath: "blobContentLength",
    mapper: {
        serializedName: "x-ms-blob-content-length",
        required: true,
        xmlName: "x-ms-blob-content-length",
        type: {
            name: "Number",
        },
    },
};
const blobSequenceNumber = {
    parameterPath: ["options", "blobSequenceNumber"],
    mapper: {
        defaultValue: 0,
        serializedName: "x-ms-blob-sequence-number",
        xmlName: "x-ms-blob-sequence-number",
        type: {
            name: "Number",
        },
    },
};
const contentType1 = {
    parameterPath: ["options", "contentType"],
    mapper: {
        defaultValue: "application/octet-stream",
        isConstant: true,
        serializedName: "Content-Type",
        type: {
            name: "String",
        },
    },
};
const body1 = {
    parameterPath: "body",
    mapper: {
        serializedName: "body",
        required: true,
        xmlName: "body",
        type: {
            name: "Stream",
        },
    },
};
const accept2 = {
    parameterPath: "accept",
    mapper: {
        defaultValue: "application/xml",
        isConstant: true,
        serializedName: "Accept",
        type: {
            name: "String",
        },
    },
};
const comp19 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "page",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const pageWrite = {
    parameterPath: "pageWrite",
    mapper: {
        defaultValue: "update",
        isConstant: true,
        serializedName: "x-ms-page-write",
        type: {
            name: "String",
        },
    },
};
const ifSequenceNumberLessThanOrEqualTo = {
    parameterPath: [
        "options",
        "sequenceNumberAccessConditions",
        "ifSequenceNumberLessThanOrEqualTo",
    ],
    mapper: {
        serializedName: "x-ms-if-sequence-number-le",
        xmlName: "x-ms-if-sequence-number-le",
        type: {
            name: "Number",
        },
    },
};
const ifSequenceNumberLessThan = {
    parameterPath: [
        "options",
        "sequenceNumberAccessConditions",
        "ifSequenceNumberLessThan",
    ],
    mapper: {
        serializedName: "x-ms-if-sequence-number-lt",
        xmlName: "x-ms-if-sequence-number-lt",
        type: {
            name: "Number",
        },
    },
};
const ifSequenceNumberEqualTo = {
    parameterPath: [
        "options",
        "sequenceNumberAccessConditions",
        "ifSequenceNumberEqualTo",
    ],
    mapper: {
        serializedName: "x-ms-if-sequence-number-eq",
        xmlName: "x-ms-if-sequence-number-eq",
        type: {
            name: "Number",
        },
    },
};
const pageWrite1 = {
    parameterPath: "pageWrite",
    mapper: {
        defaultValue: "clear",
        isConstant: true,
        serializedName: "x-ms-page-write",
        type: {
            name: "String",
        },
    },
};
const sourceUrl = {
    parameterPath: "sourceUrl",
    mapper: {
        serializedName: "x-ms-copy-source",
        required: true,
        xmlName: "x-ms-copy-source",
        type: {
            name: "String",
        },
    },
};
const sourceRange = {
    parameterPath: "sourceRange",
    mapper: {
        serializedName: "x-ms-source-range",
        required: true,
        xmlName: "x-ms-source-range",
        type: {
            name: "String",
        },
    },
};
const sourceContentCrc64 = {
    parameterPath: ["options", "sourceContentCrc64"],
    mapper: {
        serializedName: "x-ms-source-content-crc64",
        xmlName: "x-ms-source-content-crc64",
        type: {
            name: "ByteArray",
        },
    },
};
const range1 = {
    parameterPath: "range",
    mapper: {
        serializedName: "x-ms-range",
        required: true,
        xmlName: "x-ms-range",
        type: {
            name: "String",
        },
    },
};
const comp20 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "pagelist",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const prevsnapshot = {
    parameterPath: ["options", "prevsnapshot"],
    mapper: {
        serializedName: "prevsnapshot",
        xmlName: "prevsnapshot",
        type: {
            name: "String",
        },
    },
};
const prevSnapshotUrl = {
    parameterPath: ["options", "prevSnapshotUrl"],
    mapper: {
        serializedName: "x-ms-previous-snapshot-url",
        xmlName: "x-ms-previous-snapshot-url",
        type: {
            name: "String",
        },
    },
};
const sequenceNumberAction = {
    parameterPath: "sequenceNumberAction",
    mapper: {
        serializedName: "x-ms-sequence-number-action",
        required: true,
        xmlName: "x-ms-sequence-number-action",
        type: {
            name: "Enum",
            allowedValues: ["max", "update", "increment"],
        },
    },
};
const comp21 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "incrementalcopy",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const blobType1 = {
    parameterPath: "blobType",
    mapper: {
        defaultValue: "AppendBlob",
        isConstant: true,
        serializedName: "x-ms-blob-type",
        type: {
            name: "String",
        },
    },
};
const comp22 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "appendblock",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const maxSize = {
    parameterPath: ["options", "appendPositionAccessConditions", "maxSize"],
    mapper: {
        serializedName: "x-ms-blob-condition-maxsize",
        xmlName: "x-ms-blob-condition-maxsize",
        type: {
            name: "Number",
        },
    },
};
const appendPosition = {
    parameterPath: [
        "options",
        "appendPositionAccessConditions",
        "appendPosition",
    ],
    mapper: {
        serializedName: "x-ms-blob-condition-appendpos",
        xmlName: "x-ms-blob-condition-appendpos",
        type: {
            name: "Number",
        },
    },
};
const sourceRange1 = {
    parameterPath: ["options", "sourceRange"],
    mapper: {
        serializedName: "x-ms-source-range",
        xmlName: "x-ms-source-range",
        type: {
            name: "String",
        },
    },
};
const comp23 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "seal",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const blobType2 = {
    parameterPath: "blobType",
    mapper: {
        defaultValue: "BlockBlob",
        isConstant: true,
        serializedName: "x-ms-blob-type",
        type: {
            name: "String",
        },
    },
};
const copySourceBlobProperties = {
    parameterPath: ["options", "copySourceBlobProperties"],
    mapper: {
        serializedName: "x-ms-copy-source-blob-properties",
        xmlName: "x-ms-copy-source-blob-properties",
        type: {
            name: "Boolean",
        },
    },
};
const comp24 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "block",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const blockId = {
    parameterPath: "blockId",
    mapper: {
        serializedName: "blockid",
        required: true,
        xmlName: "blockid",
        type: {
            name: "String",
        },
    },
};
const blocks = {
    parameterPath: "blocks",
    mapper: BlockLookupList,
};
const comp25 = {
    parameterPath: "comp",
    mapper: {
        defaultValue: "blocklist",
        isConstant: true,
        serializedName: "comp",
        type: {
            name: "String",
        },
    },
};
const listType = {
    parameterPath: "listType",
    mapper: {
        defaultValue: "committed",
        serializedName: "blocklisttype",
        required: true,
        xmlName: "blocklisttype",
        type: {
            name: "Enum",
            allowedValues: ["committed", "uncommitted", "all"],
        },
    },
};
//# sourceMappingURL=parameters.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/operations/service.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */



/** Class containing Service operations. */
class ServiceImpl {
    client;
    /**
     * Initialize a new instance of the class Service class.
     * @param client Reference to the service client
     */
    constructor(client) {
        this.client = client;
    }
    /**
     * Sets properties for a storage account's Blob service endpoint, including properties for Storage
     * Analytics and CORS (Cross-Origin Resource Sharing) rules
     * @param blobServiceProperties The StorageService properties.
     * @param options The options parameters.
     */
    setProperties(blobServiceProperties, options) {
        return this.client.sendOperationRequest({ blobServiceProperties, options }, setPropertiesOperationSpec);
    }
    /**
     * gets the properties of a storage account's Blob service, including properties for Storage Analytics
     * and CORS (Cross-Origin Resource Sharing) rules.
     * @param options The options parameters.
     */
    getProperties(options) {
        return this.client.sendOperationRequest({ options }, getPropertiesOperationSpec);
    }
    /**
     * Retrieves statistics related to replication for the Blob service. It is only available on the
     * secondary location endpoint when read-access geo-redundant replication is enabled for the storage
     * account.
     * @param options The options parameters.
     */
    getStatistics(options) {
        return this.client.sendOperationRequest({ options }, getStatisticsOperationSpec);
    }
    /**
     * The List Containers Segment operation returns a list of the containers under the specified account
     * @param options The options parameters.
     */
    listContainersSegment(options) {
        return this.client.sendOperationRequest({ options }, listContainersSegmentOperationSpec);
    }
    /**
     * Retrieves a user delegation key for the Blob service. This is only a valid operation when using
     * bearer token authentication.
     * @param keyInfo Key information
     * @param options The options parameters.
     */
    getUserDelegationKey(keyInfo, options) {
        return this.client.sendOperationRequest({ keyInfo, options }, getUserDelegationKeyOperationSpec);
    }
    /**
     * Returns the sku name and account kind
     * @param options The options parameters.
     */
    getAccountInfo(options) {
        return this.client.sendOperationRequest({ options }, getAccountInfoOperationSpec);
    }
    /**
     * The Batch operation allows multiple API calls to be embedded into a single HTTP request.
     * @param contentLength The length of the request.
     * @param multipartContentType Required. The value of this header must be multipart/mixed with a batch
     *                             boundary. Example header value: multipart/mixed; boundary=batch_<GUID>
     * @param body Initial data
     * @param options The options parameters.
     */
    submitBatch(contentLength, multipartContentType, body, options) {
        return this.client.sendOperationRequest({ contentLength, multipartContentType, body, options }, submitBatchOperationSpec);
    }
    /**
     * The Filter Blobs operation enables callers to list blobs across all containers whose tags match a
     * given search expression.  Filter blobs searches across all containers within a storage account but
     * can be scoped within the expression to a single container.
     * @param options The options parameters.
     */
    filterBlobs(options) {
        return this.client.sendOperationRequest({ options }, filterBlobsOperationSpec);
    }
}
// Operation Specifications
const xmlSerializer = createSerializer(mappers_namespaceObject, /* isXml */ true);
const setPropertiesOperationSpec = {
    path: "/",
    httpMethod: "PUT",
    responses: {
        202: {
            headersMapper: ServiceSetPropertiesHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ServiceSetPropertiesExceptionHeaders,
        },
    },
    requestBody: blobServiceProperties,
    queryParameters: [
        restype,
        comp,
        timeoutInSeconds,
    ],
    urlParameters: [url],
    headerParameters: [
        contentType,
        accept,
        version,
        requestId,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "xml",
    serializer: xmlSerializer,
};
const getPropertiesOperationSpec = {
    path: "/",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: BlobServiceProperties,
            headersMapper: ServiceGetPropertiesHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ServiceGetPropertiesExceptionHeaders,
        },
    },
    queryParameters: [
        restype,
        comp,
        timeoutInSeconds,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
    ],
    isXML: true,
    serializer: xmlSerializer,
};
const getStatisticsOperationSpec = {
    path: "/",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: BlobServiceStatistics,
            headersMapper: ServiceGetStatisticsHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ServiceGetStatisticsExceptionHeaders,
        },
    },
    queryParameters: [
        restype,
        timeoutInSeconds,
        comp1,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
    ],
    isXML: true,
    serializer: xmlSerializer,
};
const listContainersSegmentOperationSpec = {
    path: "/",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: ListContainersSegmentResponse,
            headersMapper: ServiceListContainersSegmentHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ServiceListContainersSegmentExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        comp2,
        prefix,
        marker,
        maxPageSize,
        include,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
    ],
    isXML: true,
    serializer: xmlSerializer,
};
const getUserDelegationKeyOperationSpec = {
    path: "/",
    httpMethod: "POST",
    responses: {
        200: {
            bodyMapper: UserDelegationKey,
            headersMapper: ServiceGetUserDelegationKeyHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ServiceGetUserDelegationKeyExceptionHeaders,
        },
    },
    requestBody: keyInfo,
    queryParameters: [
        restype,
        timeoutInSeconds,
        comp3,
    ],
    urlParameters: [url],
    headerParameters: [
        contentType,
        accept,
        version,
        requestId,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "xml",
    serializer: xmlSerializer,
};
const getAccountInfoOperationSpec = {
    path: "/",
    httpMethod: "GET",
    responses: {
        200: {
            headersMapper: ServiceGetAccountInfoHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ServiceGetAccountInfoExceptionHeaders,
        },
    },
    queryParameters: [
        comp,
        timeoutInSeconds,
        restype1,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
    ],
    isXML: true,
    serializer: xmlSerializer,
};
const submitBatchOperationSpec = {
    path: "/",
    httpMethod: "POST",
    responses: {
        202: {
            bodyMapper: {
                type: { name: "Stream" },
                serializedName: "parsedResponse",
            },
            headersMapper: ServiceSubmitBatchHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ServiceSubmitBatchExceptionHeaders,
        },
    },
    requestBody: body,
    queryParameters: [timeoutInSeconds, comp4],
    urlParameters: [url],
    headerParameters: [
        accept,
        version,
        requestId,
        contentLength,
        multipartContentType,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "xml",
    serializer: xmlSerializer,
};
const filterBlobsOperationSpec = {
    path: "/",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: FilterBlobSegment,
            headersMapper: ServiceFilterBlobsHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ServiceFilterBlobsExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        marker,
        maxPageSize,
        comp5,
        where,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
    ],
    isXML: true,
    serializer: xmlSerializer,
};
//# sourceMappingURL=service.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/operations/container.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */



/** Class containing Container operations. */
class ContainerImpl {
    client;
    /**
     * Initialize a new instance of the class Container class.
     * @param client Reference to the service client
     */
    constructor(client) {
        this.client = client;
    }
    /**
     * creates a new container under the specified account. If the container with the same name already
     * exists, the operation fails
     * @param options The options parameters.
     */
    create(options) {
        return this.client.sendOperationRequest({ options }, createOperationSpec);
    }
    /**
     * returns all user-defined metadata and system properties for the specified container. The data
     * returned does not include the container's list of blobs
     * @param options The options parameters.
     */
    getProperties(options) {
        return this.client.sendOperationRequest({ options }, container_getPropertiesOperationSpec);
    }
    /**
     * operation marks the specified container for deletion. The container and any blobs contained within
     * it are later deleted during garbage collection
     * @param options The options parameters.
     */
    delete(options) {
        return this.client.sendOperationRequest({ options }, deleteOperationSpec);
    }
    /**
     * operation sets one or more user-defined name-value pairs for the specified container.
     * @param options The options parameters.
     */
    setMetadata(options) {
        return this.client.sendOperationRequest({ options }, setMetadataOperationSpec);
    }
    /**
     * gets the permissions for the specified container. The permissions indicate whether container data
     * may be accessed publicly.
     * @param options The options parameters.
     */
    getAccessPolicy(options) {
        return this.client.sendOperationRequest({ options }, getAccessPolicyOperationSpec);
    }
    /**
     * sets the permissions for the specified container. The permissions indicate whether blobs in a
     * container may be accessed publicly.
     * @param options The options parameters.
     */
    setAccessPolicy(options) {
        return this.client.sendOperationRequest({ options }, setAccessPolicyOperationSpec);
    }
    /**
     * Restores a previously-deleted container.
     * @param options The options parameters.
     */
    restore(options) {
        return this.client.sendOperationRequest({ options }, restoreOperationSpec);
    }
    /**
     * Renames an existing container.
     * @param sourceContainerName Required.  Specifies the name of the container to rename.
     * @param options The options parameters.
     */
    rename(sourceContainerName, options) {
        return this.client.sendOperationRequest({ sourceContainerName, options }, renameOperationSpec);
    }
    /**
     * The Batch operation allows multiple API calls to be embedded into a single HTTP request.
     * @param contentLength The length of the request.
     * @param multipartContentType Required. The value of this header must be multipart/mixed with a batch
     *                             boundary. Example header value: multipart/mixed; boundary=batch_<GUID>
     * @param body Initial data
     * @param options The options parameters.
     */
    submitBatch(contentLength, multipartContentType, body, options) {
        return this.client.sendOperationRequest({ contentLength, multipartContentType, body, options }, container_submitBatchOperationSpec);
    }
    /**
     * The Filter Blobs operation enables callers to list blobs in a container whose tags match a given
     * search expression.  Filter blobs searches within the given container.
     * @param options The options parameters.
     */
    filterBlobs(options) {
        return this.client.sendOperationRequest({ options }, container_filterBlobsOperationSpec);
    }
    /**
     * [Update] establishes and manages a lock on a container for delete operations. The lock duration can
     * be 15 to 60 seconds, or can be infinite
     * @param options The options parameters.
     */
    acquireLease(options) {
        return this.client.sendOperationRequest({ options }, acquireLeaseOperationSpec);
    }
    /**
     * [Update] establishes and manages a lock on a container for delete operations. The lock duration can
     * be 15 to 60 seconds, or can be infinite
     * @param leaseId Specifies the current lease ID on the resource.
     * @param options The options parameters.
     */
    releaseLease(leaseId, options) {
        return this.client.sendOperationRequest({ leaseId, options }, releaseLeaseOperationSpec);
    }
    /**
     * [Update] establishes and manages a lock on a container for delete operations. The lock duration can
     * be 15 to 60 seconds, or can be infinite
     * @param leaseId Specifies the current lease ID on the resource.
     * @param options The options parameters.
     */
    renewLease(leaseId, options) {
        return this.client.sendOperationRequest({ leaseId, options }, renewLeaseOperationSpec);
    }
    /**
     * [Update] establishes and manages a lock on a container for delete operations. The lock duration can
     * be 15 to 60 seconds, or can be infinite
     * @param options The options parameters.
     */
    breakLease(options) {
        return this.client.sendOperationRequest({ options }, breakLeaseOperationSpec);
    }
    /**
     * [Update] establishes and manages a lock on a container for delete operations. The lock duration can
     * be 15 to 60 seconds, or can be infinite
     * @param leaseId Specifies the current lease ID on the resource.
     * @param proposedLeaseId Proposed lease ID, in a GUID string format. The Blob service returns 400
     *                        (Invalid request) if the proposed lease ID is not in the correct format. See Guid Constructor
     *                        (String) for a list of valid GUID string formats.
     * @param options The options parameters.
     */
    changeLease(leaseId, proposedLeaseId, options) {
        return this.client.sendOperationRequest({ leaseId, proposedLeaseId, options }, changeLeaseOperationSpec);
    }
    /**
     * [Update] The List Blobs operation returns a list of the blobs under the specified container
     * @param options The options parameters.
     */
    listBlobFlatSegment(options) {
        return this.client.sendOperationRequest({ options }, listBlobFlatSegmentOperationSpec);
    }
    /**
     * [Update] The List Blobs operation returns a list of the blobs under the specified container
     * @param delimiter When the request includes this parameter, the operation returns a BlobPrefix
     *                  element in the response body that acts as a placeholder for all blobs whose names begin with the
     *                  same substring up to the appearance of the delimiter character. The delimiter may be a single
     *                  character or a string.
     * @param options The options parameters.
     */
    listBlobHierarchySegment(delimiter, options) {
        return this.client.sendOperationRequest({ delimiter, options }, listBlobHierarchySegmentOperationSpec);
    }
    /**
     * Returns the sku name and account kind
     * @param options The options parameters.
     */
    getAccountInfo(options) {
        return this.client.sendOperationRequest({ options }, container_getAccountInfoOperationSpec);
    }
}
// Operation Specifications
const container_xmlSerializer = createSerializer(mappers_namespaceObject, /* isXml */ true);
const createOperationSpec = {
    path: "/{containerName}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: ContainerCreateHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerCreateExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, restype2],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        metadata,
        parameters_access,
        defaultEncryptionScope,
        preventEncryptionScopeOverride,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const container_getPropertiesOperationSpec = {
    path: "/{containerName}",
    httpMethod: "GET",
    responses: {
        200: {
            headersMapper: ContainerGetPropertiesHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerGetPropertiesExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, restype2],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const deleteOperationSpec = {
    path: "/{containerName}",
    httpMethod: "DELETE",
    responses: {
        202: {
            headersMapper: ContainerDeleteHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerDeleteExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, restype2],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const setMetadataOperationSpec = {
    path: "/{containerName}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: ContainerSetMetadataHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerSetMetadataExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        restype2,
        comp6,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        metadata,
        leaseId,
        ifModifiedSince,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const getAccessPolicyOperationSpec = {
    path: "/{containerName}",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: {
                type: {
                    name: "Sequence",
                    element: {
                        type: { name: "Composite", className: "SignedIdentifier" },
                    },
                },
                serializedName: "SignedIdentifiers",
                xmlName: "SignedIdentifiers",
                xmlIsWrapped: true,
                xmlElementName: "SignedIdentifier",
            },
            headersMapper: ContainerGetAccessPolicyHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerGetAccessPolicyExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        restype2,
        comp7,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const setAccessPolicyOperationSpec = {
    path: "/{containerName}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: ContainerSetAccessPolicyHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerSetAccessPolicyExceptionHeaders,
        },
    },
    requestBody: containerAcl,
    queryParameters: [
        timeoutInSeconds,
        restype2,
        comp7,
    ],
    urlParameters: [url],
    headerParameters: [
        contentType,
        accept,
        version,
        requestId,
        parameters_access,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "xml",
    serializer: container_xmlSerializer,
};
const restoreOperationSpec = {
    path: "/{containerName}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: ContainerRestoreHeaders,
        },
        default: {
            bodyMapper: StorageError,
