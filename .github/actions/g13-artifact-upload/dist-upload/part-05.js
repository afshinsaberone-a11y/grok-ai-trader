    // after byte in input are not in the ranges
    // 0x30 (0) to 0x39 (9), 0x41 (A) to 0x46 (F),
    // and 0x61 (a) to 0x66 (f), all inclusive, append byte
    // to output.
    } else if (
      byte === 0x25 &&
      !(isHexCharByte(input[i + 1]) && isHexCharByte(input[i + 2]))
    ) {
      output[j++] = 0x25

    // 3. Otherwise:
    } else {
      // 1. Let bytePoint be the two bytes after byte in input,
      // decoded, and then interpreted as hexadecimal number.
      // 2. Append a byte whose value is bytePoint to output.
      output[j++] = (hexByteToNumber(input[i + 1]) << 4) | hexByteToNumber(input[i + 2])

      // 3. Skip the next two bytes in input.
      i += 2
    }
  }

  // 3. Return output.
  return length === j ? output : output.subarray(0, j)
}

// https://mimesniff.spec.whatwg.org/#parse-a-mime-type
/** @param {string} input */
function parseMIMEType (input) {
  // 1. Remove any leading and trailing HTTP whitespace
  // from input.
  input = removeHTTPWhitespace(input, true, true)

  // 2. Let position be a position variable for input,
  // initially pointing at the start of input.
  const position = { position: 0 }

  // 3. Let type be the result of collecting a sequence
  // of code points that are not U+002F (/) from
  // input, given position.
  const type = collectASequenceOfCodePointsFast(
    '/',
    input,
    position
  )

  // 4. If type is the empty string or does not solely
  // contain HTTP token code points, then return failure.
  // https://mimesniff.spec.whatwg.org/#http-token-code-point
  if (type.length === 0 || !HTTP_TOKEN_CODEPOINTS.test(type)) {
    return 'failure'
  }

  // 5. If position is past the end of input, then return
  // failure
  if (position.position > input.length) {
    return 'failure'
  }

  // 6. Advance position by 1. (This skips past U+002F (/).)
  position.position++

  // 7. Let subtype be the result of collecting a sequence of
  // code points that are not U+003B (;) from input, given
  // position.
  let subtype = collectASequenceOfCodePointsFast(
    ';',
    input,
    position
  )

  // 8. Remove any trailing HTTP whitespace from subtype.
  subtype = removeHTTPWhitespace(subtype, false, true)

  // 9. If subtype is the empty string or does not solely
  // contain HTTP token code points, then return failure.
  if (subtype.length === 0 || !HTTP_TOKEN_CODEPOINTS.test(subtype)) {
    return 'failure'
  }

  const typeLowercase = type.toLowerCase()
  const subtypeLowercase = subtype.toLowerCase()

  // 10. Let mimeType be a new MIME type record whose type
  // is type, in ASCII lowercase, and subtype is subtype,
  // in ASCII lowercase.
  // https://mimesniff.spec.whatwg.org/#mime-type
  const mimeType = {
    type: typeLowercase,
    subtype: subtypeLowercase,
    /** @type {Map<string, string>} */
    parameters: new Map(),
    // https://mimesniff.spec.whatwg.org/#mime-type-essence
    essence: `${typeLowercase}/${subtypeLowercase}`
  }

  // 11. While position is not past the end of input:
  while (position.position < input.length) {
    // 1. Advance position by 1. (This skips past U+003B (;).)
    position.position++

    // 2. Collect a sequence of code points that are HTTP
    // whitespace from input given position.
    collectASequenceOfCodePoints(
      // https://fetch.spec.whatwg.org/#http-whitespace
      char => HTTP_WHITESPACE_REGEX.test(char),
      input,
      position
    )

    // 3. Let parameterName be the result of collecting a
    // sequence of code points that are not U+003B (;)
    // or U+003D (=) from input, given position.
    let parameterName = collectASequenceOfCodePoints(
      (char) => char !== ';' && char !== '=',
      input,
      position
    )

    // 4. Set parameterName to parameterName, in ASCII
    // lowercase.
    parameterName = parameterName.toLowerCase()

    // 5. If position is not past the end of input, then:
    if (position.position < input.length) {
      // 1. If the code point at position within input is
      // U+003B (;), then continue.
      if (input[position.position] === ';') {
        continue
      }

      // 2. Advance position by 1. (This skips past U+003D (=).)
      position.position++
    }

    // 6. If position is past the end of input, then break.
    if (position.position > input.length) {
      break
    }

    // 7. Let parameterValue be null.
    let parameterValue = null

    // 8. If the code point at position within input is
    // U+0022 ("), then:
    if (input[position.position] === '"') {
      // 1. Set parameterValue to the result of collecting
      // an HTTP quoted string from input, given position
      // and the extract-value flag.
      parameterValue = collectAnHTTPQuotedString(input, position, true)

      // 2. Collect a sequence of code points that are not
      // U+003B (;) from input, given position.
      collectASequenceOfCodePointsFast(
        ';',
        input,
        position
      )

    // 9. Otherwise:
    } else {
      // 1. Set parameterValue to the result of collecting
      // a sequence of code points that are not U+003B (;)
      // from input, given position.
      parameterValue = collectASequenceOfCodePointsFast(
        ';',
        input,
        position
      )

      // 2. Remove any trailing HTTP whitespace from parameterValue.
      parameterValue = removeHTTPWhitespace(parameterValue, false, true)

      // 3. If parameterValue is the empty string, then continue.
      if (parameterValue.length === 0) {
        continue
      }
    }

    // 10. If all of the following are true
    // - parameterName is not the empty string
    // - parameterName solely contains HTTP token code points
    // - parameterValue solely contains HTTP quoted-string token code points
    // - mimeType’s parameters[parameterName] does not exist
    // then set mimeType’s parameters[parameterName] to parameterValue.
    if (
      parameterName.length !== 0 &&
      HTTP_TOKEN_CODEPOINTS.test(parameterName) &&
      (parameterValue.length === 0 || HTTP_QUOTED_STRING_TOKENS.test(parameterValue)) &&
      !mimeType.parameters.has(parameterName)
    ) {
      mimeType.parameters.set(parameterName, parameterValue)
    }
  }

  // 12. Return mimeType.
  return mimeType
}

// https://infra.spec.whatwg.org/#forgiving-base64-decode
/** @param {string} data */
function forgivingBase64 (data) {
  // 1. Remove all ASCII whitespace from data.
  data = data.replace(ASCII_WHITESPACE_REPLACE_REGEX, '')  // eslint-disable-line

  let dataLength = data.length
  // 2. If data’s code point length divides by 4 leaving
  // no remainder, then:
  if (dataLength % 4 === 0) {
    // 1. If data ends with one or two U+003D (=) code points,
    // then remove them from data.
    if (data.charCodeAt(dataLength - 1) === 0x003D) {
      --dataLength
      if (data.charCodeAt(dataLength - 1) === 0x003D) {
        --dataLength
      }
    }
  }

  // 3. If data’s code point length divides by 4 leaving
  // a remainder of 1, then return failure.
  if (dataLength % 4 === 1) {
    return 'failure'
  }

  // 4. If data contains a code point that is not one of
  //  U+002B (+)
  //  U+002F (/)
  //  ASCII alphanumeric
  // then return failure.
  if (/[^+/0-9A-Za-z]/.test(data.length === dataLength ? data : data.substring(0, dataLength))) {
    return 'failure'
  }

  const buffer = Buffer.from(data, 'base64')
  return new Uint8Array(buffer.buffer, buffer.byteOffset, buffer.byteLength)
}

// https://fetch.spec.whatwg.org/#collect-an-http-quoted-string
// tests: https://fetch.spec.whatwg.org/#example-http-quoted-string
/**
 * @param {string} input
 * @param {{ position: number }} position
 * @param {boolean?} extractValue
 */
function collectAnHTTPQuotedString (input, position, extractValue) {
  // 1. Let positionStart be position.
  const positionStart = position.position

  // 2. Let value be the empty string.
  let value = ''

  // 3. Assert: the code point at position within input
  // is U+0022 (").
  assert(input[position.position] === '"')

  // 4. Advance position by 1.
  position.position++

  // 5. While true:
  while (true) {
    // 1. Append the result of collecting a sequence of code points
    // that are not U+0022 (") or U+005C (\) from input, given
    // position, to value.
    value += collectASequenceOfCodePoints(
      (char) => char !== '"' && char !== '\\',
      input,
      position
    )

    // 2. If position is past the end of input, then break.
    if (position.position >= input.length) {
      break
    }

    // 3. Let quoteOrBackslash be the code point at position within
    // input.
    const quoteOrBackslash = input[position.position]

    // 4. Advance position by 1.
    position.position++

    // 5. If quoteOrBackslash is U+005C (\), then:
    if (quoteOrBackslash === '\\') {
      // 1. If position is past the end of input, then append
      // U+005C (\) to value and break.
      if (position.position >= input.length) {
        value += '\\'
        break
      }

      // 2. Append the code point at position within input to value.
      value += input[position.position]

      // 3. Advance position by 1.
      position.position++

    // 6. Otherwise:
    } else {
      // 1. Assert: quoteOrBackslash is U+0022 (").
      assert(quoteOrBackslash === '"')

      // 2. Break.
      break
    }
  }

  // 6. If the extract-value flag is set, then return value.
  if (extractValue) {
    return value
  }

  // 7. Return the code points from positionStart to position,
  // inclusive, within input.
  return input.slice(positionStart, position.position)
}

/**
 * @see https://mimesniff.spec.whatwg.org/#serialize-a-mime-type
 */
function serializeAMimeType (mimeType) {
  assert(mimeType !== 'failure')
  const { parameters, essence } = mimeType

  // 1. Let serialization be the concatenation of mimeType’s
  //    type, U+002F (/), and mimeType’s subtype.
  let serialization = essence

  // 2. For each name → value of mimeType’s parameters:
  for (let [name, value] of parameters.entries()) {
    // 1. Append U+003B (;) to serialization.
    serialization += ';'

    // 2. Append name to serialization.
    serialization += name

    // 3. Append U+003D (=) to serialization.
    serialization += '='

    // 4. If value does not solely contain HTTP token code
    //    points or value is the empty string, then:
    if (!HTTP_TOKEN_CODEPOINTS.test(value)) {
      // 1. Precede each occurrence of U+0022 (") or
      //    U+005C (\) in value with U+005C (\).
      value = value.replace(/(\\|")/g, '\\$1')

      // 2. Prepend U+0022 (") to value.
      value = '"' + value

      // 3. Append U+0022 (") to value.
      value += '"'
    }

    // 5. Append value to serialization.
    serialization += value
  }

  // 3. Return serialization.
  return serialization
}

/**
 * @see https://fetch.spec.whatwg.org/#http-whitespace
 * @param {number} char
 */
function isHTTPWhiteSpace (char) {
  // "\r\n\t "
  return char === 0x00d || char === 0x00a || char === 0x009 || char === 0x020
}

/**
 * @see https://fetch.spec.whatwg.org/#http-whitespace
 * @param {string} str
 * @param {boolean} [leading=true]
 * @param {boolean} [trailing=true]
 */
function removeHTTPWhitespace (str, leading = true, trailing = true) {
  return removeChars(str, leading, trailing, isHTTPWhiteSpace)
}

/**
 * @see https://infra.spec.whatwg.org/#ascii-whitespace
 * @param {number} char
 */
function isASCIIWhitespace (char) {
  // "\r\n\t\f "
  return char === 0x00d || char === 0x00a || char === 0x009 || char === 0x00c || char === 0x020
}

/**
 * @see https://infra.spec.whatwg.org/#strip-leading-and-trailing-ascii-whitespace
 * @param {string} str
 * @param {boolean} [leading=true]
 * @param {boolean} [trailing=true]
 */
function removeASCIIWhitespace (str, leading = true, trailing = true) {
  return removeChars(str, leading, trailing, isASCIIWhitespace)
}

/**
 * @param {string} str
 * @param {boolean} leading
 * @param {boolean} trailing
 * @param {(charCode: number) => boolean} predicate
 * @returns
 */
function removeChars (str, leading, trailing, predicate) {
  let lead = 0
  let trail = str.length - 1

  if (leading) {
    while (lead < str.length && predicate(str.charCodeAt(lead))) lead++
  }

  if (trailing) {
    while (trail > 0 && predicate(str.charCodeAt(trail))) trail--
  }

  return lead === 0 && trail === str.length - 1 ? str : str.slice(lead, trail + 1)
}

/**
 * @see https://infra.spec.whatwg.org/#isomorphic-decode
 * @param {Uint8Array} input
 * @returns {string}
 */
function isomorphicDecode (input) {
  // 1. To isomorphic decode a byte sequence input, return a string whose code point
  //    length is equal to input’s length and whose code points have the same values
  //    as the values of input’s bytes, in the same order.
  const length = input.length
  if ((2 << 15) - 1 > length) {
    return String.fromCharCode.apply(null, input)
  }
  let result = ''; let i = 0
  let addition = (2 << 15) - 1
  while (i < length) {
    if (i + addition > length) {
      addition = length - i
    }
    result += String.fromCharCode.apply(null, input.subarray(i, i += addition))
  }
  return result
}

/**
 * @see https://mimesniff.spec.whatwg.org/#minimize-a-supported-mime-type
 * @param {Exclude<ReturnType<typeof parseMIMEType>, 'failure'>} mimeType
 */
function minimizeSupportedMimeType (mimeType) {
  switch (mimeType.essence) {
    case 'application/ecmascript':
    case 'application/javascript':
    case 'application/x-ecmascript':
    case 'application/x-javascript':
    case 'text/ecmascript':
    case 'text/javascript':
    case 'text/javascript1.0':
    case 'text/javascript1.1':
    case 'text/javascript1.2':
    case 'text/javascript1.3':
    case 'text/javascript1.4':
    case 'text/javascript1.5':
    case 'text/jscript':
    case 'text/livescript':
    case 'text/x-ecmascript':
    case 'text/x-javascript':
      // 1. If mimeType is a JavaScript MIME type, then return "text/javascript".
      return 'text/javascript'
    case 'application/json':
    case 'text/json':
      // 2. If mimeType is a JSON MIME type, then return "application/json".
      return 'application/json'
    case 'image/svg+xml':
      // 3. If mimeType’s essence is "image/svg+xml", then return "image/svg+xml".
      return 'image/svg+xml'
    case 'text/xml':
    case 'application/xml':
      // 4. If mimeType is an XML MIME type, then return "application/xml".
      return 'application/xml'
  }

  // 2. If mimeType is a JSON MIME type, then return "application/json".
  if (mimeType.subtype.endsWith('+json')) {
    return 'application/json'
  }

  // 4. If mimeType is an XML MIME type, then return "application/xml".
  if (mimeType.subtype.endsWith('+xml')) {
    return 'application/xml'
  }

  // 5. If mimeType is supported by the user agent, then return mimeType’s essence.
  // Technically, node doesn't support any mimetypes.

  // 6. Return the empty string.
  return ''
}

module.exports = {
  dataURLProcessor,
  URLSerializer,
  collectASequenceOfCodePoints,
  collectASequenceOfCodePointsFast,
  stringPercentDecode,
  parseMIMEType,
  collectAnHTTPQuotedString,
  serializeAMimeType,
  removeChars,
  removeHTTPWhitespace,
  minimizeSupportedMimeType,
  HTTP_TOKEN_CODEPOINTS,
  isomorphicDecode
}


/***/ }),

/***/ 6653:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { kConnected, kSize } = __nccwpck_require__(6443)

class CompatWeakRef {
  constructor (value) {
    this.value = value
  }

  deref () {
    return this.value[kConnected] === 0 && this.value[kSize] === 0
      ? undefined
      : this.value
  }
}

class CompatFinalizer {
  constructor (finalizer) {
    this.finalizer = finalizer
  }

  register (dispatcher, key) {
    if (dispatcher.on) {
      dispatcher.on('disconnect', () => {
        if (dispatcher[kConnected] === 0 && dispatcher[kSize] === 0) {
          this.finalizer(key)
        }
      })
    }
  }

  unregister (key) {}
}

module.exports = function () {
  // FIXME: remove workaround when the Node bug is backported to v18
  // https://github.com/nodejs/node/issues/49344#issuecomment-1741776308
  if (process.env.NODE_V8_COVERAGE && process.version.startsWith('v18')) {
    process._rawDebug('Using compatibility WeakRef and FinalizationRegistry')
    return {
      WeakRef: CompatWeakRef,
      FinalizationRegistry: CompatFinalizer
    }
  }
  return { WeakRef, FinalizationRegistry }
}


/***/ }),

/***/ 7114:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { Blob, File } = __nccwpck_require__(4573)
const { kState } = __nccwpck_require__(3627)
const { webidl } = __nccwpck_require__(5893)

// TODO(@KhafraDev): remove
class FileLike {
  constructor (blobLike, fileName, options = {}) {
    // TODO: argument idl type check

    // The File constructor is invoked with two or three parameters, depending
    // on whether the optional dictionary parameter is used. When the File()
    // constructor is invoked, user agents must run the following steps:

    // 1. Let bytes be the result of processing blob parts given fileBits and
    // options.

    // 2. Let n be the fileName argument to the constructor.
    const n = fileName

    // 3. Process FilePropertyBag dictionary argument by running the following
    // substeps:

    //    1. If the type member is provided and is not the empty string, let t
    //    be set to the type dictionary member. If t contains any characters
    //    outside the range U+0020 to U+007E, then set t to the empty string
    //    and return from these substeps.
    //    TODO
    const t = options.type

    //    2. Convert every character in t to ASCII lowercase.
    //    TODO

    //    3. If the lastModified member is provided, let d be set to the
    //    lastModified dictionary member. If it is not provided, set d to the
    //    current date and time represented as the number of milliseconds since
    //    the Unix Epoch (which is the equivalent of Date.now() [ECMA-262]).
    const d = options.lastModified ?? Date.now()

    // 4. Return a new File object F such that:
    // F refers to the bytes byte sequence.
    // F.size is set to the number of total bytes in bytes.
    // F.name is set to n.
    // F.type is set to t.
    // F.lastModified is set to d.

    this[kState] = {
      blobLike,
      name: n,
      type: t,
      lastModified: d
    }
  }

  stream (...args) {
    webidl.brandCheck(this, FileLike)

    return this[kState].blobLike.stream(...args)
  }

  arrayBuffer (...args) {
    webidl.brandCheck(this, FileLike)

    return this[kState].blobLike.arrayBuffer(...args)
  }

  slice (...args) {
    webidl.brandCheck(this, FileLike)

    return this[kState].blobLike.slice(...args)
  }

  text (...args) {
    webidl.brandCheck(this, FileLike)

    return this[kState].blobLike.text(...args)
  }

  get size () {
    webidl.brandCheck(this, FileLike)

    return this[kState].blobLike.size
  }

  get type () {
    webidl.brandCheck(this, FileLike)

    return this[kState].blobLike.type
  }

  get name () {
    webidl.brandCheck(this, FileLike)

    return this[kState].name
  }

  get lastModified () {
    webidl.brandCheck(this, FileLike)

    return this[kState].lastModified
  }

  get [Symbol.toStringTag] () {
    return 'File'
  }
}

webidl.converters.Blob = webidl.interfaceConverter(Blob)

// If this function is moved to ./util.js, some tools (such as
// rollup) will warn about circular dependencies. See:
// https://github.com/nodejs/undici/issues/1629
function isFileLike (object) {
  return (
    (object instanceof File) ||
    (
      object &&
      (typeof object.stream === 'function' ||
      typeof object.arrayBuffer === 'function') &&
      object[Symbol.toStringTag] === 'File'
    )
  )
}

module.exports = { FileLike, isFileLike }


/***/ }),

/***/ 116:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { isUSVString, bufferToLowerCasedHeaderName } = __nccwpck_require__(3440)
const { utf8DecodeBytes } = __nccwpck_require__(3168)
const { HTTP_TOKEN_CODEPOINTS, isomorphicDecode } = __nccwpck_require__(1900)
const { isFileLike } = __nccwpck_require__(7114)
const { makeEntry } = __nccwpck_require__(5910)
const assert = __nccwpck_require__(4589)
const { File: NodeFile } = __nccwpck_require__(4573)

const File = globalThis.File ?? NodeFile

const formDataNameBuffer = Buffer.from('form-data; name="')
const filenameBuffer = Buffer.from('; filename')
const dd = Buffer.from('--')
const ddcrlf = Buffer.from('--\r\n')

/**
 * @param {string} chars
 */
function isAsciiString (chars) {
  for (let i = 0; i < chars.length; ++i) {
    if ((chars.charCodeAt(i) & ~0x7F) !== 0) {
      return false
    }
  }
  return true
}

/**
 * @see https://andreubotella.github.io/multipart-form-data/#multipart-form-data-boundary
 * @param {string} boundary
 */
function validateBoundary (boundary) {
  const length = boundary.length

  // - its length is greater or equal to 27 and lesser or equal to 70, and
  if (length < 27 || length > 70) {
    return false
  }

  // - it is composed by bytes in the ranges 0x30 to 0x39, 0x41 to 0x5A, or
  //   0x61 to 0x7A, inclusive (ASCII alphanumeric), or which are 0x27 ('),
  //   0x2D (-) or 0x5F (_).
  for (let i = 0; i < length; ++i) {
    const cp = boundary.charCodeAt(i)

    if (!(
      (cp >= 0x30 && cp <= 0x39) ||
      (cp >= 0x41 && cp <= 0x5a) ||
      (cp >= 0x61 && cp <= 0x7a) ||
      cp === 0x27 ||
      cp === 0x2d ||
      cp === 0x5f
    )) {
      return false
    }
  }

  return true
}

/**
 * @see https://andreubotella.github.io/multipart-form-data/#multipart-form-data-parser
 * @param {Buffer} input
 * @param {ReturnType<import('./data-url')['parseMIMEType']>} mimeType
 */
function multipartFormDataParser (input, mimeType) {
  // 1. Assert: mimeType’s essence is "multipart/form-data".
  assert(mimeType !== 'failure' && mimeType.essence === 'multipart/form-data')

  const boundaryString = mimeType.parameters.get('boundary')

  // 2. If mimeType’s parameters["boundary"] does not exist, return failure.
  //    Otherwise, let boundary be the result of UTF-8 decoding mimeType’s
  //    parameters["boundary"].
  if (boundaryString === undefined) {
    return 'failure'
  }

  const boundary = Buffer.from(`--${boundaryString}`, 'utf8')

  // 3. Let entry list be an empty entry list.
  const entryList = []

  // 4. Let position be a pointer to a byte in input, initially pointing at
  //    the first byte.
  const position = { position: 0 }

  // Note: undici addition, allows leading and trailing CRLFs.
  while (input[position.position] === 0x0d && input[position.position + 1] === 0x0a) {
    position.position += 2
  }

  let trailing = input.length

  while (input[trailing - 1] === 0x0a && input[trailing - 2] === 0x0d) {
    trailing -= 2
  }

  if (trailing !== input.length) {
    input = input.subarray(0, trailing)
  }

  // 5. While true:
  while (true) {
    // 5.1. If position points to a sequence of bytes starting with 0x2D 0x2D
    //      (`--`) followed by boundary, advance position by 2 + the length of
    //      boundary. Otherwise, return failure.
    // Note: boundary is padded with 2 dashes already, no need to add 2.
    if (input.subarray(position.position, position.position + boundary.length).equals(boundary)) {
      position.position += boundary.length
    } else {
      return 'failure'
    }

    // 5.2. If position points to the sequence of bytes 0x2D 0x2D 0x0D 0x0A
    //      (`--` followed by CR LF) followed by the end of input, return entry list.
    // Note: a body does NOT need to end with CRLF. It can end with --.
    if (
      (position.position === input.length - 2 && bufferStartsWith(input, dd, position)) ||
      (position.position === input.length - 4 && bufferStartsWith(input, ddcrlf, position))
    ) {
      return entryList
    }

    // 5.3. If position does not point to a sequence of bytes starting with 0x0D
    //      0x0A (CR LF), return failure.
    if (input[position.position] !== 0x0d || input[position.position + 1] !== 0x0a) {
      return 'failure'
    }

    // 5.4. Advance position by 2. (This skips past the newline.)
    position.position += 2

    // 5.5. Let name, filename and contentType be the result of parsing
    //      multipart/form-data headers on input and position, if the result
    //      is not failure. Otherwise, return failure.
    const result = parseMultipartFormDataHeaders(input, position)

    if (result === 'failure') {
      return 'failure'
    }

    let { name, filename, contentType, encoding } = result

    // 5.6. Advance position by 2. (This skips past the empty line that marks
    //      the end of the headers.)
    position.position += 2

    // 5.7. Let body be the empty byte sequence.
    let body

    // 5.8. Body loop: While position is not past the end of input:
    // TODO: the steps here are completely wrong
    {
      const boundaryIndex = input.indexOf(boundary.subarray(2), position.position)

      if (boundaryIndex === -1) {
        return 'failure'
      }

      body = input.subarray(position.position, boundaryIndex - 4)

      position.position += body.length

      // Note: position must be advanced by the body's length before being
      // decoded, otherwise the parsing will fail.
      if (encoding === 'base64') {
        body = Buffer.from(body.toString(), 'base64')
      }
    }

    // 5.9. If position does not point to a sequence of bytes starting with
    //      0x0D 0x0A (CR LF), return failure. Otherwise, advance position by 2.
    if (input[position.position] !== 0x0d || input[position.position + 1] !== 0x0a) {
      return 'failure'
    } else {
      position.position += 2
    }

    // 5.10. If filename is not null:
    let value

    if (filename !== null) {
      // 5.10.1. If contentType is null, set contentType to "text/plain".
      contentType ??= 'text/plain'

      // 5.10.2. If contentType is not an ASCII string, set contentType to the empty string.

      // Note: `buffer.isAscii` can be used at zero-cost, but converting a string to a buffer is a high overhead.
      // Content-Type is a relatively small string, so it is faster to use `String#charCodeAt`.
      if (!isAsciiString(contentType)) {
        contentType = ''
      }

      // 5.10.3. Let value be a new File object with name filename, type contentType, and body body.
      value = new File([body], filename, { type: contentType })
    } else {
      // 5.11. Otherwise:

      // 5.11.1. Let value be the UTF-8 decoding without BOM of body.
      value = utf8DecodeBytes(Buffer.from(body))
    }

    // 5.12. Assert: name is a scalar value string and value is either a scalar value string or a File object.
    assert(isUSVString(name))
    assert((typeof value === 'string' && isUSVString(value)) || isFileLike(value))

    // 5.13. Create an entry with name and value, and append it to entry list.
    entryList.push(makeEntry(name, value, filename))
  }
}

/**
 * @see https://andreubotella.github.io/multipart-form-data/#parse-multipart-form-data-headers
 * @param {Buffer} input
 * @param {{ position: number }} position
 */
function parseMultipartFormDataHeaders (input, position) {
  // 1. Let name, filename and contentType be null.
  let name = null
  let filename = null
  let contentType = null
  let encoding = null

  // 2. While true:
  while (true) {
    // 2.1. If position points to a sequence of bytes starting with 0x0D 0x0A (CR LF):
    if (input[position.position] === 0x0d && input[position.position + 1] === 0x0a) {
      // 2.1.1. If name is null, return failure.
      if (name === null) {
        return 'failure'
      }

      // 2.1.2. Return name, filename and contentType.
      return { name, filename, contentType, encoding }
    }

    // 2.2. Let header name be the result of collecting a sequence of bytes that are
    //      not 0x0A (LF), 0x0D (CR) or 0x3A (:), given position.
    let headerName = collectASequenceOfBytes(
      (char) => char !== 0x0a && char !== 0x0d && char !== 0x3a,
      input,
      position
    )

    // 2.3. Remove any HTTP tab or space bytes from the start or end of header name.
    headerName = removeChars(headerName, true, true, (char) => char === 0x9 || char === 0x20)

    // 2.4. If header name does not match the field-name token production, return failure.
    if (!HTTP_TOKEN_CODEPOINTS.test(headerName.toString())) {
      return 'failure'
    }

    // 2.5. If the byte at position is not 0x3A (:), return failure.
    if (input[position.position] !== 0x3a) {
      return 'failure'
    }

    // 2.6. Advance position by 1.
    position.position++

    // 2.7. Collect a sequence of bytes that are HTTP tab or space bytes given position.
    //      (Do nothing with those bytes.)
    collectASequenceOfBytes(
      (char) => char === 0x20 || char === 0x09,
      input,
      position
    )

    // 2.8. Byte-lowercase header name and switch on the result:
    switch (bufferToLowerCasedHeaderName(headerName)) {
      case 'content-disposition': {
        // 1. Set name and filename to null.
        name = filename = null

        // 2. If position does not point to a sequence of bytes starting with
        //    `form-data; name="`, return failure.
        if (!bufferStartsWith(input, formDataNameBuffer, position)) {
          return 'failure'
        }

        // 3. Advance position so it points at the byte after the next 0x22 (")
        //    byte (the one in the sequence of bytes matched above).
        position.position += 17

        // 4. Set name to the result of parsing a multipart/form-data name given
        //    input and position, if the result is not failure. Otherwise, return
        //    failure.
        name = parseMultipartFormDataName(input, position)

        if (name === null) {
          return 'failure'
        }

        // 5. If position points to a sequence of bytes starting with `; filename="`:
        if (bufferStartsWith(input, filenameBuffer, position)) {
          // Note: undici also handles filename*
          let check = position.position + filenameBuffer.length

          if (input[check] === 0x2a) {
            position.position += 1
            check += 1
          }

          if (input[check] !== 0x3d || input[check + 1] !== 0x22) { // ="
            return 'failure'
          }

          // 1. Advance position so it points at the byte after the next 0x22 (") byte
          //    (the one in the sequence of bytes matched above).
          position.position += 12

          // 2. Set filename to the result of parsing a multipart/form-data name given
          //    input and position, if the result is not failure. Otherwise, return failure.
          filename = parseMultipartFormDataName(input, position)

          if (filename === null) {
            return 'failure'
          }
        }

        break
      }
      case 'content-type': {
        // 1. Let header value be the result of collecting a sequence of bytes that are
        //    not 0x0A (LF) or 0x0D (CR), given position.
        let headerValue = collectASequenceOfBytes(
          (char) => char !== 0x0a && char !== 0x0d,
          input,
          position
        )

        // 2. Remove any HTTP tab or space bytes from the end of header value.
        headerValue = removeChars(headerValue, false, true, (char) => char === 0x9 || char === 0x20)

        // 3. Set contentType to the isomorphic decoding of header value.
        contentType = isomorphicDecode(headerValue)

        break
      }
      case 'content-transfer-encoding': {
        let headerValue = collectASequenceOfBytes(
          (char) => char !== 0x0a && char !== 0x0d,
          input,
          position
        )

        headerValue = removeChars(headerValue, false, true, (char) => char === 0x9 || char === 0x20)

        encoding = isomorphicDecode(headerValue)

        break
      }
      default: {
        // Collect a sequence of bytes that are not 0x0A (LF) or 0x0D (CR), given position.
        // (Do nothing with those bytes.)
        collectASequenceOfBytes(
          (char) => char !== 0x0a && char !== 0x0d,
          input,
          position
        )
      }
    }

    // 2.9. If position does not point to a sequence of bytes starting with 0x0D 0x0A
    //      (CR LF), return failure. Otherwise, advance position by 2 (past the newline).
    if (input[position.position] !== 0x0d && input[position.position + 1] !== 0x0a) {
      return 'failure'
    } else {
      position.position += 2
    }
  }
}

/**
 * @see https://andreubotella.github.io/multipart-form-data/#parse-a-multipart-form-data-name
 * @param {Buffer} input
 * @param {{ position: number }} position
 */
function parseMultipartFormDataName (input, position) {
  // 1. Assert: The byte at (position - 1) is 0x22 (").
  assert(input[position.position - 1] === 0x22)

  // 2. Let name be the result of collecting a sequence of bytes that are not 0x0A (LF), 0x0D (CR) or 0x22 ("), given position.
  /** @type {string | Buffer} */
  let name = collectASequenceOfBytes(
    (char) => char !== 0x0a && char !== 0x0d && char !== 0x22,
    input,
    position
  )

  // 3. If the byte at position is not 0x22 ("), return failure. Otherwise, advance position by 1.
  if (input[position.position] !== 0x22) {
    return null // name could be 'failure'
  } else {
    position.position++
  }

  // 4. Replace any occurrence of the following subsequences in name with the given byte:
  // - `%0A`: 0x0A (LF)
  // - `%0D`: 0x0D (CR)
  // - `%22`: 0x22 (")
  name = new TextDecoder().decode(name)
    .replace(/%0A/ig, '\n')
    .replace(/%0D/ig, '\r')
    .replace(/%22/g, '"')

  // 5. Return the UTF-8 decoding without BOM of name.
  return name
}

/**
 * @param {(char: number) => boolean} condition
 * @param {Buffer} input
 * @param {{ position: number }} position
 */
function collectASequenceOfBytes (condition, input, position) {
  let start = position.position

  while (start < input.length && condition(input[start])) {
    ++start
  }

  return input.subarray(position.position, (position.position = start))
}

/**
 * @param {Buffer} buf
 * @param {boolean} leading
 * @param {boolean} trailing
 * @param {(charCode: number) => boolean} predicate
 * @returns {Buffer}
 */
function removeChars (buf, leading, trailing, predicate) {
  let lead = 0
  let trail = buf.length - 1

  if (leading) {
    while (lead < buf.length && predicate(buf[lead])) lead++
  }

  if (trailing) {
    while (trail > 0 && predicate(buf[trail])) trail--
  }

  return lead === 0 && trail === buf.length - 1 ? buf : buf.subarray(lead, trail + 1)
}

/**
 * Checks if {@param buffer} starts with {@param start}
 * @param {Buffer} buffer
 * @param {Buffer} start
 * @param {{ position: number }} position
 */
function bufferStartsWith (buffer, start, position) {
  if (buffer.length < start.length) {
    return false
  }

  for (let i = 0; i < start.length; i++) {
    if (start[i] !== buffer[position.position + i]) {
      return false
    }
  }

  return true
}

module.exports = {
  multipartFormDataParser,
  validateBoundary
}


/***/ }),

/***/ 5910:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { isBlobLike, iteratorMixin } = __nccwpck_require__(3168)
const { kState } = __nccwpck_require__(3627)
const { kEnumerableProperty } = __nccwpck_require__(3440)
const { FileLike, isFileLike } = __nccwpck_require__(7114)
const { webidl } = __nccwpck_require__(5893)
const { File: NativeFile } = __nccwpck_require__(4573)
const nodeUtil = __nccwpck_require__(7975)

/** @type {globalThis['File']} */
const File = globalThis.File ?? NativeFile

// https://xhr.spec.whatwg.org/#formdata
class FormData {
  constructor (form) {
    webidl.util.markAsUncloneable(this)

    if (form !== undefined) {
      throw webidl.errors.conversionFailed({
        prefix: 'FormData constructor',
        argument: 'Argument 1',
        types: ['undefined']
      })
    }

    this[kState] = []
  }

  append (name, value, filename = undefined) {
    webidl.brandCheck(this, FormData)

    const prefix = 'FormData.append'
    webidl.argumentLengthCheck(arguments, 2, prefix)

    if (arguments.length === 3 && !isBlobLike(value)) {
      throw new TypeError(
        "Failed to execute 'append' on 'FormData': parameter 2 is not of type 'Blob'"
      )
    }

    // 1. Let value be value if given; otherwise blobValue.

    name = webidl.converters.USVString(name, prefix, 'name')
    value = isBlobLike(value)
      ? webidl.converters.Blob(value, prefix, 'value', { strict: false })
      : webidl.converters.USVString(value, prefix, 'value')
    filename = arguments.length === 3
      ? webidl.converters.USVString(filename, prefix, 'filename')
      : undefined

    // 2. Let entry be the result of creating an entry with
    // name, value, and filename if given.
    const entry = makeEntry(name, value, filename)

    // 3. Append entry to this’s entry list.
    this[kState].push(entry)
  }

  delete (name) {
    webidl.brandCheck(this, FormData)

    const prefix = 'FormData.delete'
    webidl.argumentLengthCheck(arguments, 1, prefix)

    name = webidl.converters.USVString(name, prefix, 'name')

    // The delete(name) method steps are to remove all entries whose name
    // is name from this’s entry list.
    this[kState] = this[kState].filter(entry => entry.name !== name)
  }

  get (name) {
    webidl.brandCheck(this, FormData)

    const prefix = 'FormData.get'
    webidl.argumentLengthCheck(arguments, 1, prefix)

    name = webidl.converters.USVString(name, prefix, 'name')

    // 1. If there is no entry whose name is name in this’s entry list,
    // then return null.
    const idx = this[kState].findIndex((entry) => entry.name === name)
    if (idx === -1) {
      return null
    }

    // 2. Return the value of the first entry whose name is name from
    // this’s entry list.
    return this[kState][idx].value
  }

  getAll (name) {
    webidl.brandCheck(this, FormData)

    const prefix = 'FormData.getAll'
    webidl.argumentLengthCheck(arguments, 1, prefix)

    name = webidl.converters.USVString(name, prefix, 'name')

    // 1. If there is no entry whose name is name in this’s entry list,
    // then return the empty list.
    // 2. Return the values of all entries whose name is name, in order,
    // from this’s entry list.
    return this[kState]
      .filter((entry) => entry.name === name)
      .map((entry) => entry.value)
  }

  has (name) {
    webidl.brandCheck(this, FormData)

    const prefix = 'FormData.has'
    webidl.argumentLengthCheck(arguments, 1, prefix)

    name = webidl.converters.USVString(name, prefix, 'name')

    // The has(name) method steps are to return true if there is an entry
    // whose name is name in this’s entry list; otherwise false.
    return this[kState].findIndex((entry) => entry.name === name) !== -1
  }

  set (name, value, filename = undefined) {
    webidl.brandCheck(this, FormData)

    const prefix = 'FormData.set'
    webidl.argumentLengthCheck(arguments, 2, prefix)

    if (arguments.length === 3 && !isBlobLike(value)) {
      throw new TypeError(
        "Failed to execute 'set' on 'FormData': parameter 2 is not of type 'Blob'"
      )
    }

    // The set(name, value) and set(name, blobValue, filename) method steps
    // are:

    // 1. Let value be value if given; otherwise blobValue.

    name = webidl.converters.USVString(name, prefix, 'name')
    value = isBlobLike(value)
      ? webidl.converters.Blob(value, prefix, 'name', { strict: false })
      : webidl.converters.USVString(value, prefix, 'name')
    filename = arguments.length === 3
      ? webidl.converters.USVString(filename, prefix, 'name')
      : undefined

    // 2. Let entry be the result of creating an entry with name, value, and
    // filename if given.
    const entry = makeEntry(name, value, filename)

    // 3. If there are entries in this’s entry list whose name is name, then
    // replace the first such entry with entry and remove the others.
    const idx = this[kState].findIndex((entry) => entry.name === name)
    if (idx !== -1) {
      this[kState] = [
        ...this[kState].slice(0, idx),
        entry,
        ...this[kState].slice(idx + 1).filter((entry) => entry.name !== name)
      ]
    } else {
      // 4. Otherwise, append entry to this’s entry list.
      this[kState].push(entry)
    }
  }

  [nodeUtil.inspect.custom] (depth, options) {
    const state = this[kState].reduce((a, b) => {
      if (a[b.name]) {
        if (Array.isArray(a[b.name])) {
          a[b.name].push(b.value)
        } else {
          a[b.name] = [a[b.name], b.value]
        }
      } else {
        a[b.name] = b.value
      }

      return a
    }, { __proto__: null })

    options.depth ??= depth
    options.colors ??= true

    const output = nodeUtil.formatWithOptions(options, state)

    // remove [Object null prototype]
    return `FormData ${output.slice(output.indexOf(']') + 2)}`
  }
}

iteratorMixin('FormData', FormData, kState, 'name', 'value')

Object.defineProperties(FormData.prototype, {
  append: kEnumerableProperty,
  delete: kEnumerableProperty,
  get: kEnumerableProperty,
  getAll: kEnumerableProperty,
  has: kEnumerableProperty,
  set: kEnumerableProperty,
  [Symbol.toStringTag]: {
    value: 'FormData',
    configurable: true
  }
})

/**
 * @see https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#create-an-entry
 * @param {string} name
 * @param {string|Blob} value
 * @param {?string} filename
 * @returns
 */
function makeEntry (name, value, filename) {
  // 1. Set name to the result of converting name into a scalar value string.
  // Note: This operation was done by the webidl converter USVString.

  // 2. If value is a string, then set value to the result of converting
  //    value into a scalar value string.
  if (typeof value === 'string') {
    // Note: This operation was done by the webidl converter USVString.
  } else {
    // 3. Otherwise:

    // 1. If value is not a File object, then set value to a new File object,
    //    representing the same bytes, whose name attribute value is "blob"
    if (!isFileLike(value)) {
      value = value instanceof Blob
        ? new File([value], 'blob', { type: value.type })
        : new FileLike(value, 'blob', { type: value.type })
    }

    // 2. If filename is given, then set value to a new File object,
    //    representing the same bytes, whose name attribute is filename.
    if (filename !== undefined) {
      /** @type {FilePropertyBag} */
      const options = {
        type: value.type,
        lastModified: value.lastModified
      }

      value = value instanceof NativeFile
        ? new File([value], filename, options)
        : new FileLike(value, filename, options)
    }
  }

  // 4. Return an entry whose name is name and whose value is value.
  return { name, value }
}

module.exports = { FormData, makeEntry }


/***/ }),

/***/ 1059:
/***/ ((module) => {



// In case of breaking changes, increase the version
// number to avoid conflicts.
const globalOrigin = Symbol.for('undici.globalOrigin.1')

function getGlobalOrigin () {
  return globalThis[globalOrigin]
}

function setGlobalOrigin (newOrigin) {
  if (newOrigin === undefined) {
    Object.defineProperty(globalThis, globalOrigin, {
      value: undefined,
      writable: true,
      enumerable: false,
      configurable: false
    })

    return
  }

  const parsedURL = new URL(newOrigin)

  if (parsedURL.protocol !== 'http:' && parsedURL.protocol !== 'https:') {
    throw new TypeError(`Only http & https urls are allowed, received ${parsedURL.protocol}`)
  }

  Object.defineProperty(globalThis, globalOrigin, {
    value: parsedURL,
    writable: true,
    enumerable: false,
    configurable: false
  })
}

module.exports = {
  getGlobalOrigin,
  setGlobalOrigin
}


/***/ }),

/***/ 660:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {

// https://github.com/Ethan-Arrowood/undici-fetch



const { kConstruct } = __nccwpck_require__(6443)
const { kEnumerableProperty } = __nccwpck_require__(3440)
const {
  iteratorMixin,
  isValidHeaderName,
  isValidHeaderValue
} = __nccwpck_require__(3168)
const { webidl } = __nccwpck_require__(5893)
const assert = __nccwpck_require__(4589)
const util = __nccwpck_require__(7975)

const kHeadersMap = Symbol('headers map')
const kHeadersSortedMap = Symbol('headers map sorted')

/**
 * @param {number} code
 */
function isHTTPWhiteSpaceCharCode (code) {
  return code === 0x00a || code === 0x00d || code === 0x009 || code === 0x020
}

/**
 * @see https://fetch.spec.whatwg.org/#concept-header-value-normalize
 * @param {string} potentialValue
 */
function headerValueNormalize (potentialValue) {
  //  To normalize a byte sequence potentialValue, remove
  //  any leading and trailing HTTP whitespace bytes from
  //  potentialValue.
  let i = 0; let j = potentialValue.length

  while (j > i && isHTTPWhiteSpaceCharCode(potentialValue.charCodeAt(j - 1))) --j
  while (j > i && isHTTPWhiteSpaceCharCode(potentialValue.charCodeAt(i))) ++i

  return i === 0 && j === potentialValue.length ? potentialValue : potentialValue.substring(i, j)
}

function fill (headers, object) {
  // To fill a Headers object headers with a given object object, run these steps:

  // 1. If object is a sequence, then for each header in object:
  // Note: webidl conversion to array has already been done.
  if (Array.isArray(object)) {
    for (let i = 0; i < object.length; ++i) {
      const header = object[i]
      // 1. If header does not contain exactly two items, then throw a TypeError.
      if (header.length !== 2) {
        throw webidl.errors.exception({
          header: 'Headers constructor',
          message: `expected name/value pair to be length 2, found ${header.length}.`
        })
      }

      // 2. Append (header’s first item, header’s second item) to headers.
      appendHeader(headers, header[0], header[1])
    }
  } else if (typeof object === 'object' && object !== null) {
    // Note: null should throw

    // 2. Otherwise, object is a record, then for each key → value in object,
    //    append (key, value) to headers
    const keys = Object.keys(object)
    for (let i = 0; i < keys.length; ++i) {
      appendHeader(headers, keys[i], object[keys[i]])
    }
  } else {
    throw webidl.errors.conversionFailed({
      prefix: 'Headers constructor',
      argument: 'Argument 1',
      types: ['sequence<sequence<ByteString>>', 'record<ByteString, ByteString>']
    })
  }
}

/**
 * @see https://fetch.spec.whatwg.org/#concept-headers-append
 */
function appendHeader (headers, name, value) {
  // 1. Normalize value.
  value = headerValueNormalize(value)

  // 2. If name is not a header name or value is not a
  //    header value, then throw a TypeError.
  if (!isValidHeaderName(name)) {
    throw webidl.errors.invalidArgument({
      prefix: 'Headers.append',
      value: name,
      type: 'header name'
    })
  } else if (!isValidHeaderValue(value)) {
    throw webidl.errors.invalidArgument({
      prefix: 'Headers.append',
      value,
      type: 'header value'
    })
  }

  // 3. If headers’s guard is "immutable", then throw a TypeError.
  // 4. Otherwise, if headers’s guard is "request" and name is a
  //    forbidden header name, return.
  // 5. Otherwise, if headers’s guard is "request-no-cors":
  //    TODO
  // Note: undici does not implement forbidden header names
  if (getHeadersGuard(headers) === 'immutable') {
    throw new TypeError('immutable')
  }

  // 6. Otherwise, if headers’s guard is "response" and name is a
  //    forbidden response-header name, return.

  // 7. Append (name, value) to headers’s header list.
  return getHeadersList(headers).append(name, value, false)

  // 8. If headers’s guard is "request-no-cors", then remove
  //    privileged no-CORS request headers from headers
}

function compareHeaderName (a, b) {
  return a[0] < b[0] ? -1 : 1
}

class HeadersList {
  /** @type {[string, string][]|null} */
  cookies = null

  constructor (init) {
    if (init instanceof HeadersList) {
      this[kHeadersMap] = new Map(init[kHeadersMap])
      this[kHeadersSortedMap] = init[kHeadersSortedMap]
      this.cookies = init.cookies === null ? null : [...init.cookies]
    } else {
      this[kHeadersMap] = new Map(init)
      this[kHeadersSortedMap] = null
    }
  }

  /**
   * @see https://fetch.spec.whatwg.org/#header-list-contains
   * @param {string} name
   * @param {boolean} isLowerCase
   */
  contains (name, isLowerCase) {
    // A header list list contains a header name name if list
    // contains a header whose name is a byte-case-insensitive
    // match for name.

    return this[kHeadersMap].has(isLowerCase ? name : name.toLowerCase())
  }

  clear () {
    this[kHeadersMap].clear()
    this[kHeadersSortedMap] = null
    this.cookies = null
  }

  /**
   * @see https://fetch.spec.whatwg.org/#concept-header-list-append
   * @param {string} name
   * @param {string} value
   * @param {boolean} isLowerCase
   */
  append (name, value, isLowerCase) {
    this[kHeadersSortedMap] = null

    // 1. If list contains name, then set name to the first such
    //    header’s name.
    const lowercaseName = isLowerCase ? name : name.toLowerCase()
    const exists = this[kHeadersMap].get(lowercaseName)

    // 2. Append (name, value) to list.
    if (exists) {
      const delimiter = lowercaseName === 'cookie' ? '; ' : ', '
      this[kHeadersMap].set(lowercaseName, {
        name: exists.name,
        value: `${exists.value}${delimiter}${value}`
      })
    } else {
      this[kHeadersMap].set(lowercaseName, { name, value })
    }

    if (lowercaseName === 'set-cookie') {
      (this.cookies ??= []).push(value)
    }
  }

  /**
   * @see https://fetch.spec.whatwg.org/#concept-header-list-set
   * @param {string} name
   * @param {string} value
   * @param {boolean} isLowerCase
   */
  set (name, value, isLowerCase) {
    this[kHeadersSortedMap] = null
    const lowercaseName = isLowerCase ? name : name.toLowerCase()

    if (lowercaseName === 'set-cookie') {
      this.cookies = [value]
    }

    // 1. If list contains name, then set the value of
    //    the first such header to value and remove the
    //    others.
    // 2. Otherwise, append header (name, value) to list.
    this[kHeadersMap].set(lowercaseName, { name, value })
  }

  /**
   * @see https://fetch.spec.whatwg.org/#concept-header-list-delete
   * @param {string} name
   * @param {boolean} isLowerCase
   */
  delete (name, isLowerCase) {
    this[kHeadersSortedMap] = null
    if (!isLowerCase) name = name.toLowerCase()

    if (name === 'set-cookie') {
      this.cookies = null
    }

    this[kHeadersMap].delete(name)
  }

  /**
   * @see https://fetch.spec.whatwg.org/#concept-header-list-get
   * @param {string} name
   * @param {boolean} isLowerCase
   * @returns {string | null}
   */
  get (name, isLowerCase) {
    // 1. If list does not contain name, then return null.
    // 2. Return the values of all headers in list whose name
    //    is a byte-case-insensitive match for name,
    //    separated from each other by 0x2C 0x20, in order.
    return this[kHeadersMap].get(isLowerCase ? name : name.toLowerCase())?.value ?? null
  }

  * [Symbol.iterator] () {
    // use the lowercased name
    for (const { 0: name, 1: { value } } of this[kHeadersMap]) {
      yield [name, value]
    }
  }

  get entries () {
    const headers = {}

    if (this[kHeadersMap].size !== 0) {
      for (const { name, value } of this[kHeadersMap].values()) {
        headers[name] = value
      }
    }

    return headers
  }

  rawValues () {
    return this[kHeadersMap].values()
  }

  get entriesList () {
    const headers = []

    if (this[kHeadersMap].size !== 0) {
      for (const { 0: lowerName, 1: { name, value } } of this[kHeadersMap]) {
        if (lowerName === 'set-cookie') {
          for (const cookie of this.cookies) {
            headers.push([name, cookie])
          }
        } else {
          headers.push([name, value])
        }
      }
    }

    return headers
  }

  // https://fetch.spec.whatwg.org/#convert-header-names-to-a-sorted-lowercase-set
  toSortedArray () {
    const size = this[kHeadersMap].size
    const array = new Array(size)
    // In most cases, you will use the fast-path.
    // fast-path: Use binary insertion sort for small arrays.
    if (size <= 32) {
      if (size === 0) {
        // If empty, it is an empty array. To avoid the first index assignment.
        return array
      }
      // Improve performance by unrolling loop and avoiding double-loop.
      // Double-loop-less version of the binary insertion sort.
      const iterator = this[kHeadersMap][Symbol.iterator]()
      const firstValue = iterator.next().value
      // set [name, value] to first index.
      array[0] = [firstValue[0], firstValue[1].value]
      // https://fetch.spec.whatwg.org/#concept-header-list-sort-and-combine
      // 3.2.2. Assert: value is non-null.
      assert(firstValue[1].value !== null)
      for (
        let i = 1, j = 0, right = 0, left = 0, pivot = 0, x, value;
        i < size;
        ++i
      ) {
        // get next value
        value = iterator.next().value
        // set [name, value] to current index.
        x = array[i] = [value[0], value[1].value]
        // https://fetch.spec.whatwg.org/#concept-header-list-sort-and-combine
        // 3.2.2. Assert: value is non-null.
        assert(x[1] !== null)
        left = 0
        right = i
        // binary search
        while (left < right) {
          // middle index
          pivot = left + ((right - left) >> 1)
          // compare header name
          if (array[pivot][0] <= x[0]) {
            left = pivot + 1
          } else {
            right = pivot
          }
        }
        if (i !== pivot) {
          j = i
          while (j > left) {
            array[j] = array[--j]
          }
          array[left] = x
        }
      }
      /* c8 ignore next 4 */
      if (!iterator.next().done) {
        // This is for debugging and will never be called.
        throw new TypeError('Unreachable')
      }
      return array
    } else {
      // This case would be a rare occurrence.
      // slow-path: fallback
      let i = 0
      for (const { 0: name, 1: { value } } of this[kHeadersMap]) {
        array[i++] = [name, value]
        // https://fetch.spec.whatwg.org/#concept-header-list-sort-and-combine
        // 3.2.2. Assert: value is non-null.
        assert(value !== null)
      }
      return array.sort(compareHeaderName)
    }
  }
}

// https://fetch.spec.whatwg.org/#headers-class
class Headers {
  #guard
  #headersList

  constructor (init = undefined) {
    webidl.util.markAsUncloneable(this)

    if (init === kConstruct) {
      return
    }

    this.#headersList = new HeadersList()

    // The new Headers(init) constructor steps are:

    // 1. Set this’s guard to "none".
    this.#guard = 'none'

    // 2. If init is given, then fill this with init.
    if (init !== undefined) {
      init = webidl.converters.HeadersInit(init, 'Headers contructor', 'init')
      fill(this, init)
    }
  }

  // https://fetch.spec.whatwg.org/#dom-headers-append
  append (name, value) {
    webidl.brandCheck(this, Headers)

    webidl.argumentLengthCheck(arguments, 2, 'Headers.append')

    const prefix = 'Headers.append'
    name = webidl.converters.ByteString(name, prefix, 'name')
    value = webidl.converters.ByteString(value, prefix, 'value')

    return appendHeader(this, name, value)
  }

  // https://fetch.spec.whatwg.org/#dom-headers-delete
  delete (name) {
    webidl.brandCheck(this, Headers)

    webidl.argumentLengthCheck(arguments, 1, 'Headers.delete')

    const prefix = 'Headers.delete'
    name = webidl.converters.ByteString(name, prefix, 'name')

    // 1. If name is not a header name, then throw a TypeError.
    if (!isValidHeaderName(name)) {
      throw webidl.errors.invalidArgument({
        prefix: 'Headers.delete',
        value: name,
        type: 'header name'
      })
    }

    // 2. If this’s guard is "immutable", then throw a TypeError.
    // 3. Otherwise, if this’s guard is "request" and name is a
    //    forbidden header name, return.
    // 4. Otherwise, if this’s guard is "request-no-cors", name
    //    is not a no-CORS-safelisted request-header name, and
    //    name is not a privileged no-CORS request-header name,
    //    return.
    // 5. Otherwise, if this’s guard is "response" and name is
    //    a forbidden response-header name, return.
    // Note: undici does not implement forbidden header names
    if (this.#guard === 'immutable') {
      throw new TypeError('immutable')
    }

    // 6. If this’s header list does not contain name, then
    //    return.
    if (!this.#headersList.contains(name, false)) {
      return
    }

    // 7. Delete name from this’s header list.
    // 8. If this’s guard is "request-no-cors", then remove
    //    privileged no-CORS request headers from this.
    this.#headersList.delete(name, false)
  }

  // https://fetch.spec.whatwg.org/#dom-headers-get
  get (name) {
    webidl.brandCheck(this, Headers)

    webidl.argumentLengthCheck(arguments, 1, 'Headers.get')

    const prefix = 'Headers.get'
    name = webidl.converters.ByteString(name, prefix, 'name')

    // 1. If name is not a header name, then throw a TypeError.
    if (!isValidHeaderName(name)) {
      throw webidl.errors.invalidArgument({
        prefix,
        value: name,
        type: 'header name'
      })
    }

    // 2. Return the result of getting name from this’s header
    //    list.
    return this.#headersList.get(name, false)
  }

  // https://fetch.spec.whatwg.org/#dom-headers-has
  has (name) {
    webidl.brandCheck(this, Headers)

    webidl.argumentLengthCheck(arguments, 1, 'Headers.has')

    const prefix = 'Headers.has'
    name = webidl.converters.ByteString(name, prefix, 'name')

    // 1. If name is not a header name, then throw a TypeError.
    if (!isValidHeaderName(name)) {
      throw webidl.errors.invalidArgument({
        prefix,
        value: name,
        type: 'header name'
      })
    }

    // 2. Return true if this’s header list contains name;
    //    otherwise false.
    return this.#headersList.contains(name, false)
  }

  // https://fetch.spec.whatwg.org/#dom-headers-set
  set (name, value) {
    webidl.brandCheck(this, Headers)

    webidl.argumentLengthCheck(arguments, 2, 'Headers.set')

    const prefix = 'Headers.set'
    name = webidl.converters.ByteString(name, prefix, 'name')
    value = webidl.converters.ByteString(value, prefix, 'value')

    // 1. Normalize value.
    value = headerValueNormalize(value)

    // 2. If name is not a header name or value is not a
    //    header value, then throw a TypeError.
    if (!isValidHeaderName(name)) {
      throw webidl.errors.invalidArgument({
        prefix,
        value: name,
        type: 'header name'
      })
    } else if (!isValidHeaderValue(value)) {
      throw webidl.errors.invalidArgument({
        prefix,
        value,
        type: 'header value'
      })
    }

    // 3. If this’s guard is "immutable", then throw a TypeError.
    // 4. Otherwise, if this’s guard is "request" and name is a
    //    forbidden header name, return.
    // 5. Otherwise, if this’s guard is "request-no-cors" and
    //    name/value is not a no-CORS-safelisted request-header,
    //    return.
    // 6. Otherwise, if this’s guard is "response" and name is a
    //    forbidden response-header name, return.
    // Note: undici does not implement forbidden header names
    if (this.#guard === 'immutable') {
      throw new TypeError('immutable')
    }

    // 7. Set (name, value) in this’s header list.
    // 8. If this’s guard is "request-no-cors", then remove
    //    privileged no-CORS request headers from this
    this.#headersList.set(name, value, false)
  }

  // https://fetch.spec.whatwg.org/#dom-headers-getsetcookie
  getSetCookie () {
    webidl.brandCheck(this, Headers)

    // 1. If this’s header list does not contain `Set-Cookie`, then return « ».
    // 2. Return the values of all headers in this’s header list whose name is
    //    a byte-case-insensitive match for `Set-Cookie`, in order.

    const list = this.#headersList.cookies

    if (list) {
      return [...list]
    }

    return []
  }

  // https://fetch.spec.whatwg.org/#concept-header-list-sort-and-combine
  get [kHeadersSortedMap] () {
    if (this.#headersList[kHeadersSortedMap]) {
      return this.#headersList[kHeadersSortedMap]
    }

    // 1. Let headers be an empty list of headers with the key being the name
    //    and value the value.
    const headers = []

    // 2. Let names be the result of convert header names to a sorted-lowercase
    //    set with all the names of the headers in list.
    const names = this.#headersList.toSortedArray()

    const cookies = this.#headersList.cookies

    // fast-path
    if (cookies === null || cookies.length === 1) {
      // Note: The non-null assertion of value has already been done by `HeadersList#toSortedArray`
      return (this.#headersList[kHeadersSortedMap] = names)
    }

    // 3. For each name of names:
    for (let i = 0; i < names.length; ++i) {
      const { 0: name, 1: value } = names[i]
      // 1. If name is `set-cookie`, then:
      if (name === 'set-cookie') {
        // 1. Let values be a list of all values of headers in list whose name
        //    is a byte-case-insensitive match for name, in order.

        // 2. For each value of values:
        // 1. Append (name, value) to headers.
        for (let j = 0; j < cookies.length; ++j) {
          headers.push([name, cookies[j]])
        }
      } else {
        // 2. Otherwise:

        // 1. Let value be the result of getting name from list.

        // 2. Assert: value is non-null.
        // Note: This operation was done by `HeadersList#toSortedArray`.

        // 3. Append (name, value) to headers.
        headers.push([name, value])
      }
    }

    // 4. Return headers.
    return (this.#headersList[kHeadersSortedMap] = headers)
  }

  [util.inspect.custom] (depth, options) {
    options.depth ??= depth

    return `Headers ${util.formatWithOptions(options, this.#headersList.entries)}`
  }

  static getHeadersGuard (o) {
    return o.#guard
  }

  static setHeadersGuard (o, guard) {
    o.#guard = guard
  }

  static getHeadersList (o) {
    return o.#headersList
  }

  static setHeadersList (o, list) {
    o.#headersList = list
  }
}

const { getHeadersGuard, setHeadersGuard, getHeadersList, setHeadersList } = Headers
Reflect.deleteProperty(Headers, 'getHeadersGuard')
Reflect.deleteProperty(Headers, 'setHeadersGuard')
Reflect.deleteProperty(Headers, 'getHeadersList')
Reflect.deleteProperty(Headers, 'setHeadersList')

iteratorMixin('Headers', Headers, kHeadersSortedMap, 0, 1)

Object.defineProperties(Headers.prototype, {
  append: kEnumerableProperty,
  delete: kEnumerableProperty,
  get: kEnumerableProperty,
  has: kEnumerableProperty,
  set: kEnumerableProperty,
  getSetCookie: kEnumerableProperty,
  [Symbol.toStringTag]: {
    value: 'Headers',
    configurable: true
  },
  [util.inspect.custom]: {
    enumerable: false
  }
})

webidl.converters.HeadersInit = function (V, prefix, argument) {
  if (webidl.util.Type(V) === 'Object') {
    const iterator = Reflect.get(V, Symbol.iterator)

    // A work-around to ensure we send the properly-cased Headers when V is a Headers object.
    // Read https://github.com/nodejs/undici/pull/3159#issuecomment-2075537226 before touching, please.
    if (!util.types.isProxy(V) && iterator === Headers.prototype.entries) { // Headers object
      try {
        return getHeadersList(V).entriesList
      } catch {
        // fall-through
      }
    }

    if (typeof iterator === 'function') {
      return webidl.converters['sequence<sequence<ByteString>>'](V, prefix, argument, iterator.bind(V))
    }

    return webidl.converters['record<ByteString, ByteString>'](V, prefix, argument)
  }

  throw webidl.errors.conversionFailed({
    prefix: 'Headers constructor',
    argument: 'Argument 1',
    types: ['sequence<sequence<ByteString>>', 'record<ByteString, ByteString>']
  })
}

module.exports = {
  fill,
  // for test.
  compareHeaderName,
  Headers,
  HeadersList,
  getHeadersGuard,
  setHeadersGuard,
  setHeadersList,
  getHeadersList
}


/***/ }),

/***/ 4398:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {

// https://github.com/Ethan-Arrowood/undici-fetch



const {
  makeNetworkError,
  makeAppropriateNetworkError,
  filterResponse,
  makeResponse,
  fromInnerResponse
} = __nccwpck_require__(9051)
const { HeadersList } = __nccwpck_require__(660)
const { Request, cloneRequest } = __nccwpck_require__(9967)
const zlib = __nccwpck_require__(8522)
const {
  bytesMatch,
  makePolicyContainer,
  clonePolicyContainer,
  requestBadPort,
  TAOCheck,
  appendRequestOriginHeader,
  responseLocationURL,
  requestCurrentURL,
  setRequestReferrerPolicyOnRedirect,
  tryUpgradeRequestToAPotentiallyTrustworthyURL,
  createOpaqueTimingInfo,
  appendFetchMetadata,
  corsCheck,
  crossOriginResourcePolicyCheck,
  determineRequestsReferrer,
  coarsenedSharedCurrentTime,
  createDeferredPromise,
  isBlobLike,
  sameOrigin,
  isCancelled,
  isAborted,
  isErrorLike,
  fullyReadBody,
  readableStreamClose,
  isomorphicEncode,
  urlIsLocal,
  urlIsHttpHttpsScheme,
  urlHasHttpsScheme,
  clampAndCoarsenConnectionTimingInfo,
  simpleRangeHeaderValue,
  buildContentRange,
  createInflate,
  extractMimeType
} = __nccwpck_require__(3168)
const { kState, kDispatcher } = __nccwpck_require__(3627)
const assert = __nccwpck_require__(4589)
const { safelyExtractBody, extractBody } = __nccwpck_require__(4492)
const {
  redirectStatusSet,
  nullBodyStatus,
  safeMethodsSet,
  requestBodyHeader,
  subresourceSet
} = __nccwpck_require__(4495)
const EE = __nccwpck_require__(8474)
const { Readable, pipeline, finished } = __nccwpck_require__(7075)
const { addAbortListener, isErrored, isReadable, bufferToLowerCasedHeaderName } = __nccwpck_require__(3440)
const { dataURLProcessor, serializeAMimeType, minimizeSupportedMimeType } = __nccwpck_require__(1900)
const { getGlobalDispatcher } = __nccwpck_require__(2581)
const { webidl } = __nccwpck_require__(5893)
const { STATUS_CODES } = __nccwpck_require__(7067)
const GET_OR_HEAD = ['GET', 'HEAD']

const defaultUserAgent = typeof __UNDICI_IS_NODE__ !== 'undefined' || typeof esbuildDetection !== 'undefined'
  ? 'node'
  : 'undici'

/** @type {import('buffer').resolveObjectURL} */
let resolveObjectURL

class Fetch extends EE {
  constructor (dispatcher) {
    super()

    this.dispatcher = dispatcher
    this.connection = null
    this.dump = false
    this.state = 'ongoing'
  }

  terminate (reason) {
    if (this.state !== 'ongoing') {
      return
    }

    this.state = 'terminated'
    this.connection?.destroy(reason)
    this.emit('terminated', reason)
  }

  // https://fetch.spec.whatwg.org/#fetch-controller-abort
  abort (error) {
    if (this.state !== 'ongoing') {
      return
    }

    // 1. Set controller’s state to "aborted".
    this.state = 'aborted'

    // 2. Let fallbackError be an "AbortError" DOMException.
    // 3. Set error to fallbackError if it is not given.
    if (!error) {
      error = new DOMException('The operation was aborted.', 'AbortError')
    }

    // 4. Let serializedError be StructuredSerialize(error).
    //    If that threw an exception, catch it, and let
    //    serializedError be StructuredSerialize(fallbackError).

    // 5. Set controller’s serialized abort reason to serializedError.
    this.serializedAbortReason = error

    this.connection?.destroy(error)
    this.emit('terminated', error)
  }
}

function handleFetchDone (response) {
  finalizeAndReportTiming(response, 'fetch')
}

// https://fetch.spec.whatwg.org/#fetch-method
function fetch (input, init = undefined) {
  webidl.argumentLengthCheck(arguments, 1, 'globalThis.fetch')

  // 1. Let p be a new promise.
  let p = createDeferredPromise()

  // 2. Let requestObject be the result of invoking the initial value of
  // Request as constructor with input and init as arguments. If this throws
  // an exception, reject p with it and return p.
  let requestObject

  try {
    requestObject = new Request(input, init)
  } catch (e) {
    p.reject(e)
    return p.promise
  }

  // 3. Let request be requestObject’s request.
  const request = requestObject[kState]

  // 4. If requestObject’s signal’s aborted flag is set, then:
  if (requestObject.signal.aborted) {
    // 1. Abort the fetch() call with p, request, null, and
    //    requestObject’s signal’s abort reason.
    abortFetch(p, request, null, requestObject.signal.reason)

    // 2. Return p.
    return p.promise
  }

  // 5. Let globalObject be request’s client’s global object.
  const globalObject = request.client.globalObject

  // 6. If globalObject is a ServiceWorkerGlobalScope object, then set
  // request’s service-workers mode to "none".
  if (globalObject?.constructor?.name === 'ServiceWorkerGlobalScope') {
    request.serviceWorkers = 'none'
  }

  // 7. Let responseObject be null.
  let responseObject = null

  // 8. Let relevantRealm be this’s relevant Realm.

  // 9. Let locallyAborted be false.
  let locallyAborted = false

  // 10. Let controller be null.
  let controller = null

  // 11. Add the following abort steps to requestObject’s signal:
  addAbortListener(
    requestObject.signal,
    () => {
      // 1. Set locallyAborted to true.
      locallyAborted = true

      // 2. Assert: controller is non-null.
      assert(controller != null)

      // 3. Abort controller with requestObject’s signal’s abort reason.
      controller.abort(requestObject.signal.reason)

      const realResponse = responseObject?.deref()

      // 4. Abort the fetch() call with p, request, responseObject,
      //    and requestObject’s signal’s abort reason.
      abortFetch(p, request, realResponse, requestObject.signal.reason)
    }
  )

  // 12. Let handleFetchDone given response response be to finalize and
  // report timing with response, globalObject, and "fetch".
  // see function handleFetchDone

  // 13. Set controller to the result of calling fetch given request,
  // with processResponseEndOfBody set to handleFetchDone, and processResponse
  // given response being these substeps:

  const processResponse = (response) => {
    // 1. If locallyAborted is true, terminate these substeps.
    if (locallyAborted) {
      return
    }

    // 2. If response’s aborted flag is set, then:
    if (response.aborted) {
      // 1. Let deserializedError be the result of deserialize a serialized
      //    abort reason given controller’s serialized abort reason and
      //    relevantRealm.

      // 2. Abort the fetch() call with p, request, responseObject, and
      //    deserializedError.

      abortFetch(p, request, responseObject, controller.serializedAbortReason)
      return
    }

    // 3. If response is a network error, then reject p with a TypeError
    // and terminate these substeps.
    if (response.type === 'error') {
      p.reject(new TypeError('fetch failed', { cause: response.error }))
      return
    }

    // 4. Set responseObject to the result of creating a Response object,
    // given response, "immutable", and relevantRealm.
    responseObject = new WeakRef(fromInnerResponse(response, 'immutable'))

    // 5. Resolve p with responseObject.
    p.resolve(responseObject.deref())
    p = null
  }

  controller = fetching({
    request,
    processResponseEndOfBody: handleFetchDone,
    processResponse,
    dispatcher: requestObject[kDispatcher] // undici
  })

  // 14. Return p.
  return p.promise
}

// https://fetch.spec.whatwg.org/#finalize-and-report-timing
function finalizeAndReportTiming (response, initiatorType = 'other') {
  // 1. If response is an aborted network error, then return.
  if (response.type === 'error' && response.aborted) {
    return
  }

  // 2. If response’s URL list is null or empty, then return.
  if (!response.urlList?.length) {
    return
  }

  // 3. Let originalURL be response’s URL list[0].
  const originalURL = response.urlList[0]

  // 4. Let timingInfo be response’s timing info.
  let timingInfo = response.timingInfo

  // 5. Let cacheState be response’s cache state.
  let cacheState = response.cacheState

  // 6. If originalURL’s scheme is not an HTTP(S) scheme, then return.
  if (!urlIsHttpHttpsScheme(originalURL)) {
    return
  }

  // 7. If timingInfo is null, then return.
  if (timingInfo === null) {
    return
  }

  // 8. If response’s timing allow passed flag is not set, then:
  if (!response.timingAllowPassed) {
    //  1. Set timingInfo to a the result of creating an opaque timing info for timingInfo.
    timingInfo = createOpaqueTimingInfo({
      startTime: timingInfo.startTime
    })

    //  2. Set cacheState to the empty string.
    cacheState = ''
  }

  // 9. Set timingInfo’s end time to the coarsened shared current time
  // given global’s relevant settings object’s cross-origin isolated
  // capability.
  // TODO: given global’s relevant settings object’s cross-origin isolated
  // capability?
  timingInfo.endTime = coarsenedSharedCurrentTime()

  // 10. Set response’s timing info to timingInfo.
  response.timingInfo = timingInfo

  // 11. Mark resource timing for timingInfo, originalURL, initiatorType,
  // global, and cacheState.
  markResourceTiming(
    timingInfo,
    originalURL.href,
    initiatorType,
    globalThis,
    cacheState
  )
}

// https://w3c.github.io/resource-timing/#dfn-mark-resource-timing
const markResourceTiming = performance.markResourceTiming

// https://fetch.spec.whatwg.org/#abort-fetch
function abortFetch (p, request, responseObject, error) {
  // 1. Reject promise with error.
  if (p) {
    // We might have already resolved the promise at this stage
    p.reject(error)
  }

  // 2. If request’s body is not null and is readable, then cancel request’s
  // body with error.
  if (request.body != null && isReadable(request.body?.stream)) {
    request.body.stream.cancel(error).catch((err) => {
      if (err.code === 'ERR_INVALID_STATE') {
        // Node bug?
        return
      }
      throw err
    })
  }

  // 3. If responseObject is null, then return.
  if (responseObject == null) {
    return
  }

  // 4. Let response be responseObject’s response.
  const response = responseObject[kState]

  // 5. If response’s body is not null and is readable, then error response’s
  // body with error.
  if (response.body != null && isReadable(response.body?.stream)) {
    response.body.stream.cancel(error).catch((err) => {
      if (err.code === 'ERR_INVALID_STATE') {
        // Node bug?
        return
      }
      throw err
    })
  }
}

// https://fetch.spec.whatwg.org/#fetching
function fetching ({
  request,
  processRequestBodyChunkLength,
  processRequestEndOfBody,
  processResponse,
  processResponseEndOfBody,
  processResponseConsumeBody,
  useParallelQueue = false,
  dispatcher = getGlobalDispatcher() // undici
}) {
  // Ensure that the dispatcher is set accordingly
  assert(dispatcher)

  // 1. Let taskDestination be null.
  let taskDestination = null

  // 2. Let crossOriginIsolatedCapability be false.
  let crossOriginIsolatedCapability = false

  // 3. If request’s client is non-null, then:
  if (request.client != null) {
    // 1. Set taskDestination to request’s client’s global object.
    taskDestination = request.client.globalObject

    // 2. Set crossOriginIsolatedCapability to request’s client’s cross-origin
    // isolated capability.
    crossOriginIsolatedCapability =
      request.client.crossOriginIsolatedCapability
  }

  // 4. If useParallelQueue is true, then set taskDestination to the result of
  // starting a new parallel queue.
  // TODO

  // 5. Let timingInfo be a new fetch timing info whose start time and
  // post-redirect start time are the coarsened shared current time given
  // crossOriginIsolatedCapability.
  const currentTime = coarsenedSharedCurrentTime(crossOriginIsolatedCapability)
  const timingInfo = createOpaqueTimingInfo({
    startTime: currentTime
  })

  // 6. Let fetchParams be a new fetch params whose
  // request is request,
  // timing info is timingInfo,
  // process request body chunk length is processRequestBodyChunkLength,
  // process request end-of-body is processRequestEndOfBody,
  // process response is processResponse,
  // process response consume body is processResponseConsumeBody,
  // process response end-of-body is processResponseEndOfBody,
  // task destination is taskDestination,
  // and cross-origin isolated capability is crossOriginIsolatedCapability.
  const fetchParams = {
    controller: new Fetch(dispatcher),
    request,
    timingInfo,
    processRequestBodyChunkLength,
    processRequestEndOfBody,
    processResponse,
    processResponseConsumeBody,
    processResponseEndOfBody,
    taskDestination,
    crossOriginIsolatedCapability
  }

  // 7. If request’s body is a byte sequence, then set request’s body to
  //    request’s body as a body.
  // NOTE: Since fetching is only called from fetch, body should already be
  // extracted.
  assert(!request.body || request.body.stream)

  // 8. If request’s window is "client", then set request’s window to request’s
  // client, if request’s client’s global object is a Window object; otherwise
  // "no-window".
  if (request.window === 'client') {
    // TODO: What if request.client is null?
    request.window =
      request.client?.globalObject?.constructor?.name === 'Window'
        ? request.client
        : 'no-window'
  }

  // 9. If request’s origin is "client", then set request’s origin to request’s
  // client’s origin.
  if (request.origin === 'client') {
    request.origin = request.client.origin
  }

  // 10. If all of the following conditions are true:
  // TODO

  // 11. If request’s policy container is "client", then:
  if (request.policyContainer === 'client') {
    // 1. If request’s client is non-null, then set request’s policy
    // container to a clone of request’s client’s policy container. [HTML]
    if (request.client != null) {
      request.policyContainer = clonePolicyContainer(
        request.client.policyContainer
      )
    } else {
      // 2. Otherwise, set request’s policy container to a new policy
      // container.
      request.policyContainer = makePolicyContainer()
    }
  }

  // 12. If request’s header list does not contain `Accept`, then:
  if (!request.headersList.contains('accept', true)) {
    // 1. Let value be `*/*`.
    const value = '*/*'

    // 2. A user agent should set value to the first matching statement, if
    // any, switching on request’s destination:
    // "document"
    // "frame"
    // "iframe"
    // `text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8`
    // "image"
    // `image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5`
    // "style"
    // `text/css,*/*;q=0.1`
    // TODO

    // 3. Append `Accept`/value to request’s header list.
    request.headersList.append('accept', value, true)
  }

  // 13. If request’s header list does not contain `Accept-Language`, then
  // user agents should append `Accept-Language`/an appropriate value to
  // request’s header list.
  if (!request.headersList.contains('accept-language', true)) {
    request.headersList.append('accept-language', '*', true)
  }

  // 14. If request’s priority is null, then use request’s initiator and
  // destination appropriately in setting request’s priority to a
  // user-agent-defined object.
  if (request.priority === null) {
    // TODO
  }

  // 15. If request is a subresource request, then:
  if (subresourceSet.has(request.destination)) {
    // TODO
  }

  // 16. Run main fetch given fetchParams.
  mainFetch(fetchParams)
    .catch(err => {
      fetchParams.controller.terminate(err)
    })

  // 17. Return fetchParam's controller
  return fetchParams.controller
}

// https://fetch.spec.whatwg.org/#concept-main-fetch
async function mainFetch (fetchParams, recursive = false) {
  // 1. Let request be fetchParams’s request.
  const request = fetchParams.request

  // 2. Let response be null.
  let response = null

  // 3. If request’s local-URLs-only flag is set and request’s current URL is
  // not local, then set response to a network error.
  if (request.localURLsOnly && !urlIsLocal(requestCurrentURL(request))) {
    response = makeNetworkError('local URLs only')
  }

  // 4. Run report Content Security Policy violations for request.
  // TODO

  // 5. Upgrade request to a potentially trustworthy URL, if appropriate.
  tryUpgradeRequestToAPotentiallyTrustworthyURL(request)

  // 6. If should request be blocked due to a bad port, should fetching request
  // be blocked as mixed content, or should request be blocked by Content
  // Security Policy returns blocked, then set response to a network error.
  if (requestBadPort(request) === 'blocked') {
    response = makeNetworkError('bad port')
  }
  // TODO: should fetching request be blocked as mixed content?
  // TODO: should request be blocked by Content Security Policy?

  // 7. If request’s referrer policy is the empty string, then set request’s
  // referrer policy to request’s policy container’s referrer policy.
  if (request.referrerPolicy === '') {
    request.referrerPolicy = request.policyContainer.referrerPolicy
  }

  // 8. If request’s referrer is not "no-referrer", then set request’s
  // referrer to the result of invoking determine request’s referrer.
  if (request.referrer !== 'no-referrer') {
    request.referrer = determineRequestsReferrer(request)
  }

  // 9. Set request’s current URL’s scheme to "https" if all of the following
  // conditions are true:
  // - request’s current URL’s scheme is "http"
  // - request’s current URL’s host is a domain
  // - Matching request’s current URL’s host per Known HSTS Host Domain Name
  //   Matching results in either a superdomain match with an asserted
  //   includeSubDomains directive or a congruent match (with or without an
  //   asserted includeSubDomains directive). [HSTS]
  // TODO

  // 10. If recursive is false, then run the remaining steps in parallel.
  // TODO

  // 11. If response is null, then set response to the result of running
  // the steps corresponding to the first matching statement:
  if (response === null) {
    response = await (async () => {
      const currentURL = requestCurrentURL(request)

      if (
        // - request’s current URL’s origin is same origin with request’s origin,
        //   and request’s response tainting is "basic"
        (sameOrigin(currentURL, request.url) && request.responseTainting === 'basic') ||
        // request’s current URL’s scheme is "data"
        (currentURL.protocol === 'data:') ||
        // - request’s mode is "navigate" or "websocket"
        (request.mode === 'navigate' || request.mode === 'websocket')
      ) {
        // 1. Set request’s response tainting to "basic".
        request.responseTainting = 'basic'

        // 2. Return the result of running scheme fetch given fetchParams.
        return await schemeFetch(fetchParams)
      }

      // request’s mode is "same-origin"
      if (request.mode === 'same-origin') {
        // 1. Return a network error.
        return makeNetworkError('request mode cannot be "same-origin"')
      }

      // request’s mode is "no-cors"
      if (request.mode === 'no-cors') {
        // 1. If request’s redirect mode is not "follow", then return a network
        // error.
        if (request.redirect !== 'follow') {
          return makeNetworkError(
            'redirect mode cannot be "follow" for "no-cors" request'
          )
        }

        // 2. Set request’s response tainting to "opaque".
        request.responseTainting = 'opaque'

        // 3. Return the result of running scheme fetch given fetchParams.
        return await schemeFetch(fetchParams)
      }

      // request’s current URL’s scheme is not an HTTP(S) scheme
      if (!urlIsHttpHttpsScheme(requestCurrentURL(request))) {
        // Return a network error.
        return makeNetworkError('URL scheme must be a HTTP(S) scheme')
      }

      // - request’s use-CORS-preflight flag is set
      // - request’s unsafe-request flag is set and either request’s method is
      //   not a CORS-safelisted method or CORS-unsafe request-header names with
      //   request’s header list is not empty
      //    1. Set request’s response tainting to "cors".
      //    2. Let corsWithPreflightResponse be the result of running HTTP fetch
      //    given fetchParams and true.
      //    3. If corsWithPreflightResponse is a network error, then clear cache
      //    entries using request.
      //    4. Return corsWithPreflightResponse.
      // TODO

      // Otherwise
      //    1. Set request’s response tainting to "cors".
      request.responseTainting = 'cors'

      //    2. Return the result of running HTTP fetch given fetchParams.
      return await httpFetch(fetchParams)
    })()
  }

  // 12. If recursive is true, then return response.
  if (recursive) {
    return response
  }

  // 13. If response is not a network error and response is not a filtered
  // response, then:
  if (response.status !== 0 && !response.internalResponse) {
    // If request’s response tainting is "cors", then:
    if (request.responseTainting === 'cors') {
      // 1. Let headerNames be the result of extracting header list values
      // given `Access-Control-Expose-Headers` and response’s header list.
      // TODO
      // 2. If request’s credentials mode is not "include" and headerNames
      // contains `*`, then set response’s CORS-exposed header-name list to
      // all unique header names in response’s header list.
      // TODO
      // 3. Otherwise, if headerNames is not null or failure, then set
      // response’s CORS-exposed header-name list to headerNames.
      // TODO
    }

    // Set response to the following filtered response with response as its
    // internal response, depending on request’s response tainting:
    if (request.responseTainting === 'basic') {
      response = filterResponse(response, 'basic')
    } else if (request.responseTainting === 'cors') {
      response = filterResponse(response, 'cors')
    } else if (request.responseTainting === 'opaque') {
      response = filterResponse(response, 'opaque')
    } else {
      assert(false)
    }
  }

  // 14. Let internalResponse be response, if response is a network error,
  // and response’s internal response otherwise.
  let internalResponse =
    response.status === 0 ? response : response.internalResponse

  // 15. If internalResponse’s URL list is empty, then set it to a clone of
  // request’s URL list.
  if (internalResponse.urlList.length === 0) {
    internalResponse.urlList.push(...request.urlList)
  }

  // 16. If request’s timing allow failed flag is unset, then set
  // internalResponse’s timing allow passed flag.
  if (!request.timingAllowFailed) {
    response.timingAllowPassed = true
  }

  // 17. If response is not a network error and any of the following returns
  // blocked
  // - should internalResponse to request be blocked as mixed content
  // - should internalResponse to request be blocked by Content Security Policy
  // - should internalResponse to request be blocked due to its MIME type
  // - should internalResponse to request be blocked due to nosniff
  // TODO

  // 18. If response’s type is "opaque", internalResponse’s status is 206,
  // internalResponse’s range-requested flag is set, and request’s header
  // list does not contain `Range`, then set response and internalResponse
  // to a network error.
  if (
    response.type === 'opaque' &&
    internalResponse.status === 206 &&
    internalResponse.rangeRequested &&
    !request.headers.contains('range', true)
  ) {
    response = internalResponse = makeNetworkError()
  }

  // 19. If response is not a network error and either request’s method is
  // `HEAD` or `CONNECT`, or internalResponse’s status is a null body status,
  // set internalResponse’s body to null and disregard any enqueuing toward
  // it (if any).
  if (
    response.status !== 0 &&
    (request.method === 'HEAD' ||
      request.method === 'CONNECT' ||
      nullBodyStatus.includes(internalResponse.status))
  ) {
    internalResponse.body = null
    fetchParams.controller.dump = true
  }

  // 20. If request’s integrity metadata is not the empty string, then:
  if (request.integrity) {
    // 1. Let processBodyError be this step: run fetch finale given fetchParams
    // and a network error.
    const processBodyError = (reason) =>
      fetchFinale(fetchParams, makeNetworkError(reason))

    // 2. If request’s response tainting is "opaque", or response’s body is null,
    // then run processBodyError and abort these steps.
    if (request.responseTainting === 'opaque' || response.body == null) {
      processBodyError(response.error)
      return
    }

    // 3. Let processBody given bytes be these steps:
    const processBody = (bytes) => {
      // 1. If bytes do not match request’s integrity metadata,
      // then run processBodyError and abort these steps. [SRI]
      if (!bytesMatch(bytes, request.integrity)) {
        processBodyError('integrity mismatch')
        return
      }

      // 2. Set response’s body to bytes as a body.
      response.body = safelyExtractBody(bytes)[0]

      // 3. Run fetch finale given fetchParams and response.
      fetchFinale(fetchParams, response)
    }

    // 4. Fully read response’s body given processBody and processBodyError.
    await fullyReadBody(response.body, processBody, processBodyError)
  } else {
    // 21. Otherwise, run fetch finale given fetchParams and response.
    fetchFinale(fetchParams, response)
  }
}

// https://fetch.spec.whatwg.org/#concept-scheme-fetch
// given a fetch params fetchParams
function schemeFetch (fetchParams) {
  // Note: since the connection is destroyed on redirect, which sets fetchParams to a
  // cancelled state, we do not want this condition to trigger *unless* there have been
  // no redirects. See https://github.com/nodejs/undici/issues/1776
  // 1. If fetchParams is canceled, then return the appropriate network error for fetchParams.
  if (isCancelled(fetchParams) && fetchParams.request.redirectCount === 0) {
    return Promise.resolve(makeAppropriateNetworkError(fetchParams))
  }

  // 2. Let request be fetchParams’s request.
  const { request } = fetchParams

  const { protocol: scheme } = requestCurrentURL(request)

  // 3. Switch on request’s current URL’s scheme and run the associated steps:
  switch (scheme) {
    case 'about:': {
      // If request’s current URL’s path is the string "blank", then return a new response
      // whose status message is `OK`, header list is « (`Content-Type`, `text/html;charset=utf-8`) »,
      // and body is the empty byte sequence as a body.

      // Otherwise, return a network error.
      return Promise.resolve(makeNetworkError('about scheme is not supported'))
    }
    case 'blob:': {
      if (!resolveObjectURL) {
        resolveObjectURL = (__nccwpck_require__(4573).resolveObjectURL)
      }

      // 1. Let blobURLEntry be request’s current URL’s blob URL entry.
      const blobURLEntry = requestCurrentURL(request)

      // https://github.com/web-platform-tests/wpt/blob/7b0ebaccc62b566a1965396e5be7bb2bc06f841f/FileAPI/url/resources/fetch-tests.js#L52-L56
      // Buffer.resolveObjectURL does not ignore URL queries.
      if (blobURLEntry.search.length !== 0) {
        return Promise.resolve(makeNetworkError('NetworkError when attempting to fetch resource.'))
      }

      const blob = resolveObjectURL(blobURLEntry.toString())

      // 2. If request’s method is not `GET`, blobURLEntry is null, or blobURLEntry’s
      //    object is not a Blob object, then return a network error.
      if (request.method !== 'GET' || !isBlobLike(blob)) {
        return Promise.resolve(makeNetworkError('invalid method'))
      }

      // 3. Let blob be blobURLEntry’s object.
      // Note: done above

      // 4. Let response be a new response.
      const response = makeResponse()

      // 5. Let fullLength be blob’s size.
      const fullLength = blob.size

      // 6. Let serializedFullLength be fullLength, serialized and isomorphic encoded.
      const serializedFullLength = isomorphicEncode(`${fullLength}`)

      // 7. Let type be blob’s type.
      const type = blob.type

      // 8. If request’s header list does not contain `Range`:
      // 9. Otherwise:
      if (!request.headersList.contains('range', true)) {
        // 1. Let bodyWithType be the result of safely extracting blob.
        // Note: in the FileAPI a blob "object" is a Blob *or* a MediaSource.
        // In node, this can only ever be a Blob. Therefore we can safely
        // use extractBody directly.
        const bodyWithType = extractBody(blob)

        // 2. Set response’s status message to `OK`.
        response.statusText = 'OK'

        // 3. Set response’s body to bodyWithType’s body.
        response.body = bodyWithType[0]

        // 4. Set response’s header list to « (`Content-Length`, serializedFullLength), (`Content-Type`, type) ».
        response.headersList.set('content-length', serializedFullLength, true)
        response.headersList.set('content-type', type, true)
      } else {
        // 1. Set response’s range-requested flag.
        response.rangeRequested = true

        // 2. Let rangeHeader be the result of getting `Range` from request’s header list.
        const rangeHeader = request.headersList.get('range', true)

        // 3. Let rangeValue be the result of parsing a single range header value given rangeHeader and true.
        const rangeValue = simpleRangeHeaderValue(rangeHeader, true)

        // 4. If rangeValue is failure, then return a network error.
        if (rangeValue === 'failure') {
          return Promise.resolve(makeNetworkError('failed to fetch the data URL'))
        }

        // 5. Let (rangeStart, rangeEnd) be rangeValue.
        let { rangeStartValue: rangeStart, rangeEndValue: rangeEnd } = rangeValue

        // 6. If rangeStart is null:
        // 7. Otherwise:
        if (rangeStart === null) {
          // 1. Set rangeStart to fullLength − rangeEnd.
          rangeStart = fullLength - rangeEnd

          // 2. Set rangeEnd to rangeStart + rangeEnd − 1.
          rangeEnd = rangeStart + rangeEnd - 1
        } else {
          // 1. If rangeStart is greater than or equal to fullLength, then return a network error.
          if (rangeStart >= fullLength) {
            return Promise.resolve(makeNetworkError('Range start is greater than the blob\'s size.'))
          }

          // 2. If rangeEnd is null or rangeEnd is greater than or equal to fullLength, then set
          //    rangeEnd to fullLength − 1.
          if (rangeEnd === null || rangeEnd >= fullLength) {
            rangeEnd = fullLength - 1
          }
        }

        // 8. Let slicedBlob be the result of invoking slice blob given blob, rangeStart,
        //    rangeEnd + 1, and type.
        const slicedBlob = blob.slice(rangeStart, rangeEnd, type)

        // 9. Let slicedBodyWithType be the result of safely extracting slicedBlob.
        // Note: same reason as mentioned above as to why we use extractBody
        const slicedBodyWithType = extractBody(slicedBlob)

        // 10. Set response’s body to slicedBodyWithType’s body.
        response.body = slicedBodyWithType[0]

        // 11. Let serializedSlicedLength be slicedBlob’s size, serialized and isomorphic encoded.
        const serializedSlicedLength = isomorphicEncode(`${slicedBlob.size}`)

        // 12. Let contentRange be the result of invoking build a content range given rangeStart,
        //     rangeEnd, and fullLength.
        const contentRange = buildContentRange(rangeStart, rangeEnd, fullLength)

        // 13. Set response’s status to 206.
        response.status = 206

        // 14. Set response’s status message to `Partial Content`.
        response.statusText = 'Partial Content'

        // 15. Set response’s header list to « (`Content-Length`, serializedSlicedLength),
        //     (`Content-Type`, type), (`Content-Range`, contentRange) ».
        response.headersList.set('content-length', serializedSlicedLength, true)
        response.headersList.set('content-type', type, true)
        response.headersList.set('content-range', contentRange, true)
      }

      // 10. Return response.
      return Promise.resolve(response)
    }
    case 'data:': {
      // 1. Let dataURLStruct be the result of running the
      //    data: URL processor on request’s current URL.
      const currentURL = requestCurrentURL(request)
      const dataURLStruct = dataURLProcessor(currentURL)

      // 2. If dataURLStruct is failure, then return a
      //    network error.
      if (dataURLStruct === 'failure') {
        return Promise.resolve(makeNetworkError('failed to fetch the data URL'))
      }

      // 3. Let mimeType be dataURLStruct’s MIME type, serialized.
      const mimeType = serializeAMimeType(dataURLStruct.mimeType)

      // 4. Return a response whose status message is `OK`,
      //    header list is « (`Content-Type`, mimeType) »,
      //    and body is dataURLStruct’s body as a body.
      return Promise.resolve(makeResponse({
        statusText: 'OK',
        headersList: [
          ['content-type', { name: 'Content-Type', value: mimeType }]
        ],
        body: safelyExtractBody(dataURLStruct.body)[0]
      }))
    }
    case 'file:': {
      // For now, unfortunate as it is, file URLs are left as an exercise for the reader.
      // When in doubt, return a network error.
      return Promise.resolve(makeNetworkError('not implemented... yet...'))
    }
    case 'http:':
    case 'https:': {
      // Return the result of running HTTP fetch given fetchParams.

      return httpFetch(fetchParams)
        .catch((err) => makeNetworkError(err))
    }
    default: {
      return Promise.resolve(makeNetworkError('unknown scheme'))
    }
  }
}

// https://fetch.spec.whatwg.org/#finalize-response
function finalizeResponse (fetchParams, response) {
  // 1. Set fetchParams’s request’s done flag.
  fetchParams.request.done = true

  // 2, If fetchParams’s process response done is not null, then queue a fetch
  // task to run fetchParams’s process response done given response, with
  // fetchParams’s task destination.
  if (fetchParams.processResponseDone != null) {
    queueMicrotask(() => fetchParams.processResponseDone(response))
  }
}

// https://fetch.spec.whatwg.org/#fetch-finale
function fetchFinale (fetchParams, response) {
  // 1. Let timingInfo be fetchParams’s timing info.
  let timingInfo = fetchParams.timingInfo

  // 2. If response is not a network error and fetchParams’s request’s client is a secure context,
  //    then set timingInfo’s server-timing headers to the result of getting, decoding, and splitting
  //    `Server-Timing` from response’s internal response’s header list.
  // TODO

  // 3. Let processResponseEndOfBody be the following steps:
  const processResponseEndOfBody = () => {
    // 1. Let unsafeEndTime be the unsafe shared current time.
    const unsafeEndTime = Date.now() // ?

    // 2. If fetchParams’s request’s destination is "document", then set fetchParams’s controller’s
    //    full timing info to fetchParams’s timing info.
    if (fetchParams.request.destination === 'document') {
      fetchParams.controller.fullTimingInfo = timingInfo
    }

    // 3. Set fetchParams’s controller’s report timing steps to the following steps given a global object global:
    fetchParams.controller.reportTimingSteps = () => {
      // 1. If fetchParams’s request’s URL’s scheme is not an HTTP(S) scheme, then return.
      if (fetchParams.request.url.protocol !== 'https:') {
        return
      }

      // 2. Set timingInfo’s end time to the relative high resolution time given unsafeEndTime and global.
      timingInfo.endTime = unsafeEndTime

      // 3. Let cacheState be response’s cache state.
      let cacheState = response.cacheState

      // 4. Let bodyInfo be response’s body info.
      const bodyInfo = response.bodyInfo

      // 5. If response’s timing allow passed flag is not set, then set timingInfo to the result of creating an
      //    opaque timing info for timingInfo and set cacheState to the empty string.
      if (!response.timingAllowPassed) {
        timingInfo = createOpaqueTimingInfo(timingInfo)

        cacheState = ''
      }

      // 6. Let responseStatus be 0.
      let responseStatus = 0

      // 7. If fetchParams’s request’s mode is not "navigate" or response’s has-cross-origin-redirects is false:
      if (fetchParams.request.mode !== 'navigator' || !response.hasCrossOriginRedirects) {
        // 1. Set responseStatus to response’s status.
        responseStatus = response.status

        // 2. Let mimeType be the result of extracting a MIME type from response’s header list.
        const mimeType = extractMimeType(response.headersList)

        // 3. If mimeType is not failure, then set bodyInfo’s content type to the result of minimizing a supported MIME type given mimeType.
        if (mimeType !== 'failure') {
          bodyInfo.contentType = minimizeSupportedMimeType(mimeType)
        }
      }

      // 8. If fetchParams’s request’s initiator type is non-null, then mark resource timing given timingInfo,
      //    fetchParams’s request’s URL, fetchParams’s request’s initiator type, global, cacheState, bodyInfo,
      //    and responseStatus.
      if (fetchParams.request.initiatorType != null) {
        // TODO: update markresourcetiming
        markResourceTiming(timingInfo, fetchParams.request.url.href, fetchParams.request.initiatorType, globalThis, cacheState, bodyInfo, responseStatus)
      }
    }

    // 4. Let processResponseEndOfBodyTask be the following steps:
    const processResponseEndOfBodyTask = () => {
      // 1. Set fetchParams’s request’s done flag.
      fetchParams.request.done = true

      // 2. If fetchParams’s process response end-of-body is non-null, then run fetchParams’s process
      //    response end-of-body given response.
      if (fetchParams.processResponseEndOfBody != null) {
        queueMicrotask(() => fetchParams.processResponseEndOfBody(response))
      }

      // 3. If fetchParams’s request’s initiator type is non-null and fetchParams’s request’s client’s
      //    global object is fetchParams’s task destination, then run fetchParams’s controller’s report
      //    timing steps given fetchParams’s request’s client’s global object.
      if (fetchParams.request.initiatorType != null) {
        fetchParams.controller.reportTimingSteps()
      }
    }

    // 5. Queue a fetch task to run processResponseEndOfBodyTask with fetchParams’s task destination
    queueMicrotask(() => processResponseEndOfBodyTask())
  }

  // 4. If fetchParams’s process response is non-null, then queue a fetch task to run fetchParams’s
  //    process response given response, with fetchParams’s task destination.
  if (fetchParams.processResponse != null) {
    queueMicrotask(() => {
      fetchParams.processResponse(response)
      fetchParams.processResponse = null
    })
  }

  // 5. Let internalResponse be response, if response is a network error; otherwise response’s internal response.
  const internalResponse = response.type === 'error' ? response : (response.internalResponse ?? response)

  // 6. If internalResponse’s body is null, then run processResponseEndOfBody.
  // 7. Otherwise:
  if (internalResponse.body == null) {
    processResponseEndOfBody()
  } else {
    // mcollina: all the following steps of the specs are skipped.
    // The internal transform stream is not needed.
    // See https://github.com/nodejs/undici/pull/3093#issuecomment-2050198541

    // 1. Let transformStream be a new TransformStream.
    // 2. Let identityTransformAlgorithm be an algorithm which, given chunk, enqueues chunk in transformStream.
    // 3. Set up transformStream with transformAlgorithm set to identityTransformAlgorithm and flushAlgorithm
    //    set to processResponseEndOfBody.
    // 4. Set internalResponse’s body’s stream to the result of internalResponse’s body’s stream piped through transformStream.

    finished(internalResponse.body.stream, () => {
      processResponseEndOfBody()
    })
  }
}

// https://fetch.spec.whatwg.org/#http-fetch
async function httpFetch (fetchParams) {
  // 1. Let request be fetchParams’s request.
  const request = fetchParams.request

  // 2. Let response be null.
  let response = null

  // 3. Let actualResponse be null.
  let actualResponse = null

  // 4. Let timingInfo be fetchParams’s timing info.
  const timingInfo = fetchParams.timingInfo

  // 5. If request’s service-workers mode is "all", then:
  if (request.serviceWorkers === 'all') {
    // TODO
  }

  // 6. If response is null, then:
  if (response === null) {
    // 1. If makeCORSPreflight is true and one of these conditions is true:
    // TODO

    // 2. If request’s redirect mode is "follow", then set request’s
    // service-workers mode to "none".
    if (request.redirect === 'follow') {
      request.serviceWorkers = 'none'
    }

    // 3. Set response and actualResponse to the result of running
    // HTTP-network-or-cache fetch given fetchParams.
    actualResponse = response = await httpNetworkOrCacheFetch(fetchParams)

    // 4. If request’s response tainting is "cors" and a CORS check
    // for request and response returns failure, then return a network error.
    if (
      request.responseTainting === 'cors' &&
      corsCheck(request, response) === 'failure'
    ) {
      return makeNetworkError('cors failure')
    }

    // 5. If the TAO check for request and response returns failure, then set
    // request’s timing allow failed flag.
    if (TAOCheck(request, response) === 'failure') {
      request.timingAllowFailed = true
    }
  }

  // 7. If either request’s response tainting or response’s type
  // is "opaque", and the cross-origin resource policy check with
  // request’s origin, request’s client, request’s destination,
  // and actualResponse returns blocked, then return a network error.
  if (
    (request.responseTainting === 'opaque' || response.type === 'opaque') &&
    crossOriginResourcePolicyCheck(
      request.origin,
      request.client,
      request.destination,
      actualResponse
    ) === 'blocked'
  ) {
    return makeNetworkError('blocked')
  }

  // 8. If actualResponse’s status is a redirect status, then:
  if (redirectStatusSet.has(actualResponse.status)) {
    // 1. If actualResponse’s status is not 303, request’s body is not null,
    // and the connection uses HTTP/2, then user agents may, and are even
    // encouraged to, transmit an RST_STREAM frame.
    // See, https://github.com/whatwg/fetch/issues/1288
    if (request.redirect !== 'manual') {
      fetchParams.controller.connection.destroy(undefined, false)
    }

    // 2. Switch on request’s redirect mode:
    if (request.redirect === 'error') {
      // Set response to a network error.
      response = makeNetworkError('unexpected redirect')
    } else if (request.redirect === 'manual') {
      // Set response to an opaque-redirect filtered response whose internal
      // response is actualResponse.
      // NOTE(spec): On the web this would return an `opaqueredirect` response,
      // but that doesn't make sense server side.
      // See https://github.com/nodejs/undici/issues/1193.
      response = actualResponse
    } else if (request.redirect === 'follow') {
      // Set response to the result of running HTTP-redirect fetch given
      // fetchParams and response.
      response = await httpRedirectFetch(fetchParams, response)
    } else {
      assert(false)
    }
  }

  // 9. Set response’s timing info to timingInfo.
  response.timingInfo = timingInfo

  // 10. Return response.
  return response
}

// https://fetch.spec.whatwg.org/#http-redirect-fetch
function httpRedirectFetch (fetchParams, response) {
  // 1. Let request be fetchParams’s request.
  const request = fetchParams.request

  // 2. Let actualResponse be response, if response is not a filtered response,
  // and response’s internal response otherwise.
  const actualResponse = response.internalResponse
    ? response.internalResponse
    : response

  // 3. Let locationURL be actualResponse’s location URL given request’s current
  // URL’s fragment.
  let locationURL

  try {
    locationURL = responseLocationURL(
      actualResponse,
      requestCurrentURL(request).hash
    )

    // 4. If locationURL is null, then return response.
    if (locationURL == null) {
      return response
    }
  } catch (err) {
    // 5. If locationURL is failure, then return a network error.
    return Promise.resolve(makeNetworkError(err))
  }

  // 6. If locationURL’s scheme is not an HTTP(S) scheme, then return a network
  // error.
  if (!urlIsHttpHttpsScheme(locationURL)) {
    return Promise.resolve(makeNetworkError('URL scheme must be a HTTP(S) scheme'))
  }

  // 7. If request’s redirect count is 20, then return a network error.
  if (request.redirectCount === 20) {
    return Promise.resolve(makeNetworkError('redirect count exceeded'))
  }

  // 8. Increase request’s redirect count by 1.
  request.redirectCount += 1

  // 9. If request’s mode is "cors", locationURL includes credentials, and
  // request’s origin is not same origin with locationURL’s origin, then return
  //  a network error.
  if (
    request.mode === 'cors' &&
    (locationURL.username || locationURL.password) &&
    !sameOrigin(request, locationURL)
  ) {
    return Promise.resolve(makeNetworkError('cross origin not allowed for request mode "cors"'))
  }

  // 10. If request’s response tainting is "cors" and locationURL includes
  // credentials, then return a network error.
  if (
    request.responseTainting === 'cors' &&
    (locationURL.username || locationURL.password)
  ) {
    return Promise.resolve(makeNetworkError(
      'URL cannot contain credentials for request mode "cors"'
    ))
  }

  // 11. If actualResponse’s status is not 303, request’s body is non-null,
  // and request’s body’s source is null, then return a network error.
  if (
    actualResponse.status !== 303 &&
    request.body != null &&
    request.body.source == null
  ) {
    return Promise.resolve(makeNetworkError())
  }

  // 12. If one of the following is true
  // - actualResponse’s status is 301 or 302 and request’s method is `POST`
  // - actualResponse’s status is 303 and request’s method is not `GET` or `HEAD`
  if (
    ([301, 302].includes(actualResponse.status) && request.method === 'POST') ||
    (actualResponse.status === 303 &&
      !GET_OR_HEAD.includes(request.method))
  ) {
    // then:
    // 1. Set request’s method to `GET` and request’s body to null.
    request.method = 'GET'
    request.body = null

    // 2. For each headerName of request-body-header name, delete headerName from
    // request’s header list.
    for (const headerName of requestBodyHeader) {
      request.headersList.delete(headerName)
    }
  }

  // 13. If request’s current URL’s origin is not same origin with locationURL’s
  //     origin, then for each headerName of CORS non-wildcard request-header name,
  //     delete headerName from request’s header list.
  if (!sameOrigin(requestCurrentURL(request), locationURL)) {
    // https://fetch.spec.whatwg.org/#cors-non-wildcard-request-header-name
    request.headersList.delete('authorization', true)

    // https://fetch.spec.whatwg.org/#authentication-entries
    request.headersList.delete('proxy-authorization', true)

    // "Cookie" and "Host" are forbidden request-headers, which undici doesn't implement.
    request.headersList.delete('cookie', true)
    request.headersList.delete('host', true)
  }

  // 14. If request’s body is non-null, then set request’s body to the first return
  // value of safely extracting request’s body’s source.
  if (request.body != null) {
    assert(request.body.source != null)
    request.body = safelyExtractBody(request.body.source)[0]
  }

  // 15. Let timingInfo be fetchParams’s timing info.
  const timingInfo = fetchParams.timingInfo

  // 16. Set timingInfo’s redirect end time and post-redirect start time to the
  // coarsened shared current time given fetchParams’s cross-origin isolated
  // capability.
  timingInfo.redirectEndTime = timingInfo.postRedirectStartTime =
    coarsenedSharedCurrentTime(fetchParams.crossOriginIsolatedCapability)

  // 17. If timingInfo’s redirect start time is 0, then set timingInfo’s
  //  redirect start time to timingInfo’s start time.
  if (timingInfo.redirectStartTime === 0) {
    timingInfo.redirectStartTime = timingInfo.startTime
  }

  // 18. Append locationURL to request’s URL list.
  request.urlList.push(locationURL)

  // 19. Invoke set request’s referrer policy on redirect on request and
  // actualResponse.
  setRequestReferrerPolicyOnRedirect(request, actualResponse)

  // 20. Return the result of running main fetch given fetchParams and true.
  return mainFetch(fetchParams, true)
}

// https://fetch.spec.whatwg.org/#http-network-or-cache-fetch
async function httpNetworkOrCacheFetch (
  fetchParams,
  isAuthenticationFetch = false,
  isNewConnectionFetch = false
) {
  // 1. Let request be fetchParams’s request.
  const request = fetchParams.request

  // 2. Let httpFetchParams be null.
  let httpFetchParams = null

  // 3. Let httpRequest be null.
  let httpRequest = null

  // 4. Let response be null.
  let response = null

  // 5. Let storedResponse be null.
  // TODO: cache

  // 6. Let httpCache be null.
  const httpCache = null

  // 7. Let the revalidatingFlag be unset.
  const revalidatingFlag = false

  // 8. Run these steps, but abort when the ongoing fetch is terminated:

  //    1. If request’s window is "no-window" and request’s redirect mode is
  //    "error", then set httpFetchParams to fetchParams and httpRequest to
  //    request.
  if (request.window === 'no-window' && request.redirect === 'error') {
    httpFetchParams = fetchParams
    httpRequest = request
  } else {
    // Otherwise:

    // 1. Set httpRequest to a clone of request.
    httpRequest = cloneRequest(request)

    // 2. Set httpFetchParams to a copy of fetchParams.
    httpFetchParams = { ...fetchParams }

    // 3. Set httpFetchParams’s request to httpRequest.
    httpFetchParams.request = httpRequest
  }

  //    3. Let includeCredentials be true if one of
  const includeCredentials =
    request.credentials === 'include' ||
    (request.credentials === 'same-origin' &&
      request.responseTainting === 'basic')

  //    4. Let contentLength be httpRequest’s body’s length, if httpRequest’s
  //    body is non-null; otherwise null.
  const contentLength = httpRequest.body ? httpRequest.body.length : null

  //    5. Let contentLengthHeaderValue be null.
  let contentLengthHeaderValue = null

  //    6. If httpRequest’s body is null and httpRequest’s method is `POST` or
  //    `PUT`, then set contentLengthHeaderValue to `0`.
  if (
    httpRequest.body == null &&
    ['POST', 'PUT'].includes(httpRequest.method)
  ) {
    contentLengthHeaderValue = '0'
  }

  //    7. If contentLength is non-null, then set contentLengthHeaderValue to
  //    contentLength, serialized and isomorphic encoded.
  if (contentLength != null) {
    contentLengthHeaderValue = isomorphicEncode(`${contentLength}`)
  }

  //    8. If contentLengthHeaderValue is non-null, then append
  //    `Content-Length`/contentLengthHeaderValue to httpRequest’s header
  //    list.
  if (contentLengthHeaderValue != null) {
    httpRequest.headersList.append('content-length', contentLengthHeaderValue, true)
  }

  //    9. If contentLengthHeaderValue is non-null, then append (`Content-Length`,
  //    contentLengthHeaderValue) to httpRequest’s header list.

  //    10. If contentLength is non-null and httpRequest’s keepalive is true,
  //    then:
  if (contentLength != null && httpRequest.keepalive) {
    // NOTE: keepalive is a noop outside of browser context.
  }

  //    11. If httpRequest’s referrer is a URL, then append
  //    `Referer`/httpRequest’s referrer, serialized and isomorphic encoded,
  //     to httpRequest’s header list.
  if (httpRequest.referrer instanceof URL) {
    httpRequest.headersList.append('referer', isomorphicEncode(httpRequest.referrer.href), true)
  }

  //    12. Append a request `Origin` header for httpRequest.
  appendRequestOriginHeader(httpRequest)

  //    13. Append the Fetch metadata headers for httpRequest. [FETCH-METADATA]
  appendFetchMetadata(httpRequest)

  //    14. If httpRequest’s header list does not contain `User-Agent`, then
  //    user agents should append `User-Agent`/default `User-Agent` value to
  //    httpRequest’s header list.
  if (!httpRequest.headersList.contains('user-agent', true)) {
    httpRequest.headersList.append('user-agent', defaultUserAgent)
  }

  //    15. If httpRequest’s cache mode is "default" and httpRequest’s header
  //    list contains `If-Modified-Since`, `If-None-Match`,
  //    `If-Unmodified-Since`, `If-Match`, or `If-Range`, then set
  //    httpRequest’s cache mode to "no-store".
  if (
    httpRequest.cache === 'default' &&
    (httpRequest.headersList.contains('if-modified-since', true) ||
      httpRequest.headersList.contains('if-none-match', true) ||
      httpRequest.headersList.contains('if-unmodified-since', true) ||
      httpRequest.headersList.contains('if-match', true) ||
      httpRequest.headersList.contains('if-range', true))
  ) {
    httpRequest.cache = 'no-store'
  }

  //    16. If httpRequest’s cache mode is "no-cache", httpRequest’s prevent
  //    no-cache cache-control header modification flag is unset, and
  //    httpRequest’s header list does not contain `Cache-Control`, then append
  //    `Cache-Control`/`max-age=0` to httpRequest’s header list.
  if (
    httpRequest.cache === 'no-cache' &&
    !httpRequest.preventNoCacheCacheControlHeaderModification &&
    !httpRequest.headersList.contains('cache-control', true)
  ) {
    httpRequest.headersList.append('cache-control', 'max-age=0', true)
  }

  //    17. If httpRequest’s cache mode is "no-store" or "reload", then:
  if (httpRequest.cache === 'no-store' || httpRequest.cache === 'reload') {
    // 1. If httpRequest’s header list does not contain `Pragma`, then append
    // `Pragma`/`no-cache` to httpRequest’s header list.
    if (!httpRequest.headersList.contains('pragma', true)) {
      httpRequest.headersList.append('pragma', 'no-cache', true)
    }

    // 2. If httpRequest’s header list does not contain `Cache-Control`,
    // then append `Cache-Control`/`no-cache` to httpRequest’s header list.
    if (!httpRequest.headersList.contains('cache-control', true)) {
      httpRequest.headersList.append('cache-control', 'no-cache', true)
    }
  }

  //    18. If httpRequest’s header list contains `Range`, then append
  //    `Accept-Encoding`/`identity` to httpRequest’s header list.
  if (httpRequest.headersList.contains('range', true)) {
    httpRequest.headersList.append('accept-encoding', 'identity', true)
  }

  //    19. Modify httpRequest’s header list per HTTP. Do not append a given
  //    header if httpRequest’s header list contains that header’s name.
  //    TODO: https://github.com/whatwg/fetch/issues/1285#issuecomment-896560129
  if (!httpRequest.headersList.contains('accept-encoding', true)) {
    if (urlHasHttpsScheme(requestCurrentURL(httpRequest))) {
      httpRequest.headersList.append('accept-encoding', 'br, gzip, deflate', true)
    } else {
      httpRequest.headersList.append('accept-encoding', 'gzip, deflate', true)
    }
  }

  httpRequest.headersList.delete('host', true)

  //    20. If includeCredentials is true, then:
  if (includeCredentials) {
    // 1. If the user agent is not configured to block cookies for httpRequest
    // (see section 7 of [COOKIES]), then:
    // TODO: credentials
    // 2. If httpRequest’s header list does not contain `Authorization`, then:
    // TODO: credentials
  }

  //    21. If there’s a proxy-authentication entry, use it as appropriate.
  //    TODO: proxy-authentication

  //    22. Set httpCache to the result of determining the HTTP cache
  //    partition, given httpRequest.
  //    TODO: cache

  //    23. If httpCache is null, then set httpRequest’s cache mode to
  //    "no-store".
  if (httpCache == null) {
    httpRequest.cache = 'no-store'
  }

  //    24. If httpRequest’s cache mode is neither "no-store" nor "reload",
  //    then:
  if (httpRequest.cache !== 'no-store' && httpRequest.cache !== 'reload') {
    // TODO: cache
  }

  // 9. If aborted, then return the appropriate network error for fetchParams.
  // TODO

  // 10. If response is null, then:
  if (response == null) {
    // 1. If httpRequest’s cache mode is "only-if-cached", then return a
    // network error.
    if (httpRequest.cache === 'only-if-cached') {
      return makeNetworkError('only if cached')
    }

    // 2. Let forwardResponse be the result of running HTTP-network fetch
    // given httpFetchParams, includeCredentials, and isNewConnectionFetch.
    const forwardResponse = await httpNetworkFetch(
      httpFetchParams,
      includeCredentials,
      isNewConnectionFetch
    )

    // 3. If httpRequest’s method is unsafe and forwardResponse’s status is
    // in the range 200 to 399, inclusive, invalidate appropriate stored
    // responses in httpCache, as per the "Invalidation" chapter of HTTP
    // Caching, and set storedResponse to null. [HTTP-CACHING]
    if (
      !safeMethodsSet.has(httpRequest.method) &&
      forwardResponse.status >= 200 &&
      forwardResponse.status <= 399
    ) {
      // TODO: cache
    }

    // 4. If the revalidatingFlag is set and forwardResponse’s status is 304,
    // then:
    if (revalidatingFlag && forwardResponse.status === 304) {
      // TODO: cache
    }

    // 5. If response is null, then:
    if (response == null) {
      // 1. Set response to forwardResponse.
      response = forwardResponse

      // 2. Store httpRequest and forwardResponse in httpCache, as per the
      // "Storing Responses in Caches" chapter of HTTP Caching. [HTTP-CACHING]
      // TODO: cache
    }
  }

  // 11. Set response’s URL list to a clone of httpRequest’s URL list.
  response.urlList = [...httpRequest.urlList]

  // 12. If httpRequest’s header list contains `Range`, then set response’s
  // range-requested flag.
  if (httpRequest.headersList.contains('range', true)) {
    response.rangeRequested = true
  }

  // 13. Set response’s request-includes-credentials to includeCredentials.
  response.requestIncludesCredentials = includeCredentials

  // 14. If response’s status is 401, httpRequest’s response tainting is not
  // "cors", includeCredentials is true, and request’s window is an environment
  // settings object, then:
  // TODO

  // 15. If response’s status is 407, then:
  if (response.status === 407) {
    // 1. If request’s window is "no-window", then return a network error.
    if (request.window === 'no-window') {
      return makeNetworkError()
    }

    // 2. ???

    // 3. If fetchParams is canceled, then return the appropriate network error for fetchParams.
    if (isCancelled(fetchParams)) {
      return makeAppropriateNetworkError(fetchParams)
    }

    // 4. Prompt the end user as appropriate in request’s window and store
    // the result as a proxy-authentication entry. [HTTP-AUTH]
    // TODO: Invoke some kind of callback?

    // 5. Set response to the result of running HTTP-network-or-cache fetch given
    // fetchParams.
    // TODO
    return makeNetworkError('proxy authentication required')
  }

  // 16. If all of the following are true
  if (
    // response’s status is 421
    response.status === 421 &&
    // isNewConnectionFetch is false
    !isNewConnectionFetch &&
    // request’s body is null, or request’s body is non-null and request’s body’s source is non-null
    (request.body == null || request.body.source != null)
  ) {
    // then:

    // 1. If fetchParams is canceled, then return the appropriate network error for fetchParams.
    if (isCancelled(fetchParams)) {
      return makeAppropriateNetworkError(fetchParams)
    }

    // 2. Set response to the result of running HTTP-network-or-cache
    // fetch given fetchParams, isAuthenticationFetch, and true.

    // TODO (spec): The spec doesn't specify this but we need to cancel
    // the active response before we can start a new one.
    // https://github.com/whatwg/fetch/issues/1293
    fetchParams.controller.connection.destroy()

    response = await httpNetworkOrCacheFetch(
      fetchParams,
      isAuthenticationFetch,
      true
    )
  }

  // 17. If isAuthenticationFetch is true, then create an authentication entry
  if (isAuthenticationFetch) {
    // TODO
  }

  // 18. Return response.
  return response
}

// https://fetch.spec.whatwg.org/#http-network-fetch
async function httpNetworkFetch (
  fetchParams,
  includeCredentials = false,
  forceNewConnection = false
) {
  assert(!fetchParams.controller.connection || fetchParams.controller.connection.destroyed)

  fetchParams.controller.connection = {
    abort: null,
    destroyed: false,
    destroy (err, abort = true) {
      if (!this.destroyed) {
        this.destroyed = true
        if (abort) {
          this.abort?.(err ?? new DOMException('The operation was aborted.', 'AbortError'))
        }
      }
    }
  }

  // 1. Let request be fetchParams’s request.
  const request = fetchParams.request

  // 2. Let response be null.
  let response = null

  // 3. Let timingInfo be fetchParams’s timing info.
  const timingInfo = fetchParams.timingInfo

  // 4. Let httpCache be the result of determining the HTTP cache partition,
  // given request.
  // TODO: cache
  const httpCache = null

  // 5. If httpCache is null, then set request’s cache mode to "no-store".
  if (httpCache == null) {
    request.cache = 'no-store'
  }

  // 6. Let networkPartitionKey be the result of determining the network
  // partition key given request.
  // TODO

  // 7. Let newConnection be "yes" if forceNewConnection is true; otherwise
  // "no".
  const newConnection = forceNewConnection ? 'yes' : 'no' // eslint-disable-line no-unused-vars

  // 8. Switch on request’s mode:
  if (request.mode === 'websocket') {
    // Let connection be the result of obtaining a WebSocket connection,
    // given request’s current URL.
    // TODO
  } else {
    // Let connection be the result of obtaining a connection, given
    // networkPartitionKey, request’s current URL’s origin,
    // includeCredentials, and forceNewConnection.
    // TODO
  }

  // 9. Run these steps, but abort when the ongoing fetch is terminated:

  //    1. If connection is failure, then return a network error.

  //    2. Set timingInfo’s final connection timing info to the result of
  //    calling clamp and coarsen connection timing info with connection’s
  //    timing info, timingInfo’s post-redirect start time, and fetchParams’s
  //    cross-origin isolated capability.

  //    3. If connection is not an HTTP/2 connection, request’s body is non-null,
  //    and request’s body’s source is null, then append (`Transfer-Encoding`,
  //    `chunked`) to request’s header list.

  //    4. Set timingInfo’s final network-request start time to the coarsened
  //    shared current time given fetchParams’s cross-origin isolated
  //    capability.

  //    5. Set response to the result of making an HTTP request over connection
  //    using request with the following caveats:

  //        - Follow the relevant requirements from HTTP. [HTTP] [HTTP-SEMANTICS]
  //        [HTTP-COND] [HTTP-CACHING] [HTTP-AUTH]

  //        - If request’s body is non-null, and request’s body’s source is null,
  //        then the user agent may have a buffer of up to 64 kibibytes and store
  //        a part of request’s body in that buffer. If the user agent reads from
  //        request’s body beyond that buffer’s size and the user agent needs to
  //        resend request, then instead return a network error.

  //        - Set timingInfo’s final network-response start time to the coarsened
  //        shared current time given fetchParams’s cross-origin isolated capability,
  //        immediately after the user agent’s HTTP parser receives the first byte
  //        of the response (e.g., frame header bytes for HTTP/2 or response status
  //        line for HTTP/1.x).

  //        - Wait until all the headers are transmitted.

  //        - Any responses whose status is in the range 100 to 199, inclusive,
  //        and is not 101, are to be ignored, except for the purposes of setting
  //        timingInfo’s final network-response start time above.

  //    - If request’s header list contains `Transfer-Encoding`/`chunked` and
  //    response is transferred via HTTP/1.0 or older, then return a network
  //    error.

  //    - If the HTTP request results in a TLS client certificate dialog, then:

  //        1. If request’s window is an environment settings object, make the
  //        dialog available in request’s window.

  //        2. Otherwise, return a network error.

  // To transmit request’s body body, run these steps:
  let requestBody = null
  // 1. If body is null and fetchParams’s process request end-of-body is
  // non-null, then queue a fetch task given fetchParams’s process request
  // end-of-body and fetchParams’s task destination.
  if (request.body == null && fetchParams.processRequestEndOfBody) {
    queueMicrotask(() => fetchParams.processRequestEndOfBody())
  } else if (request.body != null) {
    // 2. Otherwise, if body is non-null:

    //    1. Let processBodyChunk given bytes be these steps:
    const processBodyChunk = async function * (bytes) {
      // 1. If the ongoing fetch is terminated, then abort these steps.
      if (isCancelled(fetchParams)) {
        return
      }

      // 2. Run this step in parallel: transmit bytes.
      yield bytes

      // 3. If fetchParams’s process request body is non-null, then run
      // fetchParams’s process request body given bytes’s length.
      fetchParams.processRequestBodyChunkLength?.(bytes.byteLength)
    }

    // 2. Let processEndOfBody be these steps:
    const processEndOfBody = () => {
      // 1. If fetchParams is canceled, then abort these steps.
      if (isCancelled(fetchParams)) {
        return
      }

      // 2. If fetchParams’s process request end-of-body is non-null,
      // then run fetchParams’s process request end-of-body.
      if (fetchParams.processRequestEndOfBody) {
        fetchParams.processRequestEndOfBody()
      }
    }

    // 3. Let processBodyError given e be these steps:
    const processBodyError = (e) => {
      // 1. If fetchParams is canceled, then abort these steps.
      if (isCancelled(fetchParams)) {
        return
      }

      // 2. If e is an "AbortError" DOMException, then abort fetchParams’s controller.
      if (e.name === 'AbortError') {
        fetchParams.controller.abort()
      } else {
        fetchParams.controller.terminate(e)
      }
    }

    // 4. Incrementally read request’s body given processBodyChunk, processEndOfBody,
    // processBodyError, and fetchParams’s task destination.
    requestBody = (async function * () {
      try {
        for await (const bytes of request.body.stream) {
          yield * processBodyChunk(bytes)
        }
        processEndOfBody()
      } catch (err) {
        processBodyError(err)
      }
    })()
  }

  try {
    // socket is only provided for websockets
    const { body, status, statusText, headersList, socket } = await dispatch({ body: requestBody })

    if (socket) {
      response = makeResponse({ status, statusText, headersList, socket })
    } else {
      const iterator = body[Symbol.asyncIterator]()
      fetchParams.controller.next = () => iterator.next()

      response = makeResponse({ status, statusText, headersList })
    }
  } catch (err) {
    // 10. If aborted, then:
    if (err.name === 'AbortError') {
      // 1. If connection uses HTTP/2, then transmit an RST_STREAM frame.
      fetchParams.controller.connection.destroy()

      // 2. Return the appropriate network error for fetchParams.
      return makeAppropriateNetworkError(fetchParams, err)
    }

    return makeNetworkError(err)
  }

  // 11. Let pullAlgorithm be an action that resumes the ongoing fetch
  // if it is suspended.
  const pullAlgorithm = async () => {
    await fetchParams.controller.resume()
  }

  // 12. Let cancelAlgorithm be an algorithm that aborts fetchParams’s
  // controller with reason, given reason.
  const cancelAlgorithm = (reason) => {
    // If the aborted fetch was already terminated, then we do not
    // need to do anything.
    if (!isCancelled(fetchParams)) {
      fetchParams.controller.abort(reason)
    }
  }

  // 13. Let highWaterMark be a non-negative, non-NaN number, chosen by
  // the user agent.
  // TODO

  // 14. Let sizeAlgorithm be an algorithm that accepts a chunk object
  // and returns a non-negative, non-NaN, non-infinite number, chosen by the user agent.
  // TODO

  // 15. Let stream be a new ReadableStream.
  // 16. Set up stream with byte reading support with pullAlgorithm set to pullAlgorithm,
  //     cancelAlgorithm set to cancelAlgorithm.
  const stream = new ReadableStream(
    {
      async start (controller) {
        fetchParams.controller.controller = controller
      },
      async pull (controller) {
        await pullAlgorithm(controller)
      },
      async cancel (reason) {
        await cancelAlgorithm(reason)
      },
      type: 'bytes'
    }
  )

  // 17. Run these steps, but abort when the ongoing fetch is terminated:

  //    1. Set response’s body to a new body whose stream is stream.
  response.body = { stream, source: null, length: null }

  //    2. If response is not a network error and request’s cache mode is
  //    not "no-store", then update response in httpCache for request.
  //    TODO

  //    3. If includeCredentials is true and the user agent is not configured
  //    to block cookies for request (see section 7 of [COOKIES]), then run the
  //    "set-cookie-string" parsing algorithm (see section 5.2 of [COOKIES]) on
  //    the value of each header whose name is a byte-case-insensitive match for
  //    `Set-Cookie` in response’s header list, if any, and request’s current URL.
  //    TODO

  // 18. If aborted, then:
  // TODO

  // 19. Run these steps in parallel:

  //    1. Run these steps, but abort when fetchParams is canceled:
  fetchParams.controller.onAborted = onAborted
  fetchParams.controller.on('terminated', onAborted)
  fetchParams.controller.resume = async () => {
    // 1. While true
    while (true) {
      // 1-3. See onData...

      // 4. Set bytes to the result of handling content codings given
      // codings and bytes.
      let bytes
      let isFailure
      try {
        const { done, value } = await fetchParams.controller.next()

        if (isAborted(fetchParams)) {
          break
        }

        bytes = done ? undefined : value
      } catch (err) {
        if (fetchParams.controller.ended && !timingInfo.encodedBodySize) {
          // zlib doesn't like empty streams.
          bytes = undefined
        } else {
          bytes = err

          // err may be propagated from the result of calling readablestream.cancel,
          // which might not be an error. https://github.com/nodejs/undici/issues/2009
          isFailure = true
        }
      }

      if (bytes === undefined) {
        // 2. Otherwise, if the bytes transmission for response’s message
        // body is done normally and stream is readable, then close
        // stream, finalize response for fetchParams and response, and
        // abort these in-parallel steps.
        readableStreamClose(fetchParams.controller.controller)

        finalizeResponse(fetchParams, response)

        return
      }

      // 5. Increase timingInfo’s decoded body size by bytes’s length.
      timingInfo.decodedBodySize += bytes?.byteLength ?? 0

      // 6. If bytes is failure, then terminate fetchParams’s controller.
      if (isFailure) {
        fetchParams.controller.terminate(bytes)
        return
      }

      // 7. Enqueue a Uint8Array wrapping an ArrayBuffer containing bytes
      // into stream.
      const buffer = new Uint8Array(bytes)
      if (buffer.byteLength) {
        fetchParams.controller.controller.enqueue(buffer)
      }

      // 8. If stream is errored, then terminate the ongoing fetch.
      if (isErrored(stream)) {
        fetchParams.controller.terminate()
        return
      }

      // 9. If stream doesn’t need more data ask the user agent to suspend
      // the ongoing fetch.
      if (fetchParams.controller.controller.desiredSize <= 0) {
        return
      }
    }
  }

  //    2. If aborted, then:
  function onAborted (reason) {
    // 2. If fetchParams is aborted, then:
    if (isAborted(fetchParams)) {
      // 1. Set response’s aborted flag.
      response.aborted = true

      // 2. If stream is readable, then error stream with the result of
      //    deserialize a serialized abort reason given fetchParams’s
      //    controller’s serialized abort reason and an
      //    implementation-defined realm.
      if (isReadable(stream)) {
        fetchParams.controller.controller.error(
          fetchParams.controller.serializedAbortReason
        )
      }
    } else {
      // 3. Otherwise, if stream is readable, error stream with a TypeError.
      if (isReadable(stream)) {
        fetchParams.controller.controller.error(new TypeError('terminated', {
          cause: isErrorLike(reason) ? reason : undefined
        }))
      }
    }

    // 4. If connection uses HTTP/2, then transmit an RST_STREAM frame.
    // 5. Otherwise, the user agent should close connection unless it would be bad for performance to do so.
    fetchParams.controller.connection.destroy()
  }

  // 20. Return response.
  return response

  function dispatch ({ body }) {
    const url = requestCurrentURL(request)
    /** @type {import('../..').Agent} */
    const agent = fetchParams.controller.dispatcher

    return new Promise((resolve, reject) => agent.dispatch(
      {
        path: url.pathname + url.search,
        origin: url.origin,
        method: request.method,
        body: agent.isMockActive ? request.body && (request.body.source || request.body.stream) : body,
        headers: request.headersList.entries,
        maxRedirections: 0,
        upgrade: request.mode === 'websocket' ? 'websocket' : undefined
      },
      {
        body: null,
        abort: null,

        onConnect (abort) {
          // TODO (fix): Do we need connection here?
          const { connection } = fetchParams.controller

          // Set timingInfo’s final connection timing info to the result of calling clamp and coarsen
          // connection timing info with connection’s timing info, timingInfo’s post-redirect start
          // time, and fetchParams’s cross-origin isolated capability.
          // TODO: implement connection timing
          timingInfo.finalConnectionTimingInfo = clampAndCoarsenConnectionTimingInfo(undefined, timingInfo.postRedirectStartTime, fetchParams.crossOriginIsolatedCapability)

          if (connection.destroyed) {
            abort(new DOMException('The operation was aborted.', 'AbortError'))
          } else {
            fetchParams.controller.on('terminated', abort)
            this.abort = connection.abort = abort
          }

          // Set timingInfo’s final network-request start time to the coarsened shared current time given
          // fetchParams’s cross-origin isolated capability.
          timingInfo.finalNetworkRequestStartTime = coarsenedSharedCurrentTime(fetchParams.crossOriginIsolatedCapability)
        },

        onResponseStarted () {
          // Set timingInfo’s final network-response start time to the coarsened shared current
          // time given fetchParams’s cross-origin isolated capability, immediately after the
          // user agent’s HTTP parser receives the first byte of the response (e.g., frame header
          // bytes for HTTP/2 or response status line for HTTP/1.x).
          timingInfo.finalNetworkResponseStartTime = coarsenedSharedCurrentTime(fetchParams.crossOriginIsolatedCapability)
        },

        onHeaders (status, rawHeaders, resume, statusText) {
          if (status < 200) {
            return
          }

          let location = ''

          const headersList = new HeadersList()

          for (let i = 0; i < rawHeaders.length; i += 2) {
            headersList.append(bufferToLowerCasedHeaderName(rawHeaders[i]), rawHeaders[i + 1].toString('latin1'), true)
          }
          location = headersList.get('location', true)

          this.body = new Readable({ read: resume })

          const decoders = []

          const willFollow = location && request.redirect === 'follow' &&
            redirectStatusSet.has(status)

          // https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Encoding
          if (request.method !== 'HEAD' && request.method !== 'CONNECT' && !nullBodyStatus.includes(status) && !willFollow) {
            // https://www.rfc-editor.org/rfc/rfc7231#section-3.1.2.1
            const contentEncoding = headersList.get('content-encoding', true)
            // "All content-coding values are case-insensitive..."
            /** @type {string[]} */
            const codings = contentEncoding ? contentEncoding.toLowerCase().split(',') : []

            // Limit the number of content-encodings to prevent resource exhaustion.
            // CVE fix similar to urllib3 (GHSA-gm62-xv2j-4w53) and curl (CVE-2022-32206).
            const maxContentEncodings = 5
            if (codings.length > maxContentEncodings) {
              reject(new Error(`too many content-encodings in response: ${codings.length}, maximum allowed is ${maxContentEncodings}`))
              return true
            }

            for (let i = codings.length - 1; i >= 0; --i) {
              const coding = codings[i].trim()
              // https://www.rfc-editor.org/rfc/rfc9112.html#section-7.2
              if (coding === 'x-gzip' || coding === 'gzip') {
                decoders.push(zlib.createGunzip({
                  // Be less strict when decoding compressed responses, since sometimes
                  // servers send slightly invalid responses that are still accepted
                  // by common browsers.
                  // Always using Z_SYNC_FLUSH is what cURL does.
                  flush: zlib.constants.Z_SYNC_FLUSH,
                  finishFlush: zlib.constants.Z_SYNC_FLUSH
                }))
              } else if (coding === 'deflate') {
                decoders.push(createInflate({
                  flush: zlib.constants.Z_SYNC_FLUSH,
                  finishFlush: zlib.constants.Z_SYNC_FLUSH
                }))
              } else if (coding === 'br') {
                decoders.push(zlib.createBrotliDecompress({
                  flush: zlib.constants.BROTLI_OPERATION_FLUSH,
                  finishFlush: zlib.constants.BROTLI_OPERATION_FLUSH
                }))
              } else {
                decoders.length = 0
                break
              }
            }
          }

          const onError = this.onError.bind(this)

          resolve({
            status,
            statusText,
            headersList,
            body: decoders.length
              ? pipeline(this.body, ...decoders, (err) => {
                if (err) {
                  this.onError(err)
                }
              }).on('error', onError)
              : this.body.on('error', onError)
          })

          return true
        },

        onData (chunk) {
          if (fetchParams.controller.dump) {
            return
          }

          // 1. If one or more bytes have been transmitted from response’s
          // message body, then:

          //  1. Let bytes be the transmitted bytes.
          const bytes = chunk

          //  2. Let codings be the result of extracting header list values
          //  given `Content-Encoding` and response’s header list.
          //  See pullAlgorithm.

          //  3. Increase timingInfo’s encoded body size by bytes’s length.
          timingInfo.encodedBodySize += bytes.byteLength

          //  4. See pullAlgorithm...

          return this.body.push(bytes)
        },

        onComplete () {
          if (this.abort) {
            fetchParams.controller.off('terminated', this.abort)
          }

          if (fetchParams.controller.onAborted) {
            fetchParams.controller.off('terminated', fetchParams.controller.onAborted)
          }

          fetchParams.controller.ended = true

          this.body.push(null)
        },

        onError (error) {
          if (this.abort) {
            fetchParams.controller.off('terminated', this.abort)
          }

          this.body?.destroy(error)

          fetchParams.controller.terminate(error)

          reject(error)
        },

        onUpgrade (status, rawHeaders, socket) {
          if (status !== 101) {
            return
          }

          const headersList = new HeadersList()

          for (let i = 0; i < rawHeaders.length; i += 2) {
            headersList.append(bufferToLowerCasedHeaderName(rawHeaders[i]), rawHeaders[i + 1].toString('latin1'), true)
          }

          resolve({
            status,
            statusText: STATUS_CODES[status],
            headersList,
            socket
          })

          return true
        }
      }
    ))
  }
}

module.exports = {
  fetch,
  Fetch,
  fetching,
  finalizeAndReportTiming
}


/***/ }),

/***/ 9967:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {

/* globals AbortController */



const { extractBody, mixinBody, cloneBody, bodyUnusable } = __nccwpck_require__(4492)
const { Headers, fill: fillHeaders, HeadersList, setHeadersGuard, getHeadersGuard, setHeadersList, getHeadersList } = __nccwpck_require__(660)
const { FinalizationRegistry } = __nccwpck_require__(6653)()
const util = __nccwpck_require__(3440)
const nodeUtil = __nccwpck_require__(7975)
const {
  isValidHTTPToken,
  sameOrigin,
  environmentSettingsObject
} = __nccwpck_require__(3168)
const {
  forbiddenMethodsSet,
  corsSafeListedMethodsSet,
  referrerPolicy,
  requestRedirect,
  requestMode,
  requestCredentials,
  requestCache,
  requestDuplex
} = __nccwpck_require__(4495)
const { kEnumerableProperty, normalizedMethodRecordsBase, normalizedMethodRecords } = util
const { kHeaders, kSignal, kState, kDispatcher } = __nccwpck_require__(3627)
const { webidl } = __nccwpck_require__(5893)
const { URLSerializer } = __nccwpck_require__(1900)
const { kConstruct } = __nccwpck_require__(6443)
const assert = __nccwpck_require__(4589)
const { getMaxListeners, setMaxListeners, getEventListeners, defaultMaxListeners } = __nccwpck_require__(8474)

const kAbortController = Symbol('abortController')

const requestFinalizer = new FinalizationRegistry(({ signal, abort }) => {
  signal.removeEventListener('abort', abort)
})

const dependentControllerMap = new WeakMap()

function buildAbort (acRef) {
  return abort

  function abort () {
    const ac = acRef.deref()
    if (ac !== undefined) {
      // Currently, there is a problem with FinalizationRegistry.
      // https://github.com/nodejs/node/issues/49344
      // https://github.com/nodejs/node/issues/47748
      // In the case of abort, the first step is to unregister from it.
      // If the controller can refer to it, it is still registered.
      // It will be removed in the future.
      requestFinalizer.unregister(abort)

      // Unsubscribe a listener.
      // FinalizationRegistry will no longer be called, so this must be done.
      this.removeEventListener('abort', abort)

      ac.abort(this.reason)

      const controllerList = dependentControllerMap.get(ac.signal)

      if (controllerList !== undefined) {
        if (controllerList.size !== 0) {
          for (const ref of controllerList) {
            const ctrl = ref.deref()
            if (ctrl !== undefined) {
              ctrl.abort(this.reason)
            }
          }
          controllerList.clear()
        }
        dependentControllerMap.delete(ac.signal)
      }
    }
  }
}

let patchMethodWarning = false

// https://fetch.spec.whatwg.org/#request-class
class Request {
  // https://fetch.spec.whatwg.org/#dom-request
  constructor (input, init = {}) {
    webidl.util.markAsUncloneable(this)
    if (input === kConstruct) {
      return
    }

    const prefix = 'Request constructor'
    webidl.argumentLengthCheck(arguments, 1, prefix)

    input = webidl.converters.RequestInfo(input, prefix, 'input')
    init = webidl.converters.RequestInit(init, prefix, 'init')

    // 1. Let request be null.
    let request = null

    // 2. Let fallbackMode be null.
    let fallbackMode = null

    // 3. Let baseURL be this’s relevant settings object’s API base URL.
    const baseUrl = environmentSettingsObject.settingsObject.baseUrl

    // 4. Let signal be null.
    let signal = null

    // 5. If input is a string, then:
    if (typeof input === 'string') {
      this[kDispatcher] = init.dispatcher

      // 1. Let parsedURL be the result of parsing input with baseURL.
      // 2. If parsedURL is failure, then throw a TypeError.
      let parsedURL
      try {
        parsedURL = new URL(input, baseUrl)
      } catch (err) {
        throw new TypeError('Failed to parse URL from ' + input, { cause: err })
      }

      // 3. If parsedURL includes credentials, then throw a TypeError.
      if (parsedURL.username || parsedURL.password) {
        throw new TypeError(
          'Request cannot be constructed from a URL that includes credentials: ' +
            input
        )
      }

      // 4. Set request to a new request whose URL is parsedURL.
      request = makeRequest({ urlList: [parsedURL] })

      // 5. Set fallbackMode to "cors".
      fallbackMode = 'cors'
    } else {
      this[kDispatcher] = init.dispatcher || input[kDispatcher]

      // 6. Otherwise:

      // 7. Assert: input is a Request object.
      assert(input instanceof Request)

      // 8. Set request to input’s request.
      request = input[kState]

      // 9. Set signal to input’s signal.
      signal = input[kSignal]
    }

    // 7. Let origin be this’s relevant settings object’s origin.
    const origin = environmentSettingsObject.settingsObject.origin

    // 8. Let window be "client".
    let window = 'client'

    // 9. If request’s window is an environment settings object and its origin
    // is same origin with origin, then set window to request’s window.
    if (
      request.window?.constructor?.name === 'EnvironmentSettingsObject' &&
      sameOrigin(request.window, origin)
    ) {
      window = request.window
    }

    // 10. If init["window"] exists and is non-null, then throw a TypeError.
    if (init.window != null) {
      throw new TypeError(`'window' option '${window}' must be null`)
    }

    // 11. If init["window"] exists, then set window to "no-window".
    if ('window' in init) {
      window = 'no-window'
    }

    // 12. Set request to a new request with the following properties:
    request = makeRequest({
      // URL request’s URL.
      // undici implementation note: this is set as the first item in request's urlList in makeRequest
      // method request’s method.
      method: request.method,
      // header list A copy of request’s header list.
      // undici implementation note: headersList is cloned in makeRequest
      headersList: request.headersList,
      // unsafe-request flag Set.
      unsafeRequest: request.unsafeRequest,
      // client This’s relevant settings object.
      client: environmentSettingsObject.settingsObject,
      // window window.
      window,
      // priority request’s priority.
      priority: request.priority,
      // origin request’s origin. The propagation of the origin is only significant for navigation requests
      // being handled by a service worker. In this scenario a request can have an origin that is different
      // from the current client.
      origin: request.origin,
      // referrer request’s referrer.
      referrer: request.referrer,
      // referrer policy request’s referrer policy.
      referrerPolicy: request.referrerPolicy,
      // mode request’s mode.
      mode: request.mode,
      // credentials mode request’s credentials mode.
      credentials: request.credentials,
      // cache mode request’s cache mode.
      cache: request.cache,
      // redirect mode request’s redirect mode.
      redirect: request.redirect,
      // integrity metadata request’s integrity metadata.
      integrity: request.integrity,
      // keepalive request’s keepalive.
      keepalive: request.keepalive,
      // reload-navigation flag request’s reload-navigation flag.
      reloadNavigation: request.reloadNavigation,
      // history-navigation flag request’s history-navigation flag.
      historyNavigation: request.historyNavigation,
      // URL list A clone of request’s URL list.
      urlList: [...request.urlList]
    })

    const initHasKey = Object.keys(init).length !== 0

    // 13. If init is not empty, then:
    if (initHasKey) {
      // 1. If request’s mode is "navigate", then set it to "same-origin".
      if (request.mode === 'navigate') {
        request.mode = 'same-origin'
      }

      // 2. Unset request’s reload-navigation flag.
      request.reloadNavigation = false

      // 3. Unset request’s history-navigation flag.
      request.historyNavigation = false

      // 4. Set request’s origin to "client".
      request.origin = 'client'

      // 5. Set request’s referrer to "client"
      request.referrer = 'client'

      // 6. Set request’s referrer policy to the empty string.
      request.referrerPolicy = ''

      // 7. Set request’s URL to request’s current URL.
      request.url = request.urlList[request.urlList.length - 1]

      // 8. Set request’s URL list to « request’s URL ».
      request.urlList = [request.url]
    }

    // 14. If init["referrer"] exists, then:
    if (init.referrer !== undefined) {
      // 1. Let referrer be init["referrer"].
      const referrer = init.referrer

      // 2. If referrer is the empty string, then set request’s referrer to "no-referrer".
      if (referrer === '') {
        request.referrer = 'no-referrer'
      } else {
        // 1. Let parsedReferrer be the result of parsing referrer with
        // baseURL.
        // 2. If parsedReferrer is failure, then throw a TypeError.
        let parsedReferrer
        try {
          parsedReferrer = new URL(referrer, baseUrl)
        } catch (err) {
          throw new TypeError(`Referrer "${referrer}" is not a valid URL.`, { cause: err })
        }

        // 3. If one of the following is true
        // - parsedReferrer’s scheme is "about" and path is the string "client"
        // - parsedReferrer’s origin is not same origin with origin
        // then set request’s referrer to "client".
        if (
          (parsedReferrer.protocol === 'about:' && parsedReferrer.hostname === 'client') ||
          (origin && !sameOrigin(parsedReferrer, environmentSettingsObject.settingsObject.baseUrl))
        ) {
          request.referrer = 'client'
        } else {
          // 4. Otherwise, set request’s referrer to parsedReferrer.
          request.referrer = parsedReferrer
        }
      }
    }

    // 15. If init["referrerPolicy"] exists, then set request’s referrer policy
    // to it.
    if (init.referrerPolicy !== undefined) {
      request.referrerPolicy = init.referrerPolicy
    }

    // 16. Let mode be init["mode"] if it exists, and fallbackMode otherwise.
    let mode
    if (init.mode !== undefined) {
      mode = init.mode
    } else {
      mode = fallbackMode
    }

    // 17. If mode is "navigate", then throw a TypeError.
    if (mode === 'navigate') {
      throw webidl.errors.exception({
        header: 'Request constructor',
        message: 'invalid request mode navigate.'
      })
    }

    // 18. If mode is non-null, set request’s mode to mode.
    if (mode != null) {
      request.mode = mode
    }

    // 19. If init["credentials"] exists, then set request’s credentials mode
    // to it.
    if (init.credentials !== undefined) {
      request.credentials = init.credentials
    }

    // 18. If init["cache"] exists, then set request’s cache mode to it.
    if (init.cache !== undefined) {
      request.cache = init.cache
    }

    // 21. If request’s cache mode is "only-if-cached" and request’s mode is
    // not "same-origin", then throw a TypeError.
    if (request.cache === 'only-if-cached' && request.mode !== 'same-origin') {
      throw new TypeError(
        "'only-if-cached' can be set only with 'same-origin' mode"
      )
    }

    // 22. If init["redirect"] exists, then set request’s redirect mode to it.
    if (init.redirect !== undefined) {
      request.redirect = init.redirect
    }

    // 23. If init["integrity"] exists, then set request’s integrity metadata to it.
    if (init.integrity != null) {
      request.integrity = String(init.integrity)
    }

    // 24. If init["keepalive"] exists, then set request’s keepalive to it.
    if (init.keepalive !== undefined) {
      request.keepalive = Boolean(init.keepalive)
    }

    // 25. If init["method"] exists, then:
    if (init.method !== undefined) {
      // 1. Let method be init["method"].
      let method = init.method

      const mayBeNormalized = normalizedMethodRecords[method]

      if (mayBeNormalized !== undefined) {
        // Note: Bypass validation DELETE, GET, HEAD, OPTIONS, POST, PUT, PATCH and these lowercase ones
        request.method = mayBeNormalized
      } else {
        // 2. If method is not a method or method is a forbidden method, then
        // throw a TypeError.
        if (!isValidHTTPToken(method)) {
          throw new TypeError(`'${method}' is not a valid HTTP method.`)
        }

        const upperCase = method.toUpperCase()

        if (forbiddenMethodsSet.has(upperCase)) {
          throw new TypeError(`'${method}' HTTP method is unsupported.`)
        }

        // 3. Normalize method.
        // https://fetch.spec.whatwg.org/#concept-method-normalize
        // Note: must be in uppercase
        method = normalizedMethodRecordsBase[upperCase] ?? method

        // 4. Set request’s method to method.
        request.method = method
      }

      if (!patchMethodWarning && request.method === 'patch') {
        process.emitWarning('Using `patch` is highly likely to result in a `405 Method Not Allowed`. `PATCH` is much more likely to succeed.', {
          code: 'UNDICI-FETCH-patch'
        })

        patchMethodWarning = true
      }
    }

    // 26. If init["signal"] exists, then set signal to it.
    if (init.signal !== undefined) {
      signal = init.signal
    }

    // 27. Set this’s request to request.
    this[kState] = request

    // 28. Set this’s signal to a new AbortSignal object with this’s relevant
    // Realm.
    // TODO: could this be simplified with AbortSignal.any
    // (https://dom.spec.whatwg.org/#dom-abortsignal-any)
    const ac = new AbortController()
    this[kSignal] = ac.signal

    // 29. If signal is not null, then make this’s signal follow signal.
    if (signal != null) {
      if (
        !signal ||
        typeof signal.aborted !== 'boolean' ||
        typeof signal.addEventListener !== 'function'
      ) {
        throw new TypeError(
          "Failed to construct 'Request': member signal is not of type AbortSignal."
        )
      }

      if (signal.aborted) {
        ac.abort(signal.reason)
      } else {
        // Keep a strong ref to ac while request object
        // is alive. This is needed to prevent AbortController
        // from being prematurely garbage collected.
        // See, https://github.com/nodejs/undici/issues/1926.
        this[kAbortController] = ac

        const acRef = new WeakRef(ac)
        const abort = buildAbort(acRef)

        // Third-party AbortControllers may not work with these.
        // See, https://github.com/nodejs/undici/pull/1910#issuecomment-1464495619.
        try {
          // If the max amount of listeners is equal to the default, increase it
          // This is only available in node >= v19.9.0
          if (typeof getMaxListeners === 'function' && getMaxListeners(signal) === defaultMaxListeners) {
            setMaxListeners(1500, signal)
          } else if (getEventListeners(signal, 'abort').length >= defaultMaxListeners) {
            setMaxListeners(1500, signal)
          }
        } catch {}

        util.addAbortListener(signal, abort)
        // The third argument must be a registry key to be unregistered.
        // Without it, you cannot unregister.
        // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/FinalizationRegistry
        // abort is used as the unregister key. (because it is unique)
        requestFinalizer.register(ac, { signal, abort }, abort)
      }
    }

    // 30. Set this’s headers to a new Headers object with this’s relevant
    // Realm, whose header list is request’s header list and guard is
    // "request".
    this[kHeaders] = new Headers(kConstruct)
    setHeadersList(this[kHeaders], request.headersList)
    setHeadersGuard(this[kHeaders], 'request')

    // 31. If this’s request’s mode is "no-cors", then:
    if (mode === 'no-cors') {
      // 1. If this’s request’s method is not a CORS-safelisted method,
      // then throw a TypeError.
      if (!corsSafeListedMethodsSet.has(request.method)) {
        throw new TypeError(
          `'${request.method} is unsupported in no-cors mode.`
        )
      }

      // 2. Set this’s headers’s guard to "request-no-cors".
      setHeadersGuard(this[kHeaders], 'request-no-cors')
    }

    // 32. If init is not empty, then:
    if (initHasKey) {
      /** @type {HeadersList} */
      const headersList = getHeadersList(this[kHeaders])
      // 1. Let headers be a copy of this’s headers and its associated header
      // list.
      // 2. If init["headers"] exists, then set headers to init["headers"].
      const headers = init.headers !== undefined ? init.headers : new HeadersList(headersList)

      // 3. Empty this’s headers’s header list.
      headersList.clear()

      // 4. If headers is a Headers object, then for each header in its header
      // list, append header’s name/header’s value to this’s headers.
      if (headers instanceof HeadersList) {
        for (const { name, value } of headers.rawValues()) {
          headersList.append(name, value, false)
        }
        // Note: Copy the `set-cookie` meta-data.
        headersList.cookies = headers.cookies
      } else {
        // 5. Otherwise, fill this’s headers with headers.
        fillHeaders(this[kHeaders], headers)
      }
    }

    // 33. Let inputBody be input’s request’s body if input is a Request
    // object; otherwise null.
    const inputBody = input instanceof Request ? input[kState].body : null

    // 34. If either init["body"] exists and is non-null or inputBody is
    // non-null, and request’s method is `GET` or `HEAD`, then throw a
    // TypeError.
    if (
      (init.body != null || inputBody != null) &&
      (request.method === 'GET' || request.method === 'HEAD')
    ) {
      throw new TypeError('Request with GET/HEAD method cannot have body.')
    }

    // 35. Let initBody be null.
    let initBody = null

    // 36. If init["body"] exists and is non-null, then:
    if (init.body != null) {
      // 1. Let Content-Type be null.
      // 2. Set initBody and Content-Type to the result of extracting
      // init["body"], with keepalive set to request’s keepalive.
      const [extractedBody, contentType] = extractBody(
        init.body,
        request.keepalive
      )
      initBody = extractedBody

      // 3, If Content-Type is non-null and this’s headers’s header list does
      // not contain `Content-Type`, then append `Content-Type`/Content-Type to
      // this’s headers.
      if (contentType && !getHeadersList(this[kHeaders]).contains('content-type', true)) {
        this[kHeaders].append('content-type', contentType)
      }
    }

    // 37. Let inputOrInitBody be initBody if it is non-null; otherwise
    // inputBody.
    const inputOrInitBody = initBody ?? inputBody

    // 38. If inputOrInitBody is non-null and inputOrInitBody’s source is
    // null, then:
    if (inputOrInitBody != null && inputOrInitBody.source == null) {
      // 1. If initBody is non-null and init["duplex"] does not exist,
      //    then throw a TypeError.
      if (initBody != null && init.duplex == null) {
        throw new TypeError('RequestInit: duplex option is required when sending a body.')
      }

      // 2. If this’s request’s mode is neither "same-origin" nor "cors",
      // then throw a TypeError.
      if (request.mode !== 'same-origin' && request.mode !== 'cors') {
        throw new TypeError(
          'If request is made from ReadableStream, mode should be "same-origin" or "cors"'
        )
      }

      // 3. Set this’s request’s use-CORS-preflight flag.
      request.useCORSPreflightFlag = true
    }

    // 39. Let finalBody be inputOrInitBody.
    let finalBody = inputOrInitBody

    // 40. If initBody is null and inputBody is non-null, then:
    if (initBody == null && inputBody != null) {
      // 1. If input is unusable, then throw a TypeError.
      if (bodyUnusable(input)) {
        throw new TypeError(
          'Cannot construct a Request with a Request object that has already been used.'
        )
      }

      // 2. Set finalBody to the result of creating a proxy for inputBody.
      // https://streams.spec.whatwg.org/#readablestream-create-a-proxy
      const identityTransform = new TransformStream()
      inputBody.stream.pipeThrough(identityTransform)
      finalBody = {
        source: inputBody.source,
        length: inputBody.length,
        stream: identityTransform.readable
      }
    }

    // 41. Set this’s request’s body to finalBody.
    this[kState].body = finalBody
  }

  // Returns request’s HTTP method, which is "GET" by default.
  get method () {
    webidl.brandCheck(this, Request)

    // The method getter steps are to return this’s request’s method.
    return this[kState].method
  }

  // Returns the URL of request as a string.
  get url () {
    webidl.brandCheck(this, Request)

    // The url getter steps are to return this’s request’s URL, serialized.
    return URLSerializer(this[kState].url)
  }

  // Returns a Headers object consisting of the headers associated with request.
  // Note that headers added in the network layer by the user agent will not
  // be accounted for in this object, e.g., the "Host" header.
  get headers () {
    webidl.brandCheck(this, Request)

    // The headers getter steps are to return this’s headers.
    return this[kHeaders]
  }

  // Returns the kind of resource requested by request, e.g., "document"
  // or "script".
  get destination () {
    webidl.brandCheck(this, Request)

    // The destination getter are to return this’s request’s destination.
    return this[kState].destination
  }

  // Returns the referrer of request. Its value can be a same-origin URL if
  // explicitly set in init, the empty string to indicate no referrer, and
  // "about:client" when defaulting to the global’s default. This is used
  // during fetching to determine the value of the `Referer` header of the
  // request being made.
  get referrer () {
    webidl.brandCheck(this, Request)

    // 1. If this’s request’s referrer is "no-referrer", then return the
    // empty string.
    if (this[kState].referrer === 'no-referrer') {
      return ''
    }

    // 2. If this’s request’s referrer is "client", then return
    // "about:client".
    if (this[kState].referrer === 'client') {
      return 'about:client'
    }

    // Return this’s request’s referrer, serialized.
    return this[kState].referrer.toString()
  }

  // Returns the referrer policy associated with request.
  // This is used during fetching to compute the value of the request’s
  // referrer.
  get referrerPolicy () {
    webidl.brandCheck(this, Request)

    // The referrerPolicy getter steps are to return this’s request’s referrer policy.
    return this[kState].referrerPolicy
  }

  // Returns the mode associated with request, which is a string indicating
  // whether the request will use CORS, or will be restricted to same-origin
  // URLs.
  get mode () {
    webidl.brandCheck(this, Request)

    // The mode getter steps are to return this’s request’s mode.
    return this[kState].mode
  }

  // Returns the credentials mode associated with request,
  // which is a string indicating whether credentials will be sent with the
  // request always, never, or only when sent to a same-origin URL.
  get credentials () {
    // The credentials getter steps are to return this’s request’s credentials mode.
    return this[kState].credentials
  }

  // Returns the cache mode associated with request,
  // which is a string indicating how the request will
  // interact with the browser’s cache when fetching.
  get cache () {
    webidl.brandCheck(this, Request)

    // The cache getter steps are to return this’s request’s cache mode.
    return this[kState].cache
  }

  // Returns the redirect mode associated with request,
  // which is a string indicating how redirects for the
  // request will be handled during fetching. A request
  // will follow redirects by default.
  get redirect () {
    webidl.brandCheck(this, Request)

    // The redirect getter steps are to return this’s request’s redirect mode.
    return this[kState].redirect
  }

  // Returns request’s subresource integrity metadata, which is a
  // cryptographic hash of the resource being fetched. Its value
  // consists of multiple hashes separated by whitespace. [SRI]
  get integrity () {
    webidl.brandCheck(this, Request)

    // The integrity getter steps are to return this’s request’s integrity
    // metadata.
    return this[kState].integrity
  }

  // Returns a boolean indicating whether or not request can outlive the
  // global in which it was created.
  get keepalive () {
    webidl.brandCheck(this, Request)

    // The keepalive getter steps are to return this’s request’s keepalive.
    return this[kState].keepalive
  }

  // Returns a boolean indicating whether or not request is for a reload
  // navigation.
  get isReloadNavigation () {
    webidl.brandCheck(this, Request)

    // The isReloadNavigation getter steps are to return true if this’s
    // request’s reload-navigation flag is set; otherwise false.
    return this[kState].reloadNavigation
  }

  // Returns a boolean indicating whether or not request is for a history
  // navigation (a.k.a. back-forward navigation).
  get isHistoryNavigation () {
    webidl.brandCheck(this, Request)

    // The isHistoryNavigation getter steps are to return true if this’s request’s
    // history-navigation flag is set; otherwise false.
    return this[kState].historyNavigation
  }

  // Returns the signal associated with request, which is an AbortSignal
  // object indicating whether or not request has been aborted, and its
  // abort event handler.
  get signal () {
    webidl.brandCheck(this, Request)

    // The signal getter steps are to return this’s signal.
    return this[kSignal]
  }

  get body () {
    webidl.brandCheck(this, Request)

    return this[kState].body ? this[kState].body.stream : null
  }

  get bodyUsed () {
    webidl.brandCheck(this, Request)

    return !!this[kState].body && util.isDisturbed(this[kState].body.stream)
  }

  get duplex () {
    webidl.brandCheck(this, Request)

    return 'half'
  }

  // Returns a clone of request.
  clone () {
    webidl.brandCheck(this, Request)

    // 1. If this is unusable, then throw a TypeError.
    if (bodyUnusable(this)) {
      throw new TypeError('unusable')
    }

    // 2. Let clonedRequest be the result of cloning this’s request.
    const clonedRequest = cloneRequest(this[kState])

    // 3. Let clonedRequestObject be the result of creating a Request object,
    // given clonedRequest, this’s headers’s guard, and this’s relevant Realm.
    // 4. Make clonedRequestObject’s signal follow this’s signal.
    const ac = new AbortController()
    if (this.signal.aborted) {
      ac.abort(this.signal.reason)
    } else {
      let list = dependentControllerMap.get(this.signal)
      if (list === undefined) {
        list = new Set()
        dependentControllerMap.set(this.signal, list)
      }
      const acRef = new WeakRef(ac)
      list.add(acRef)
      util.addAbortListener(
        ac.signal,
        buildAbort(acRef)
      )
    }

    // 4. Return clonedRequestObject.
    return fromInnerRequest(clonedRequest, ac.signal, getHeadersGuard(this[kHeaders]))
  }

  [nodeUtil.inspect.custom] (depth, options) {
    if (options.depth === null) {
      options.depth = 2
    }

    options.colors ??= true

    const properties = {
      method: this.method,
      url: this.url,
      headers: this.headers,
      destination: this.destination,
      referrer: this.referrer,
      referrerPolicy: this.referrerPolicy,
      mode: this.mode,
      credentials: this.credentials,
      cache: this.cache,
      redirect: this.redirect,
      integrity: this.integrity,
      keepalive: this.keepalive,
      isReloadNavigation: this.isReloadNavigation,
      isHistoryNavigation: this.isHistoryNavigation,
      signal: this.signal
    }

    return `Request ${nodeUtil.formatWithOptions(options, properties)}`
  }
}

mixinBody(Request)

// https://fetch.spec.whatwg.org/#requests
function makeRequest (init) {
  return {
    method: init.method ?? 'GET',
    localURLsOnly: init.localURLsOnly ?? false,
    unsafeRequest: init.unsafeRequest ?? false,
    body: init.body ?? null,
    client: init.client ?? null,
    reservedClient: init.reservedClient ?? null,
    replacesClientId: init.replacesClientId ?? '',
    window: init.window ?? 'client',
    keepalive: init.keepalive ?? false,
    serviceWorkers: init.serviceWorkers ?? 'all',
    initiator: init.initiator ?? '',
    destination: init.destination ?? '',
    priority: init.priority ?? null,
    origin: init.origin ?? 'client',
    policyContainer: init.policyContainer ?? 'client',
    referrer: init.referrer ?? 'client',
    referrerPolicy: init.referrerPolicy ?? '',
    mode: init.mode ?? 'no-cors',
    useCORSPreflightFlag: init.useCORSPreflightFlag ?? false,
    credentials: init.credentials ?? 'same-origin',
    useCredentials: init.useCredentials ?? false,
    cache: init.cache ?? 'default',
    redirect: init.redirect ?? 'follow',
    integrity: init.integrity ?? '',
    cryptoGraphicsNonceMetadata: init.cryptoGraphicsNonceMetadata ?? '',
    parserMetadata: init.parserMetadata ?? '',
    reloadNavigation: init.reloadNavigation ?? false,
    historyNavigation: init.historyNavigation ?? false,
    userActivation: init.userActivation ?? false,
    taintedOrigin: init.taintedOrigin ?? false,
    redirectCount: init.redirectCount ?? 0,
    responseTainting: init.responseTainting ?? 'basic',
    preventNoCacheCacheControlHeaderModification: init.preventNoCacheCacheControlHeaderModification ?? false,
    done: init.done ?? false,
    timingAllowFailed: init.timingAllowFailed ?? false,
    urlList: init.urlList,
    url: init.urlList[0],
    headersList: init.headersList
      ? new HeadersList(init.headersList)
      : new HeadersList()
  }
}

// https://fetch.spec.whatwg.org/#concept-request-clone
function cloneRequest (request) {
  // To clone a request request, run these steps:

  // 1. Let newRequest be a copy of request, except for its body.
  const newRequest = makeRequest({ ...request, body: null })

  // 2. If request’s body is non-null, set newRequest’s body to the
  // result of cloning request’s body.
  if (request.body != null) {
    newRequest.body = cloneBody(newRequest, request.body)
  }

  // 3. Return newRequest.
  return newRequest
}

/**
 * @see https://fetch.spec.whatwg.org/#request-create
 * @param {any} innerRequest
 * @param {AbortSignal} signal
 * @param {'request' | 'immutable' | 'request-no-cors' | 'response' | 'none'} guard
 * @returns {Request}
 */
function fromInnerRequest (innerRequest, signal, guard) {
  const request = new Request(kConstruct)
  request[kState] = innerRequest
  request[kSignal] = signal
  request[kHeaders] = new Headers(kConstruct)
  setHeadersList(request[kHeaders], innerRequest.headersList)
  setHeadersGuard(request[kHeaders], guard)
  return request
}

Object.defineProperties(Request.prototype, {
  method: kEnumerableProperty,
  url: kEnumerableProperty,
  headers: kEnumerableProperty,
  redirect: kEnumerableProperty,
  clone: kEnumerableProperty,
  signal: kEnumerableProperty,
  duplex: kEnumerableProperty,
  destination: kEnumerableProperty,
  body: kEnumerableProperty,
  bodyUsed: kEnumerableProperty,
  isHistoryNavigation: kEnumerableProperty,
  isReloadNavigation: kEnumerableProperty,
  keepalive: kEnumerableProperty,
  integrity: kEnumerableProperty,
  cache: kEnumerableProperty,
  credentials: kEnumerableProperty,
  attribute: kEnumerableProperty,
  referrerPolicy: kEnumerableProperty,
  referrer: kEnumerableProperty,
  mode: kEnumerableProperty,
  [Symbol.toStringTag]: {
    value: 'Request',
    configurable: true
  }
})

webidl.converters.Request = webidl.interfaceConverter(
  Request
)

// https://fetch.spec.whatwg.org/#requestinfo
webidl.converters.RequestInfo = function (V, prefix, argument) {
  if (typeof V === 'string') {
    return webidl.converters.USVString(V, prefix, argument)
  }

  if (V instanceof Request) {
    return webidl.converters.Request(V, prefix, argument)
  }

  return webidl.converters.USVString(V, prefix, argument)
}

webidl.converters.AbortSignal = webidl.interfaceConverter(
  AbortSignal
)

// https://fetch.spec.whatwg.org/#requestinit
webidl.converters.RequestInit = webidl.dictionaryConverter([
  {
    key: 'method',
    converter: webidl.converters.ByteString
  },
  {
    key: 'headers',
    converter: webidl.converters.HeadersInit
  },
  {
    key: 'body',
    converter: webidl.nullableConverter(
      webidl.converters.BodyInit
    )
  },
  {
    key: 'referrer',
    converter: webidl.converters.USVString
  },
  {
    key: 'referrerPolicy',
    converter: webidl.converters.DOMString,
    // https://w3c.github.io/webappsec-referrer-policy/#referrer-policy
    allowedValues: referrerPolicy
  },
  {
    key: 'mode',
    converter: webidl.converters.DOMString,
    // https://fetch.spec.whatwg.org/#concept-request-mode
    allowedValues: requestMode
  },
  {
    key: 'credentials',
    converter: webidl.converters.DOMString,
    // https://fetch.spec.whatwg.org/#requestcredentials
    allowedValues: requestCredentials
  },
  {
    key: 'cache',
    converter: webidl.converters.DOMString,
    // https://fetch.spec.whatwg.org/#requestcache
    allowedValues: requestCache
  },
  {
    key: 'redirect',
    converter: webidl.converters.DOMString,
    // https://fetch.spec.whatwg.org/#requestredirect
    allowedValues: requestRedirect
  },
  {
    key: 'integrity',
    converter: webidl.converters.DOMString
  },
  {
    key: 'keepalive',
    converter: webidl.converters.boolean
  },
  {
    key: 'signal',
    converter: webidl.nullableConverter(
      (signal) => webidl.converters.AbortSignal(
        signal,
        'RequestInit',
        'signal',
        { strict: false }
      )
    )
  },
  {
    key: 'window',
    converter: webidl.converters.any
  },
  {
    key: 'duplex',
    converter: webidl.converters.DOMString,
    allowedValues: requestDuplex
  },
  {
    key: 'dispatcher', // undici specific option
    converter: webidl.converters.any
  }
])

module.exports = { Request, makeRequest, fromInnerRequest, cloneRequest }


/***/ }),

/***/ 9051:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { Headers, HeadersList, fill, getHeadersGuard, setHeadersGuard, setHeadersList } = __nccwpck_require__(660)
const { extractBody, cloneBody, mixinBody, hasFinalizationRegistry, streamRegistry, bodyUnusable } = __nccwpck_require__(4492)
const util = __nccwpck_require__(3440)
const nodeUtil = __nccwpck_require__(7975)
const { kEnumerableProperty } = util
const {
  isValidReasonPhrase,
  isCancelled,
  isAborted,
  isBlobLike,
  serializeJavascriptValueToJSONString,
  isErrorLike,
  isomorphicEncode,
  environmentSettingsObject: relevantRealm
} = __nccwpck_require__(3168)
const {
  redirectStatusSet,
  nullBodyStatus
} = __nccwpck_require__(4495)
const { kState, kHeaders } = __nccwpck_require__(3627)
const { webidl } = __nccwpck_require__(5893)
const { FormData } = __nccwpck_require__(5910)
const { URLSerializer } = __nccwpck_require__(1900)
const { kConstruct } = __nccwpck_require__(6443)
const assert = __nccwpck_require__(4589)
const { types } = __nccwpck_require__(7975)

const textEncoder = new TextEncoder('utf-8')

// https://fetch.spec.whatwg.org/#response-class
class Response {
  // Creates network error Response.
  static error () {
    // The static error() method steps are to return the result of creating a
    // Response object, given a new network error, "immutable", and this’s
    // relevant Realm.
    const responseObject = fromInnerResponse(makeNetworkError(), 'immutable')

    return responseObject
  }

  // https://fetch.spec.whatwg.org/#dom-response-json
  static json (data, init = {}) {
    webidl.argumentLengthCheck(arguments, 1, 'Response.json')

    if (init !== null) {
      init = webidl.converters.ResponseInit(init)
    }

    // 1. Let bytes the result of running serialize a JavaScript value to JSON bytes on data.
    const bytes = textEncoder.encode(
      serializeJavascriptValueToJSONString(data)
    )

    // 2. Let body be the result of extracting bytes.
    const body = extractBody(bytes)

    // 3. Let responseObject be the result of creating a Response object, given a new response,
    //    "response", and this’s relevant Realm.
    const responseObject = fromInnerResponse(makeResponse({}), 'response')

    // 4. Perform initialize a response given responseObject, init, and (body, "application/json").
    initializeResponse(responseObject, init, { body: body[0], type: 'application/json' })

    // 5. Return responseObject.
    return responseObject
  }

  // Creates a redirect Response that redirects to url with status status.
  static redirect (url, status = 302) {
    webidl.argumentLengthCheck(arguments, 1, 'Response.redirect')

    url = webidl.converters.USVString(url)
    status = webidl.converters['unsigned short'](status)

    // 1. Let parsedURL be the result of parsing url with current settings
    // object’s API base URL.
    // 2. If parsedURL is failure, then throw a TypeError.
    // TODO: base-URL?
    let parsedURL
    try {
      parsedURL = new URL(url, relevantRealm.settingsObject.baseUrl)
    } catch (err) {
      throw new TypeError(`Failed to parse URL from ${url}`, { cause: err })
    }

    // 3. If status is not a redirect status, then throw a RangeError.
    if (!redirectStatusSet.has(status)) {
      throw new RangeError(`Invalid status code ${status}`)
    }

    // 4. Let responseObject be the result of creating a Response object,
    // given a new response, "immutable", and this’s relevant Realm.
    const responseObject = fromInnerResponse(makeResponse({}), 'immutable')

    // 5. Set responseObject’s response’s status to status.
    responseObject[kState].status = status

    // 6. Let value be parsedURL, serialized and isomorphic encoded.
    const value = isomorphicEncode(URLSerializer(parsedURL))

    // 7. Append `Location`/value to responseObject’s response’s header list.
    responseObject[kState].headersList.append('location', value, true)

    // 8. Return responseObject.
    return responseObject
  }

  // https://fetch.spec.whatwg.org/#dom-response
  constructor (body = null, init = {}) {
    webidl.util.markAsUncloneable(this)
    if (body === kConstruct) {
      return
    }

    if (body !== null) {
      body = webidl.converters.BodyInit(body)
    }

    init = webidl.converters.ResponseInit(init)

    // 1. Set this’s response to a new response.
    this[kState] = makeResponse({})

    // 2. Set this’s headers to a new Headers object with this’s relevant
    // Realm, whose header list is this’s response’s header list and guard
    // is "response".
    this[kHeaders] = new Headers(kConstruct)
    setHeadersGuard(this[kHeaders], 'response')
    setHeadersList(this[kHeaders], this[kState].headersList)

    // 3. Let bodyWithType be null.
    let bodyWithType = null

    // 4. If body is non-null, then set bodyWithType to the result of extracting body.
    if (body != null) {
      const [extractedBody, type] = extractBody(body)
      bodyWithType = { body: extractedBody, type }
    }

    // 5. Perform initialize a response given this, init, and bodyWithType.
    initializeResponse(this, init, bodyWithType)
  }

  // Returns response’s type, e.g., "cors".
  get type () {
    webidl.brandCheck(this, Response)

    // The type getter steps are to return this’s response’s type.
    return this[kState].type
  }

  // Returns response’s URL, if it has one; otherwise the empty string.
  get url () {
    webidl.brandCheck(this, Response)

    const urlList = this[kState].urlList

    // The url getter steps are to return the empty string if this’s
    // response’s URL is null; otherwise this’s response’s URL,
    // serialized with exclude fragment set to true.
    const url = urlList[urlList.length - 1] ?? null

    if (url === null) {
      return ''
    }

    return URLSerializer(url, true)
  }

  // Returns whether response was obtained through a redirect.
  get redirected () {
    webidl.brandCheck(this, Response)

    // The redirected getter steps are to return true if this’s response’s URL
    // list has more than one item; otherwise false.
    return this[kState].urlList.length > 1
  }

  // Returns response’s status.
  get status () {
    webidl.brandCheck(this, Response)

    // The status getter steps are to return this’s response’s status.
    return this[kState].status
  }

  // Returns whether response’s status is an ok status.
  get ok () {
    webidl.brandCheck(this, Response)

    // The ok getter steps are to return true if this’s response’s status is an
    // ok status; otherwise false.
    return this[kState].status >= 200 && this[kState].status <= 299
  }

  // Returns response’s status message.
  get statusText () {
    webidl.brandCheck(this, Response)

    // The statusText getter steps are to return this’s response’s status
    // message.
    return this[kState].statusText
  }

  // Returns response’s headers as Headers.
  get headers () {
    webidl.brandCheck(this, Response)

    // The headers getter steps are to return this’s headers.
    return this[kHeaders]
  }

  get body () {
    webidl.brandCheck(this, Response)

    return this[kState].body ? this[kState].body.stream : null
  }

  get bodyUsed () {
    webidl.brandCheck(this, Response)

    return !!this[kState].body && util.isDisturbed(this[kState].body.stream)
  }

  // Returns a clone of response.
  clone () {
    webidl.brandCheck(this, Response)

    // 1. If this is unusable, then throw a TypeError.
    if (bodyUnusable(this)) {
      throw webidl.errors.exception({
        header: 'Response.clone',
        message: 'Body has already been consumed.'
      })
    }

    // 2. Let clonedResponse be the result of cloning this’s response.
    const clonedResponse = cloneResponse(this[kState])

    // Note: To re-register because of a new stream.
    if (hasFinalizationRegistry && this[kState].body?.stream) {
      streamRegistry.register(this, new WeakRef(this[kState].body.stream))
    }

    // 3. Return the result of creating a Response object, given
    // clonedResponse, this’s headers’s guard, and this’s relevant Realm.
    return fromInnerResponse(clonedResponse, getHeadersGuard(this[kHeaders]))
  }

  [nodeUtil.inspect.custom] (depth, options) {
    if (options.depth === null) {
      options.depth = 2
    }

    options.colors ??= true

    const properties = {
      status: this.status,
      statusText: this.statusText,
      headers: this.headers,
      body: this.body,
      bodyUsed: this.bodyUsed,
      ok: this.ok,
      redirected: this.redirected,
      type: this.type,
      url: this.url
    }

    return `Response ${nodeUtil.formatWithOptions(options, properties)}`
  }
}

mixinBody(Response)

Object.defineProperties(Response.prototype, {
  type: kEnumerableProperty,
  url: kEnumerableProperty,
  status: kEnumerableProperty,
  ok: kEnumerableProperty,
  redirected: kEnumerableProperty,
  statusText: kEnumerableProperty,
  headers: kEnumerableProperty,
  clone: kEnumerableProperty,
  body: kEnumerableProperty,
  bodyUsed: kEnumerableProperty,
  [Symbol.toStringTag]: {
    value: 'Response',
    configurable: true
  }
})

Object.defineProperties(Response, {
  json: kEnumerableProperty,
  redirect: kEnumerableProperty,
  error: kEnumerableProperty
})

// https://fetch.spec.whatwg.org/#concept-response-clone
function cloneResponse (response) {
  // To clone a response response, run these steps:

  // 1. If response is a filtered response, then return a new identical
  // filtered response whose internal response is a clone of response’s
  // internal response.
  if (response.internalResponse) {
    return filterResponse(
      cloneResponse(response.internalResponse),
      response.type
    )
  }

  // 2. Let newResponse be a copy of response, except for its body.
  const newResponse = makeResponse({ ...response, body: null })

  // 3. If response’s body is non-null, then set newResponse’s body to the
  // result of cloning response’s body.
  if (response.body != null) {
    newResponse.body = cloneBody(newResponse, response.body)
  }

  // 4. Return newResponse.
  return newResponse
}

function makeResponse (init) {
  return {
    aborted: false,
    rangeRequested: false,
    timingAllowPassed: false,
    requestIncludesCredentials: false,
    type: 'default',
    status: 200,
    timingInfo: null,
    cacheState: '',
    statusText: '',
    ...init,
    headersList: init?.headersList
      ? new HeadersList(init?.headersList)
      : new HeadersList(),
    urlList: init?.urlList ? [...init.urlList] : []
  }
}

function makeNetworkError (reason) {
  const isError = isErrorLike(reason)
  return makeResponse({
    type: 'error',
    status: 0,
    error: isError
      ? reason
      : new Error(reason ? String(reason) : reason),
    aborted: reason && reason.name === 'AbortError'
  })
}

// @see https://fetch.spec.whatwg.org/#concept-network-error
function isNetworkError (response) {
  return (
    // A network error is a response whose type is "error",
    response.type === 'error' &&
    // status is 0
    response.status === 0
  )
}

function makeFilteredResponse (response, state) {
  state = {
    internalResponse: response,
    ...state
  }

  return new Proxy(response, {
    get (target, p) {
      return p in state ? state[p] : target[p]
    },
    set (target, p, value) {
      assert(!(p in state))
      target[p] = value
      return true
    }
  })
}

// https://fetch.spec.whatwg.org/#concept-filtered-response
function filterResponse (response, type) {
  // Set response to the following filtered response with response as its
  // internal response, depending on request’s response tainting:
  if (type === 'basic') {
    // A basic filtered response is a filtered response whose type is "basic"
    // and header list excludes any headers in internal response’s header list
    // whose name is a forbidden response-header name.

    // Note: undici does not implement forbidden response-header names
    return makeFilteredResponse(response, {
      type: 'basic',
      headersList: response.headersList
    })
  } else if (type === 'cors') {
    // A CORS filtered response is a filtered response whose type is "cors"
    // and header list excludes any headers in internal response’s header
    // list whose name is not a CORS-safelisted response-header name, given
    // internal response’s CORS-exposed header-name list.

    // Note: undici does not implement CORS-safelisted response-header names
    return makeFilteredResponse(response, {
      type: 'cors',
      headersList: response.headersList
    })
  } else if (type === 'opaque') {
    // An opaque filtered response is a filtered response whose type is
    // "opaque", URL list is the empty list, status is 0, status message
    // is the empty byte sequence, header list is empty, and body is null.

    return makeFilteredResponse(response, {
      type: 'opaque',
      urlList: Object.freeze([]),
      status: 0,
      statusText: '',
      body: null
    })
  } else if (type === 'opaqueredirect') {
    // An opaque-redirect filtered response is a filtered response whose type
    // is "opaqueredirect", status is 0, status message is the empty byte
    // sequence, header list is empty, and body is null.

    return makeFilteredResponse(response, {
      type: 'opaqueredirect',
      status: 0,
      statusText: '',
      headersList: [],
      body: null
    })
  } else {
    assert(false)
  }
}

// https://fetch.spec.whatwg.org/#appropriate-network-error
function makeAppropriateNetworkError (fetchParams, err = null) {
  // 1. Assert: fetchParams is canceled.
  assert(isCancelled(fetchParams))

  // 2. Return an aborted network error if fetchParams is aborted;
  // otherwise return a network error.
  return isAborted(fetchParams)
    ? makeNetworkError(Object.assign(new DOMException('The operation was aborted.', 'AbortError'), { cause: err }))
    : makeNetworkError(Object.assign(new DOMException('Request was cancelled.'), { cause: err }))
}

// https://whatpr.org/fetch/1392.html#initialize-a-response
function initializeResponse (response, init, body) {
  // 1. If init["status"] is not in the range 200 to 599, inclusive, then
  //    throw a RangeError.
  if (init.status !== null && (init.status < 200 || init.status > 599)) {
    throw new RangeError('init["status"] must be in the range of 200 to 599, inclusive.')
  }

  // 2. If init["statusText"] does not match the reason-phrase token production,
  //    then throw a TypeError.
  if ('statusText' in init && init.statusText != null) {
    // See, https://datatracker.ietf.org/doc/html/rfc7230#section-3.1.2:
    //   reason-phrase  = *( HTAB / SP / VCHAR / obs-text )
    if (!isValidReasonPhrase(String(init.statusText))) {
      throw new TypeError('Invalid statusText')
    }
  }

  // 3. Set response’s response’s status to init["status"].
  if ('status' in init && init.status != null) {
    response[kState].status = init.status
  }

  // 4. Set response’s response’s status message to init["statusText"].
  if ('statusText' in init && init.statusText != null) {
    response[kState].statusText = init.statusText
  }

  // 5. If init["headers"] exists, then fill response’s headers with init["headers"].
  if ('headers' in init && init.headers != null) {
    fill(response[kHeaders], init.headers)
  }

  // 6. If body was given, then:
  if (body) {
    // 1. If response's status is a null body status, then throw a TypeError.
    if (nullBodyStatus.includes(response.status)) {
      throw webidl.errors.exception({
        header: 'Response constructor',
        message: `Invalid response status code ${response.status}`
      })
    }

    // 2. Set response's body to body's body.
    response[kState].body = body.body

    // 3. If body's type is non-null and response's header list does not contain
    //    `Content-Type`, then append (`Content-Type`, body's type) to response's header list.
    if (body.type != null && !response[kState].headersList.contains('content-type', true)) {
      response[kState].headersList.append('content-type', body.type, true)
    }
  }
}

/**
 * @see https://fetch.spec.whatwg.org/#response-create
 * @param {any} innerResponse
 * @param {'request' | 'immutable' | 'request-no-cors' | 'response' | 'none'} guard
 * @returns {Response}
 */
function fromInnerResponse (innerResponse, guard) {
  const response = new Response(kConstruct)
  response[kState] = innerResponse
  response[kHeaders] = new Headers(kConstruct)
  setHeadersList(response[kHeaders], innerResponse.headersList)
  setHeadersGuard(response[kHeaders], guard)

  if (hasFinalizationRegistry && innerResponse.body?.stream) {
    // If the target (response) is reclaimed, the cleanup callback may be called at some point with
    // the held value provided for it (innerResponse.body.stream). The held value can be any value:
    // a primitive or an object, even undefined. If the held value is an object, the registry keeps
    // a strong reference to it (so it can pass it to the cleanup callback later). Reworded from
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/FinalizationRegistry
    streamRegistry.register(response, new WeakRef(innerResponse.body.stream))
  }

  return response
}

webidl.converters.ReadableStream = webidl.interfaceConverter(
  ReadableStream
)

webidl.converters.FormData = webidl.interfaceConverter(
  FormData
)

webidl.converters.URLSearchParams = webidl.interfaceConverter(
  URLSearchParams
)

// https://fetch.spec.whatwg.org/#typedefdef-xmlhttprequestbodyinit
webidl.converters.XMLHttpRequestBodyInit = function (V, prefix, name) {
  if (typeof V === 'string') {
    return webidl.converters.USVString(V, prefix, name)
  }

  if (isBlobLike(V)) {
    return webidl.converters.Blob(V, prefix, name, { strict: false })
  }

  if (ArrayBuffer.isView(V) || types.isArrayBuffer(V)) {
    return webidl.converters.BufferSource(V, prefix, name)
  }

  if (util.isFormDataLike(V)) {
    return webidl.converters.FormData(V, prefix, name, { strict: false })
  }

  if (V instanceof URLSearchParams) {
    return webidl.converters.URLSearchParams(V, prefix, name)
  }

  return webidl.converters.DOMString(V, prefix, name)
}

// https://fetch.spec.whatwg.org/#bodyinit
webidl.converters.BodyInit = function (V, prefix, argument) {
  if (V instanceof ReadableStream) {
    return webidl.converters.ReadableStream(V, prefix, argument)
  }

  // Note: the spec doesn't include async iterables,
  // this is an undici extension.
  if (V?.[Symbol.asyncIterator]) {
    return V
  }

  return webidl.converters.XMLHttpRequestBodyInit(V, prefix, argument)
}

webidl.converters.ResponseInit = webidl.dictionaryConverter([
  {
    key: 'status',
    converter: webidl.converters['unsigned short'],
    defaultValue: () => 200
  },
  {
    key: 'statusText',
    converter: webidl.converters.ByteString,
    defaultValue: () => ''
  },
  {
    key: 'headers',
    converter: webidl.converters.HeadersInit
  }
])

module.exports = {
  isNetworkError,
  makeNetworkError,
  makeResponse,
  makeAppropriateNetworkError,
  filterResponse,
  Response,
  cloneResponse,
  fromInnerResponse
}


/***/ }),

/***/ 3627:
/***/ ((module) => {



module.exports = {
  kUrl: Symbol('url'),
  kHeaders: Symbol('headers'),
  kSignal: Symbol('signal'),
  kState: Symbol('state'),
  kDispatcher: Symbol('dispatcher')
}


/***/ }),

/***/ 3168:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { Transform } = __nccwpck_require__(7075)
const zlib = __nccwpck_require__(8522)
const { redirectStatusSet, referrerPolicySet: referrerPolicyTokens, badPortsSet } = __nccwpck_require__(4495)
const { getGlobalOrigin } = __nccwpck_require__(1059)
const { collectASequenceOfCodePoints, collectAnHTTPQuotedString, removeChars, parseMIMEType } = __nccwpck_require__(1900)
const { performance } = __nccwpck_require__(643)
const { isBlobLike, ReadableStreamFrom, isValidHTTPToken, normalizedMethodRecordsBase } = __nccwpck_require__(3440)
const assert = __nccwpck_require__(4589)
const { isUint8Array } = __nccwpck_require__(3429)
const { webidl } = __nccwpck_require__(5893)

let supportedHashes = []

// https://nodejs.org/api/crypto.html#determining-if-crypto-support-is-unavailable
/** @type {import('crypto')} */
let crypto
try {
  crypto = __nccwpck_require__(7598)
  const possibleRelevantHashes = ['sha256', 'sha384', 'sha512']
  supportedHashes = crypto.getHashes().filter((hash) => possibleRelevantHashes.includes(hash))
/* c8 ignore next 3 */
} catch {

}

function responseURL (response) {
  // https://fetch.spec.whatwg.org/#responses
  // A response has an associated URL. It is a pointer to the last URL
  // in response’s URL list and null if response’s URL list is empty.
  const urlList = response.urlList
  const length = urlList.length
  return length === 0 ? null : urlList[length - 1].toString()
}

// https://fetch.spec.whatwg.org/#concept-response-location-url
function responseLocationURL (response, requestFragment) {
  // 1. If response’s status is not a redirect status, then return null.
  if (!redirectStatusSet.has(response.status)) {
    return null
  }

  // 2. Let location be the result of extracting header list values given
  // `Location` and response’s header list.
  let location = response.headersList.get('location', true)

  // 3. If location is a header value, then set location to the result of
  //    parsing location with response’s URL.
  if (location !== null && isValidHeaderValue(location)) {
    if (!isValidEncodedURL(location)) {
      // Some websites respond location header in UTF-8 form without encoding them as ASCII
      // and major browsers redirect them to correctly UTF-8 encoded addresses.
      // Here, we handle that behavior in the same way.
      location = normalizeBinaryStringToUtf8(location)
    }
    location = new URL(location, responseURL(response))
  }

  // 4. If location is a URL whose fragment is null, then set location’s
  // fragment to requestFragment.
  if (location && !location.hash) {
    location.hash = requestFragment
  }

  // 5. Return location.
  return location
}

/**
 * @see https://www.rfc-editor.org/rfc/rfc1738#section-2.2
 * @param {string} url
 * @returns {boolean}
 */
function isValidEncodedURL (url) {
  for (let i = 0; i < url.length; ++i) {
    const code = url.charCodeAt(i)

    if (
      code > 0x7E || // Non-US-ASCII + DEL
      code < 0x20 // Control characters NUL - US
    ) {
      return false
    }
  }
  return true
}

/**
 * If string contains non-ASCII characters, assumes it's UTF-8 encoded and decodes it.
 * Since UTF-8 is a superset of ASCII, this will work for ASCII strings as well.
 * @param {string} value
 * @returns {string}
 */
function normalizeBinaryStringToUtf8 (value) {
  return Buffer.from(value, 'binary').toString('utf8')
}

/** @returns {URL} */
function requestCurrentURL (request) {
  return request.urlList[request.urlList.length - 1]
}

function requestBadPort (request) {
  // 1. Let url be request’s current URL.
  const url = requestCurrentURL(request)

  // 2. If url’s scheme is an HTTP(S) scheme and url’s port is a bad port,
  // then return blocked.
  if (urlIsHttpHttpsScheme(url) && badPortsSet.has(url.port)) {
    return 'blocked'
  }

  // 3. Return allowed.
  return 'allowed'
}

function isErrorLike (object) {
  return object instanceof Error || (
    object?.constructor?.name === 'Error' ||
    object?.constructor?.name === 'DOMException'
  )
}

// Check whether |statusText| is a ByteString and
// matches the Reason-Phrase token production.
// RFC 2616: https://tools.ietf.org/html/rfc2616
// RFC 7230: https://tools.ietf.org/html/rfc7230
// "reason-phrase = *( HTAB / SP / VCHAR / obs-text )"
// https://github.com/chromium/chromium/blob/94.0.4604.1/third_party/blink/renderer/core/fetch/response.cc#L116
function isValidReasonPhrase (statusText) {
  for (let i = 0; i < statusText.length; ++i) {
    const c = statusText.charCodeAt(i)
    if (
      !(
        (
          c === 0x09 || // HTAB
          (c >= 0x20 && c <= 0x7e) || // SP / VCHAR
          (c >= 0x80 && c <= 0xff)
        ) // obs-text
      )
    ) {
      return false
    }
  }
  return true
}

/**
 * @see https://fetch.spec.whatwg.org/#header-name
 * @param {string} potentialValue
 */
const isValidHeaderName = isValidHTTPToken

/**
 * @see https://fetch.spec.whatwg.org/#header-value
 * @param {string} potentialValue
 */
function isValidHeaderValue (potentialValue) {
  // - Has no leading or trailing HTTP tab or space bytes.
  // - Contains no 0x00 (NUL) or HTTP newline bytes.
  return (
    potentialValue[0] === '\t' ||
    potentialValue[0] === ' ' ||
    potentialValue[potentialValue.length - 1] === '\t' ||
    potentialValue[potentialValue.length - 1] === ' ' ||
    potentialValue.includes('\n') ||
    potentialValue.includes('\r') ||
    potentialValue.includes('\0')
  ) === false
}

// https://w3c.github.io/webappsec-referrer-policy/#set-requests-referrer-policy-on-redirect
function setRequestReferrerPolicyOnRedirect (request, actualResponse) {
  //  Given a request request and a response actualResponse, this algorithm
  //  updates request’s referrer policy according to the Referrer-Policy
  //  header (if any) in actualResponse.

  // 1. Let policy be the result of executing § 8.1 Parse a referrer policy
  // from a Referrer-Policy header on actualResponse.

  // 8.1 Parse a referrer policy from a Referrer-Policy header
  // 1. Let policy-tokens be the result of extracting header list values given `Referrer-Policy` and response’s header list.
  const { headersList } = actualResponse
  // 2. Let policy be the empty string.
  // 3. For each token in policy-tokens, if token is a referrer policy and token is not the empty string, then set policy to token.
  // 4. Return policy.
  const policyHeader = (headersList.get('referrer-policy', true) ?? '').split(',')

  // Note: As the referrer-policy can contain multiple policies
  // separated by comma, we need to loop through all of them
  // and pick the first valid one.
  // Ref: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy#specify_a_fallback_policy
  let policy = ''
  if (policyHeader.length > 0) {
    // The right-most policy takes precedence.
    // The left-most policy is the fallback.
    for (let i = policyHeader.length; i !== 0; i--) {
      const token = policyHeader[i - 1].trim()
      if (referrerPolicyTokens.has(token)) {
        policy = token
        break
      }
    }
  }

  // 2. If policy is not the empty string, then set request’s referrer policy to policy.
  if (policy !== '') {
    request.referrerPolicy = policy
  }
}

// https://fetch.spec.whatwg.org/#cross-origin-resource-policy-check
function crossOriginResourcePolicyCheck () {
  // TODO
  return 'allowed'
}

// https://fetch.spec.whatwg.org/#concept-cors-check
function corsCheck () {
  // TODO
  return 'success'
}

// https://fetch.spec.whatwg.org/#concept-tao-check
function TAOCheck () {
  // TODO
  return 'success'
}

function appendFetchMetadata (httpRequest) {
  //  https://w3c.github.io/webappsec-fetch-metadata/#sec-fetch-dest-header
  //  TODO

  //  https://w3c.github.io/webappsec-fetch-metadata/#sec-fetch-mode-header

  //  1. Assert: r’s url is a potentially trustworthy URL.
  //  TODO

  //  2. Let header be a Structured Header whose value is a token.
  let header = null

  //  3. Set header’s value to r’s mode.
  header = httpRequest.mode

  //  4. Set a structured field value `Sec-Fetch-Mode`/header in r’s header list.
  httpRequest.headersList.set('sec-fetch-mode', header, true)

  //  https://w3c.github.io/webappsec-fetch-metadata/#sec-fetch-site-header
  //  TODO

  //  https://w3c.github.io/webappsec-fetch-metadata/#sec-fetch-user-header
  //  TODO
}

// https://fetch.spec.whatwg.org/#append-a-request-origin-header
function appendRequestOriginHeader (request) {
  // 1. Let serializedOrigin be the result of byte-serializing a request origin
  //    with request.
  // TODO: implement "byte-serializing a request origin"
  let serializedOrigin = request.origin

  // - "'client' is changed to an origin during fetching."
  //   This doesn't happen in undici (in most cases) because undici, by default,
  //   has no concept of origin.
  // - request.origin can also be set to request.client.origin (client being
  //   an environment settings object), which is undefined without using
  //   setGlobalOrigin.
  if (serializedOrigin === 'client' || serializedOrigin === undefined) {
    return
  }

  // 2. If request’s response tainting is "cors" or request’s mode is "websocket",
  //    then append (`Origin`, serializedOrigin) to request’s header list.
  // 3. Otherwise, if request’s method is neither `GET` nor `HEAD`, then:
  if (request.responseTainting === 'cors' || request.mode === 'websocket') {
    request.headersList.append('origin', serializedOrigin, true)
  } else if (request.method !== 'GET' && request.method !== 'HEAD') {
    // 1. Switch on request’s referrer policy:
    switch (request.referrerPolicy) {
      case 'no-referrer':
        // Set serializedOrigin to `null`.
        serializedOrigin = null
        break
      case 'no-referrer-when-downgrade':
      case 'strict-origin':
      case 'strict-origin-when-cross-origin':
        // If request’s origin is a tuple origin, its scheme is "https", and
        // request’s current URL’s scheme is not "https", then set
        // serializedOrigin to `null`.
        if (request.origin && urlHasHttpsScheme(request.origin) && !urlHasHttpsScheme(requestCurrentURL(request))) {
          serializedOrigin = null
        }
        break
      case 'same-origin':
        // If request’s origin is not same origin with request’s current URL’s
        // origin, then set serializedOrigin to `null`.
        if (!sameOrigin(request, requestCurrentURL(request))) {
          serializedOrigin = null
        }
        break
      default:
        // Do nothing.
    }

    // 2. Append (`Origin`, serializedOrigin) to request’s header list.
    request.headersList.append('origin', serializedOrigin, true)
  }
}

// https://w3c.github.io/hr-time/#dfn-coarsen-time
function coarsenTime (timestamp, crossOriginIsolatedCapability) {
  // TODO
  return timestamp
}

// https://fetch.spec.whatwg.org/#clamp-and-coarsen-connection-timing-info
function clampAndCoarsenConnectionTimingInfo (connectionTimingInfo, defaultStartTime, crossOriginIsolatedCapability) {
  if (!connectionTimingInfo?.startTime || connectionTimingInfo.startTime < defaultStartTime) {
    return {
      domainLookupStartTime: defaultStartTime,
      domainLookupEndTime: defaultStartTime,
      connectionStartTime: defaultStartTime,
      connectionEndTime: defaultStartTime,
      secureConnectionStartTime: defaultStartTime,
      ALPNNegotiatedProtocol: connectionTimingInfo?.ALPNNegotiatedProtocol
    }
  }

  return {
    domainLookupStartTime: coarsenTime(connectionTimingInfo.domainLookupStartTime, crossOriginIsolatedCapability),
    domainLookupEndTime: coarsenTime(connectionTimingInfo.domainLookupEndTime, crossOriginIsolatedCapability),
    connectionStartTime: coarsenTime(connectionTimingInfo.connectionStartTime, crossOriginIsolatedCapability),
    connectionEndTime: coarsenTime(connectionTimingInfo.connectionEndTime, crossOriginIsolatedCapability),
    secureConnectionStartTime: coarsenTime(connectionTimingInfo.secureConnectionStartTime, crossOriginIsolatedCapability),
    ALPNNegotiatedProtocol: connectionTimingInfo.ALPNNegotiatedProtocol
  }
}

// https://w3c.github.io/hr-time/#dfn-coarsened-shared-current-time
function coarsenedSharedCurrentTime (crossOriginIsolatedCapability) {
  return coarsenTime(performance.now(), crossOriginIsolatedCapability)
}

// https://fetch.spec.whatwg.org/#create-an-opaque-timing-info
function createOpaqueTimingInfo (timingInfo) {
  return {
    startTime: timingInfo.startTime ?? 0,
    redirectStartTime: 0,
    redirectEndTime: 0,
    postRedirectStartTime: timingInfo.startTime ?? 0,
    finalServiceWorkerStartTime: 0,
    finalNetworkResponseStartTime: 0,
    finalNetworkRequestStartTime: 0,
    endTime: 0,
    encodedBodySize: 0,
    decodedBodySize: 0,
    finalConnectionTimingInfo: null
  }
}

// https://html.spec.whatwg.org/multipage/origin.html#policy-container
function makePolicyContainer () {
  // Note: the fetch spec doesn't make use of embedder policy or CSP list
  return {
    referrerPolicy: 'strict-origin-when-cross-origin'
  }
}

// https://html.spec.whatwg.org/multipage/origin.html#clone-a-policy-container
function clonePolicyContainer (policyContainer) {
  return {
    referrerPolicy: policyContainer.referrerPolicy
  }
}

// https://w3c.github.io/webappsec-referrer-policy/#determine-requests-referrer
function determineRequestsReferrer (request) {
  // 1. Let policy be request's referrer policy.
  const policy = request.referrerPolicy

  // Note: policy cannot (shouldn't) be null or an empty string.
  assert(policy)

  // 2. Let environment be request’s client.

  let referrerSource = null

  // 3. Switch on request’s referrer:
  if (request.referrer === 'client') {
    // Note: node isn't a browser and doesn't implement document/iframes,
    // so we bypass this step and replace it with our own.

    const globalOrigin = getGlobalOrigin()

    if (!globalOrigin || globalOrigin.origin === 'null') {
      return 'no-referrer'
    }

    // note: we need to clone it as it's mutated
    referrerSource = new URL(globalOrigin)
  } else if (request.referrer instanceof URL) {
    // Let referrerSource be request’s referrer.
    referrerSource = request.referrer
  }

  // 4. Let request’s referrerURL be the result of stripping referrerSource for
  //    use as a referrer.
  let referrerURL = stripURLForReferrer(referrerSource)

  // 5. Let referrerOrigin be the result of stripping referrerSource for use as
  //    a referrer, with the origin-only flag set to true.
  const referrerOrigin = stripURLForReferrer(referrerSource, true)

  // 6. If the result of serializing referrerURL is a string whose length is
  //    greater than 4096, set referrerURL to referrerOrigin.
  if (referrerURL.toString().length > 4096) {
    referrerURL = referrerOrigin
  }

  const areSameOrigin = sameOrigin(request, referrerURL)
  const isNonPotentiallyTrustWorthy = isURLPotentiallyTrustworthy(referrerURL) &&
    !isURLPotentiallyTrustworthy(request.url)

  // 8. Execute the switch statements corresponding to the value of policy:
  switch (policy) {
    case 'origin': return referrerOrigin != null ? referrerOrigin : stripURLForReferrer(referrerSource, true)
    case 'unsafe-url': return referrerURL
    case 'same-origin':
      return areSameOrigin ? referrerOrigin : 'no-referrer'
    case 'origin-when-cross-origin':
      return areSameOrigin ? referrerURL : referrerOrigin
    case 'strict-origin-when-cross-origin': {
      const currentURL = requestCurrentURL(request)

      // 1. If the origin of referrerURL and the origin of request’s current
      //    URL are the same, then return referrerURL.
      if (sameOrigin(referrerURL, currentURL)) {
        return referrerURL
      }

      // 2. If referrerURL is a potentially trustworthy URL and request’s
      //    current URL is not a potentially trustworthy URL, then return no
      //    referrer.
      if (isURLPotentiallyTrustworthy(referrerURL) && !isURLPotentiallyTrustworthy(currentURL)) {
        return 'no-referrer'
      }

      // 3. Return referrerOrigin.
      return referrerOrigin
    }
    case 'strict-origin': // eslint-disable-line
      /**
         * 1. If referrerURL is a potentially trustworthy URL and
         * request’s current URL is not a potentially trustworthy URL,
         * then return no referrer.
         * 2. Return referrerOrigin
        */
    case 'no-referrer-when-downgrade': // eslint-disable-line
      /**
       * 1. If referrerURL is a potentially trustworthy URL and
       * request’s current URL is not a potentially trustworthy URL,
       * then return no referrer.
       * 2. Return referrerOrigin
      */

    default: // eslint-disable-line
      return isNonPotentiallyTrustWorthy ? 'no-referrer' : referrerOrigin
  }
}

/**
 * @see https://w3c.github.io/webappsec-referrer-policy/#strip-url
 * @param {URL} url
 * @param {boolean|undefined} originOnly
 */
function stripURLForReferrer (url, originOnly) {
  // 1. Assert: url is a URL.
  assert(url instanceof URL)

  url = new URL(url)

  // 2. If url’s scheme is a local scheme, then return no referrer.
  if (url.protocol === 'file:' || url.protocol === 'about:' || url.protocol === 'blank:') {
    return 'no-referrer'
  }

  // 3. Set url’s username to the empty string.
  url.username = ''

  // 4. Set url’s password to the empty string.
  url.password = ''

  // 5. Set url’s fragment to null.
  url.hash = ''

  // 6. If the origin-only flag is true, then:
  if (originOnly) {
    // 1. Set url’s path to « the empty string ».
    url.pathname = ''

    // 2. Set url’s query to null.
    url.search = ''
  }

  // 7. Return url.
  return url
}

function isURLPotentiallyTrustworthy (url) {
  if (!(url instanceof URL)) {
    return false
  }

  // If child of about, return true
  if (url.href === 'about:blank' || url.href === 'about:srcdoc') {
    return true
  }

  // If scheme is data, return true
  if (url.protocol === 'data:') return true

  // If file, return true
  if (url.protocol === 'file:') return true

  return isOriginPotentiallyTrustworthy(url.origin)

  function isOriginPotentiallyTrustworthy (origin) {
    // If origin is explicitly null, return false
    if (origin == null || origin === 'null') return false

    const originAsURL = new URL(origin)

    // If secure, return true
    if (originAsURL.protocol === 'https:' || originAsURL.protocol === 'wss:') {
      return true
    }

    // If localhost or variants, return true
    if (/^127(?:\.[0-9]+){0,2}\.[0-9]+$|^\[(?:0*:)*?:?0*1\]$/.test(originAsURL.hostname) ||
     (originAsURL.hostname === 'localhost' || originAsURL.hostname.includes('localhost.')) ||
     (originAsURL.hostname.endsWith('.localhost'))) {
      return true
    }

    // If any other, return false
    return false
  }
}

/**
 * @see https://w3c.github.io/webappsec-subresource-integrity/#does-response-match-metadatalist
 * @param {Uint8Array} bytes
 * @param {string} metadataList
 */
function bytesMatch (bytes, metadataList) {
  // If node is not built with OpenSSL support, we cannot check
  // a request's integrity, so allow it by default (the spec will
  // allow requests if an invalid hash is given, as precedence).
  /* istanbul ignore if: only if node is built with --without-ssl */
  if (crypto === undefined) {
    return true
  }

  // 1. Let parsedMetadata be the result of parsing metadataList.
  const parsedMetadata = parseMetadata(metadataList)

  // 2. If parsedMetadata is no metadata, return true.
  if (parsedMetadata === 'no metadata') {
    return true
  }

  // 3. If response is not eligible for integrity validation, return false.
  // TODO

  // 4. If parsedMetadata is the empty set, return true.
  if (parsedMetadata.length === 0) {
    return true
  }

  // 5. Let metadata be the result of getting the strongest
  //    metadata from parsedMetadata.
  const strongest = getStrongestMetadata(parsedMetadata)
  const metadata = filterMetadataListByAlgorithm(parsedMetadata, strongest)

  // 6. For each item in metadata:
  for (const item of metadata) {
    // 1. Let algorithm be the alg component of item.
    const algorithm = item.algo

    // 2. Let expectedValue be the val component of item.
    const expectedValue = item.hash

    // See https://github.com/web-platform-tests/wpt/commit/e4c5cc7a5e48093220528dfdd1c4012dc3837a0e
    // "be liberal with padding". This is annoying, and it's not even in the spec.

    // 3. Let actualValue be the result of applying algorithm to bytes.
    let actualValue = crypto.createHash(algorithm).update(bytes).digest('base64')

    if (actualValue[actualValue.length - 1] === '=') {
      if (actualValue[actualValue.length - 2] === '=') {
        actualValue = actualValue.slice(0, -2)
      } else {
        actualValue = actualValue.slice(0, -1)
      }
    }

    // 4. If actualValue is a case-sensitive match for expectedValue,
    //    return true.
    if (compareBase64Mixed(actualValue, expectedValue)) {
      return true
    }
  }

  // 7. Return false.
  return false
}

// https://w3c.github.io/webappsec-subresource-integrity/#grammardef-hash-with-options
// https://www.w3.org/TR/CSP2/#source-list-syntax
// https://www.rfc-editor.org/rfc/rfc5234#appendix-B.1
const parseHashWithOptions = /(?<algo>sha256|sha384|sha512)-((?<hash>[A-Za-z0-9+/]+|[A-Za-z0-9_-]+)={0,2}(?:\s|$)( +[!-~]*)?)?/i

/**
 * @see https://w3c.github.io/webappsec-subresource-integrity/#parse-metadata
 * @param {string} metadata
 */
function parseMetadata (metadata) {
  // 1. Let result be the empty set.
  /** @type {{ algo: string, hash: string }[]} */
  const result = []

  // 2. Let empty be equal to true.
  let empty = true

  // 3. For each token returned by splitting metadata on spaces:
  for (const token of metadata.split(' ')) {
    // 1. Set empty to false.
    empty = false

    // 2. Parse token as a hash-with-options.
    const parsedToken = parseHashWithOptions.exec(token)

    // 3. If token does not parse, continue to the next token.
    if (
      parsedToken === null ||
      parsedToken.groups === undefined ||
      parsedToken.groups.algo === undefined
    ) {
      // Note: Chromium blocks the request at this point, but Firefox
      // gives a warning that an invalid integrity was given. The
      // correct behavior is to ignore these, and subsequently not
      // check the integrity of the resource.
      continue
    }

    // 4. Let algorithm be the hash-algo component of token.
    const algorithm = parsedToken.groups.algo.toLowerCase()

    // 5. If algorithm is a hash function recognized by the user
    //    agent, add the parsed token to result.
    if (supportedHashes.includes(algorithm)) {
      result.push(parsedToken.groups)
    }
  }

  // 4. Return no metadata if empty is true, otherwise return result.
  if (empty === true) {
    return 'no metadata'
  }

  return result
}

/**
 * @param {{ algo: 'sha256' | 'sha384' | 'sha512' }[]} metadataList
 */
function getStrongestMetadata (metadataList) {
  // Let algorithm be the algo component of the first item in metadataList.
  // Can be sha256
  let algorithm = metadataList[0].algo
  // If the algorithm is sha512, then it is the strongest
  // and we can return immediately
  if (algorithm[3] === '5') {
    return algorithm
  }

  for (let i = 1; i < metadataList.length; ++i) {
    const metadata = metadataList[i]
    // If the algorithm is sha512, then it is the strongest
    // and we can break the loop immediately
    if (metadata.algo[3] === '5') {
      algorithm = 'sha512'
      break
    // If the algorithm is sha384, then a potential sha256 or sha384 is ignored
    } else if (algorithm[3] === '3') {
      continue
    // algorithm is sha256, check if algorithm is sha384 and if so, set it as
    // the strongest
    } else if (metadata.algo[3] === '3') {
      algorithm = 'sha384'
    }
  }
  return algorithm
}

function filterMetadataListByAlgorithm (metadataList, algorithm) {
  if (metadataList.length === 1) {
    return metadataList
  }

  let pos = 0
  for (let i = 0; i < metadataList.length; ++i) {
    if (metadataList[i].algo === algorithm) {
      metadataList[pos++] = metadataList[i]
    }
  }

  metadataList.length = pos

  return metadataList
}

/**
 * Compares two base64 strings, allowing for base64url
 * in the second string.
 *
* @param {string} actualValue always base64
 * @param {string} expectedValue base64 or base64url
 * @returns {boolean}
 */
function compareBase64Mixed (actualValue, expectedValue) {
  if (actualValue.length !== expectedValue.length) {
    return false
  }
  for (let i = 0; i < actualValue.length; ++i) {
    if (actualValue[i] !== expectedValue[i]) {
      if (
        (actualValue[i] === '+' && expectedValue[i] === '-') ||
        (actualValue[i] === '/' && expectedValue[i] === '_')
      ) {
        continue
      }
      return false
    }
  }

  return true
}

// https://w3c.github.io/webappsec-upgrade-insecure-requests/#upgrade-request
function tryUpgradeRequestToAPotentiallyTrustworthyURL (request) {
  // TODO
}

/**
 * @link {https://html.spec.whatwg.org/multipage/origin.html#same-origin}
 * @param {URL} A
 * @param {URL} B
 */
function sameOrigin (A, B) {
  // 1. If A and B are the same opaque origin, then return true.
  if (A.origin === B.origin && A.origin === 'null') {
    return true
  }

  // 2. If A and B are both tuple origins and their schemes,
  //    hosts, and port are identical, then return true.
  if (A.protocol === B.protocol && A.hostname === B.hostname && A.port === B.port) {
    return true
  }

  // 3. Return false.
  return false
}

function createDeferredPromise () {
  let res
  let rej
  const promise = new Promise((resolve, reject) => {
    res = resolve
    rej = reject
  })

  return { promise, resolve: res, reject: rej }
}

function isAborted (fetchParams) {
  return fetchParams.controller.state === 'aborted'
}

function isCancelled (fetchParams) {
  return fetchParams.controller.state === 'aborted' ||
    fetchParams.controller.state === 'terminated'
}

/**
 * @see https://fetch.spec.whatwg.org/#concept-method-normalize
 * @param {string} method
 */
function normalizeMethod (method) {
  return normalizedMethodRecordsBase[method.toLowerCase()] ?? method
}

// https://infra.spec.whatwg.org/#serialize-a-javascript-value-to-a-json-string
function serializeJavascriptValueToJSONString (value) {
  // 1. Let result be ? Call(%JSON.stringify%, undefined, « value »).
  const result = JSON.stringify(value)

  // 2. If result is undefined, then throw a TypeError.
  if (result === undefined) {
    throw new TypeError('Value is not JSON serializable')
  }

  // 3. Assert: result is a string.
  assert(typeof result === 'string')

  // 4. Return result.
  return result
}

// https://tc39.es/ecma262/#sec-%25iteratorprototype%25-object
const esIteratorPrototype = Object.getPrototypeOf(Object.getPrototypeOf([][Symbol.iterator]()))

/**
 * @see https://webidl.spec.whatwg.org/#dfn-iterator-prototype-object
 * @param {string} name name of the instance
 * @param {symbol} kInternalIterator
 * @param {string | number} [keyIndex]
 * @param {string | number} [valueIndex]
 */
function createIterator (name, kInternalIterator, keyIndex = 0, valueIndex = 1) {
  class FastIterableIterator {
    /** @type {any} */
    #target
    /** @type {'key' | 'value' | 'key+value'} */
    #kind
    /** @type {number} */
    #index

    /**
     * @see https://webidl.spec.whatwg.org/#dfn-default-iterator-object
     * @param {unknown} target
     * @param {'key' | 'value' | 'key+value'} kind
     */
    constructor (target, kind) {
      this.#target = target
      this.#kind = kind
      this.#index = 0
    }

    next () {
      // 1. Let interface be the interface for which the iterator prototype object exists.
      // 2. Let thisValue be the this value.
      // 3. Let object be ? ToObject(thisValue).
      // 4. If object is a platform object, then perform a security
      //    check, passing:
      // 5. If object is not a default iterator object for interface,
      //    then throw a TypeError.
      if (typeof this !== 'object' || this === null || !(#target in this)) {
        throw new TypeError(
          `'next' called on an object that does not implement interface ${name} Iterator.`
        )
      }

      // 6. Let index be object’s index.
      // 7. Let kind be object’s kind.
      // 8. Let values be object’s target's value pairs to iterate over.
      const index = this.#index
      const values = this.#target[kInternalIterator]

      // 9. Let len be the length of values.
      const len = values.length

      // 10. If index is greater than or equal to len, then return
      //     CreateIterResultObject(undefined, true).
      if (index >= len) {
        return {
          value: undefined,
          done: true
        }
      }

      // 11. Let pair be the entry in values at index index.
      const { [keyIndex]: key, [valueIndex]: value } = values[index]

      // 12. Set object’s index to index + 1.
      this.#index = index + 1

      // 13. Return the iterator result for pair and kind.

      // https://webidl.spec.whatwg.org/#iterator-result

      // 1. Let result be a value determined by the value of kind:
      let result
      switch (this.#kind) {
        case 'key':
          // 1. Let idlKey be pair’s key.
          // 2. Let key be the result of converting idlKey to an
          //    ECMAScript value.
          // 3. result is key.
          result = key
          break
        case 'value':
          // 1. Let idlValue be pair’s value.
          // 2. Let value be the result of converting idlValue to
          //    an ECMAScript value.
          // 3. result is value.
          result = value
          break
        case 'key+value':
          // 1. Let idlKey be pair’s key.
          // 2. Let idlValue be pair’s value.
          // 3. Let key be the result of converting idlKey to an
          //    ECMAScript value.
          // 4. Let value be the result of converting idlValue to
          //    an ECMAScript value.
          // 5. Let array be ! ArrayCreate(2).
          // 6. Call ! CreateDataProperty(array, "0", key).
          // 7. Call ! CreateDataProperty(array, "1", value).
          // 8. result is array.
          result = [key, value]
          break
      }

      // 2. Return CreateIterResultObject(result, false).
      return {
        value: result,
        done: false
      }
    }
  }

  // https://webidl.spec.whatwg.org/#dfn-iterator-prototype-object
  // @ts-ignore
  delete FastIterableIterator.prototype.constructor

  Object.setPrototypeOf(FastIterableIterator.prototype, esIteratorPrototype)

  Object.defineProperties(FastIterableIterator.prototype, {
    [Symbol.toStringTag]: {
      writable: false,
      enumerable: false,
      configurable: true,
      value: `${name} Iterator`
    },
    next: { writable: true, enumerable: true, configurable: true }
  })

  /**
   * @param {unknown} target
   * @param {'key' | 'value' | 'key+value'} kind
   * @returns {IterableIterator<any>}
   */
  return function (target, kind) {
    return new FastIterableIterator(target, kind)
  }
}

/**
 * @see https://webidl.spec.whatwg.org/#dfn-iterator-prototype-object
 * @param {string} name name of the instance
 * @param {any} object class
 * @param {symbol} kInternalIterator
 * @param {string | number} [keyIndex]
 * @param {string | number} [valueIndex]
 */
function iteratorMixin (name, object, kInternalIterator, keyIndex = 0, valueIndex = 1) {
  const makeIterator = createIterator(name, kInternalIterator, keyIndex, valueIndex)

  const properties = {
    keys: {
      writable: true,
      enumerable: true,
      configurable: true,
      value: function keys () {
        webidl.brandCheck(this, object)
        return makeIterator(this, 'key')
      }
    },
    values: {
      writable: true,
      enumerable: true,
      configurable: true,
      value: function values () {
        webidl.brandCheck(this, object)
        return makeIterator(this, 'value')
      }
    },
    entries: {
      writable: true,
      enumerable: true,
      configurable: true,
      value: function entries () {
        webidl.brandCheck(this, object)
        return makeIterator(this, 'key+value')
      }
    },
    forEach: {
      writable: true,
      enumerable: true,
      configurable: true,
      value: function forEach (callbackfn, thisArg = globalThis) {
        webidl.brandCheck(this, object)
        webidl.argumentLengthCheck(arguments, 1, `${name}.forEach`)
        if (typeof callbackfn !== 'function') {
          throw new TypeError(
            `Failed to execute 'forEach' on '${name}': parameter 1 is not of type 'Function'.`
          )
        }
        for (const { 0: key, 1: value } of makeIterator(this, 'key+value')) {
          callbackfn.call(thisArg, value, key, this)
        }
      }
    }
  }

  return Object.defineProperties(object.prototype, {
    ...properties,
    [Symbol.iterator]: {
      writable: true,
      enumerable: false,
      configurable: true,
      value: properties.entries.value
    }
  })
}

/**
 * @see https://fetch.spec.whatwg.org/#body-fully-read
 */
async function fullyReadBody (body, processBody, processBodyError) {
  // 1. If taskDestination is null, then set taskDestination to
  //    the result of starting a new parallel queue.

  // 2. Let successSteps given a byte sequence bytes be to queue a
  //    fetch task to run processBody given bytes, with taskDestination.
  const successSteps = processBody

  // 3. Let errorSteps be to queue a fetch task to run processBodyError,
  //    with taskDestination.
  const errorSteps = processBodyError

  // 4. Let reader be the result of getting a reader for body’s stream.
  //    If that threw an exception, then run errorSteps with that
  //    exception and return.
  let reader

  try {
    reader = body.stream.getReader()
  } catch (e) {
    errorSteps(e)
    return
  }

  // 5. Read all bytes from reader, given successSteps and errorSteps.
  try {
    successSteps(await readAllBytes(reader))
  } catch (e) {
    errorSteps(e)
  }
}

function isReadableStreamLike (stream) {
  return stream instanceof ReadableStream || (
    stream[Symbol.toStringTag] === 'ReadableStream' &&
    typeof stream.tee === 'function'
  )
}

/**
 * @param {ReadableStreamController<Uint8Array>} controller
 */
function readableStreamClose (controller) {
  try {
    controller.close()
    controller.byobRequest?.respond(0)
  } catch (err) {
    // TODO: add comment explaining why this error occurs.
    if (!err.message.includes('Controller is already closed') && !err.message.includes('ReadableStream is already closed')) {
      throw err
    }
  }
}

const invalidIsomorphicEncodeValueRegex = /[^\x00-\xFF]/ // eslint-disable-line

/**
 * @see https://infra.spec.whatwg.org/#isomorphic-encode
 * @param {string} input
 */
function isomorphicEncode (input) {
  // 1. Assert: input contains no code points greater than U+00FF.
  assert(!invalidIsomorphicEncodeValueRegex.test(input))

  // 2. Return a byte sequence whose length is equal to input’s code
  //    point length and whose bytes have the same values as the
  //    values of input’s code points, in the same order
  return input
}

/**
 * @see https://streams.spec.whatwg.org/#readablestreamdefaultreader-read-all-bytes
 * @see https://streams.spec.whatwg.org/#read-loop
 * @param {ReadableStreamDefaultReader} reader
 */
async function readAllBytes (reader) {
  const bytes = []
  let byteLength = 0

  while (true) {
    const { done, value: chunk } = await reader.read()

    if (done) {
      // 1. Call successSteps with bytes.
      return Buffer.concat(bytes, byteLength)
    }

    // 1. If chunk is not a Uint8Array object, call failureSteps
    //    with a TypeError and abort these steps.
    if (!isUint8Array(chunk)) {
      throw new TypeError('Received non-Uint8Array chunk')
    }

    // 2. Append the bytes represented by chunk to bytes.
    bytes.push(chunk)
    byteLength += chunk.length

    // 3. Read-loop given reader, bytes, successSteps, and failureSteps.
  }
}

/**
 * @see https://fetch.spec.whatwg.org/#is-local
 * @param {URL} url
 */
function urlIsLocal (url) {
  assert('protocol' in url) // ensure it's a url object

  const protocol = url.protocol

  return protocol === 'about:' || protocol === 'blob:' || protocol === 'data:'
}

/**
 * @param {string|URL} url
 * @returns {boolean}
 */
function urlHasHttpsScheme (url) {
  return (
    (
      typeof url === 'string' &&
      url[5] === ':' &&
      url[0] === 'h' &&
      url[1] === 't' &&
      url[2] === 't' &&
      url[3] === 'p' &&
      url[4] === 's'
    ) ||
    url.protocol === 'https:'
  )
}

/**
 * @see https://fetch.spec.whatwg.org/#http-scheme
 * @param {URL} url
 */
function urlIsHttpHttpsScheme (url) {
  assert('protocol' in url) // ensure it's a url object

  const protocol = url.protocol

  return protocol === 'http:' || protocol === 'https:'
}

/**
 * @see https://fetch.spec.whatwg.org/#simple-range-header-value
 * @param {string} value
 * @param {boolean} allowWhitespace
 */
function simpleRangeHeaderValue (value, allowWhitespace) {
  // 1. Let data be the isomorphic decoding of value.
  // Note: isomorphic decoding takes a sequence of bytes (ie. a Uint8Array) and turns it into a string,
  // nothing more. We obviously don't need to do that if value is a string already.
  const data = value

  // 2. If data does not start with "bytes", then return failure.
  if (!data.startsWith('bytes')) {
    return 'failure'
  }

  // 3. Let position be a position variable for data, initially pointing at the 5th code point of data.
  const position = { position: 5 }

  // 4. If allowWhitespace is true, collect a sequence of code points that are HTTP tab or space,
  //    from data given position.
  if (allowWhitespace) {
    collectASequenceOfCodePoints(
      (char) => char === '\t' || char === ' ',
      data,
      position
    )
  }

  // 5. If the code point at position within data is not U+003D (=), then return failure.
  if (data.charCodeAt(position.position) !== 0x3D) {
    return 'failure'
  }

  // 6. Advance position by 1.
  position.position++

  // 7. If allowWhitespace is true, collect a sequence of code points that are HTTP tab or space, from
  //    data given position.
  if (allowWhitespace) {
    collectASequenceOfCodePoints(
      (char) => char === '\t' || char === ' ',
      data,
      position
    )
  }

  // 8. Let rangeStart be the result of collecting a sequence of code points that are ASCII digits,
  //    from data given position.
  const rangeStart = collectASequenceOfCodePoints(
    (char) => {
      const code = char.charCodeAt(0)

      return code >= 0x30 && code <= 0x39
    },
    data,
    position
  )

  // 9. Let rangeStartValue be rangeStart, interpreted as decimal number, if rangeStart is not the
  //    empty string; otherwise null.
  const rangeStartValue = rangeStart.length ? Number(rangeStart) : null

  // 10. If allowWhitespace is true, collect a sequence of code points that are HTTP tab or space,
  //     from data given position.
  if (allowWhitespace) {
    collectASequenceOfCodePoints(
      (char) => char === '\t' || char === ' ',
      data,
      position
    )
  }

  // 11. If the code point at position within data is not U+002D (-), then return failure.
  if (data.charCodeAt(position.position) !== 0x2D) {
    return 'failure'
  }

  // 12. Advance position by 1.
  position.position++

  // 13. If allowWhitespace is true, collect a sequence of code points that are HTTP tab
  //     or space, from data given position.
  // Note from Khafra: its the same step as in #8 again lol
  if (allowWhitespace) {
    collectASequenceOfCodePoints(
      (char) => char === '\t' || char === ' ',
      data,
      position
    )
  }

  // 14. Let rangeEnd be the result of collecting a sequence of code points that are
  //     ASCII digits, from data given position.
  // Note from Khafra: you wouldn't guess it, but this is also the same step as #8
  const rangeEnd = collectASequenceOfCodePoints(
    (char) => {
      const code = char.charCodeAt(0)

      return code >= 0x30 && code <= 0x39
    },
    data,
    position
  )

  // 15. Let rangeEndValue be rangeEnd, interpreted as decimal number, if rangeEnd
  //     is not the empty string; otherwise null.
  // Note from Khafra: THE SAME STEP, AGAIN!!!
  // Note: why interpret as a decimal if we only collect ascii digits?
  const rangeEndValue = rangeEnd.length ? Number(rangeEnd) : null

  // 16. If position is not past the end of data, then return failure.
  if (position.position < data.length) {
    return 'failure'
  }

  // 17. If rangeEndValue and rangeStartValue are null, then return failure.
  if (rangeEndValue === null && rangeStartValue === null) {
    return 'failure'
  }

  // 18. If rangeStartValue and rangeEndValue are numbers, and rangeStartValue is
  //     greater than rangeEndValue, then return failure.
  // Note: ... when can they not be numbers?
  if (rangeStartValue > rangeEndValue) {
    return 'failure'
  }

  // 19. Return (rangeStartValue, rangeEndValue).
  return { rangeStartValue, rangeEndValue }
}

/**
 * @see https://fetch.spec.whatwg.org/#build-a-content-range
 * @param {number} rangeStart
 * @param {number} rangeEnd
 * @param {number} fullLength
 */
function buildContentRange (rangeStart, rangeEnd, fullLength) {
  // 1. Let contentRange be `bytes `.
  let contentRange = 'bytes '

  // 2. Append rangeStart, serialized and isomorphic encoded, to contentRange.
  contentRange += isomorphicEncode(`${rangeStart}`)

  // 3. Append 0x2D (-) to contentRange.
  contentRange += '-'

  // 4. Append rangeEnd, serialized and isomorphic encoded to contentRange.
  contentRange += isomorphicEncode(`${rangeEnd}`)

  // 5. Append 0x2F (/) to contentRange.
  contentRange += '/'

  // 6. Append fullLength, serialized and isomorphic encoded to contentRange.
  contentRange += isomorphicEncode(`${fullLength}`)

  // 7. Return contentRange.
  return contentRange
}

// A Stream, which pipes the response to zlib.createInflate() or
// zlib.createInflateRaw() depending on the first byte of the Buffer.
// If the lower byte of the first byte is 0x08, then the stream is
// interpreted as a zlib stream, otherwise it's interpreted as a
// raw deflate stream.
class InflateStream extends Transform {
  #zlibOptions

  /** @param {zlib.ZlibOptions} [zlibOptions] */
  constructor (zlibOptions) {
    super()
    this.#zlibOptions = zlibOptions
  }

  _transform (chunk, encoding, callback) {
    if (!this._inflateStream) {
      if (chunk.length === 0) {
        callback()
        return
      }
      this._inflateStream = (chunk[0] & 0x0F) === 0x08
        ? zlib.createInflate(this.#zlibOptions)
        : zlib.createInflateRaw(this.#zlibOptions)

      this._inflateStream.on('data', this.push.bind(this))
      this._inflateStream.on('end', () => this.push(null))
      this._inflateStream.on('error', (err) => this.destroy(err))
    }

    this._inflateStream.write(chunk, encoding, callback)
  }

  _final (callback) {
    if (this._inflateStream) {
      this._inflateStream.end()
      this._inflateStream = null
    }
    callback()
  }
}

/**
 * @param {zlib.ZlibOptions} [zlibOptions]
 * @returns {InflateStream}
 */
function createInflate (zlibOptions) {
  return new InflateStream(zlibOptions)
}

/**
 * @see https://fetch.spec.whatwg.org/#concept-header-extract-mime-type
 * @param {import('./headers').HeadersList} headers
 */
function extractMimeType (headers) {
  // 1. Let charset be null.
  let charset = null

  // 2. Let essence be null.
  let essence = null

  // 3. Let mimeType be null.
  let mimeType = null

  // 4. Let values be the result of getting, decoding, and splitting `Content-Type` from headers.
  const values = getDecodeSplit('content-type', headers)

  // 5. If values is null, then return failure.
  if (values === null) {
    return 'failure'
  }

  // 6. For each value of values:
  for (const value of values) {
    // 6.1. Let temporaryMimeType be the result of parsing value.
    const temporaryMimeType = parseMIMEType(value)

    // 6.2. If temporaryMimeType is failure or its essence is "*/*", then continue.
    if (temporaryMimeType === 'failure' || temporaryMimeType.essence === '*/*') {
      continue
    }

    // 6.3. Set mimeType to temporaryMimeType.
    mimeType = temporaryMimeType

    // 6.4. If mimeType’s essence is not essence, then:
    if (mimeType.essence !== essence) {
      // 6.4.1. Set charset to null.
      charset = null

      // 6.4.2. If mimeType’s parameters["charset"] exists, then set charset to
      //        mimeType’s parameters["charset"].
      if (mimeType.parameters.has('charset')) {
        charset = mimeType.parameters.get('charset')
      }

      // 6.4.3. Set essence to mimeType’s essence.
      essence = mimeType.essence
    } else if (!mimeType.parameters.has('charset') && charset !== null) {
      // 6.5. Otherwise, if mimeType’s parameters["charset"] does not exist, and
      //      charset is non-null, set mimeType’s parameters["charset"] to charset.
      mimeType.parameters.set('charset', charset)
    }
  }

  // 7. If mimeType is null, then return failure.
  if (mimeType == null) {
    return 'failure'
  }

  // 8. Return mimeType.
  return mimeType
}

/**
 * @see https://fetch.spec.whatwg.org/#header-value-get-decode-and-split
 * @param {string|null} value
 */
function gettingDecodingSplitting (value) {
  // 1. Let input be the result of isomorphic decoding value.
  const input = value

  // 2. Let position be a position variable for input, initially pointing at the start of input.
  const position = { position: 0 }

  // 3. Let values be a list of strings, initially empty.
  const values = []

  // 4. Let temporaryValue be the empty string.
  let temporaryValue = ''

  // 5. While position is not past the end of input:
  while (position.position < input.length) {
    // 5.1. Append the result of collecting a sequence of code points that are not U+0022 (")
    //      or U+002C (,) from input, given position, to temporaryValue.
    temporaryValue += collectASequenceOfCodePoints(
      (char) => char !== '"' && char !== ',',
      input,
      position
    )

    // 5.2. If position is not past the end of input, then:
    if (position.position < input.length) {
      // 5.2.1. If the code point at position within input is U+0022 ("), then:
      if (input.charCodeAt(position.position) === 0x22) {
        // 5.2.1.1. Append the result of collecting an HTTP quoted string from input, given position, to temporaryValue.
        temporaryValue += collectAnHTTPQuotedString(
          input,
          position
        )

        // 5.2.1.2. If position is not past the end of input, then continue.
        if (position.position < input.length) {
          continue
        }
      } else {
        // 5.2.2. Otherwise:

        // 5.2.2.1. Assert: the code point at position within input is U+002C (,).
        assert(input.charCodeAt(position.position) === 0x2C)

        // 5.2.2.2. Advance position by 1.
        position.position++
      }
    }

    // 5.3. Remove all HTTP tab or space from the start and end of temporaryValue.
    temporaryValue = removeChars(temporaryValue, true, true, (char) => char === 0x9 || char === 0x20)

    // 5.4. Append temporaryValue to values.
    values.push(temporaryValue)

    // 5.6. Set temporaryValue to the empty string.
    temporaryValue = ''
  }

  // 6. Return values.
  return values
}

/**
 * @see https://fetch.spec.whatwg.org/#concept-header-list-get-decode-split
 * @param {string} name lowercase header name
 * @param {import('./headers').HeadersList} list
 */
function getDecodeSplit (name, list) {
  // 1. Let value be the result of getting name from list.
  const value = list.get(name, true)

  // 2. If value is null, then return null.
  if (value === null) {
    return null
  }

  // 3. Return the result of getting, decoding, and splitting value.
  return gettingDecodingSplitting(value)
}

const textDecoder = new TextDecoder()

/**
 * @see https://encoding.spec.whatwg.org/#utf-8-decode
 * @param {Buffer} buffer
 */
function utf8DecodeBytes (buffer) {
  if (buffer.length === 0) {
    return ''
  }

  // 1. Let buffer be the result of peeking three bytes from
  //    ioQueue, converted to a byte sequence.

  // 2. If buffer is 0xEF 0xBB 0xBF, then read three
  //    bytes from ioQueue. (Do nothing with those bytes.)
  if (buffer[0] === 0xEF && buffer[1] === 0xBB && buffer[2] === 0xBF) {
    buffer = buffer.subarray(3)
  }

  // 3. Process a queue with an instance of UTF-8’s
  //    decoder, ioQueue, output, and "replacement".
  const output = textDecoder.decode(buffer)

  // 4. Return output.
  return output
}

class EnvironmentSettingsObjectBase {
  get baseUrl () {
    return getGlobalOrigin()
  }

  get origin () {
    return this.baseUrl?.origin
  }

  policyContainer = makePolicyContainer()
}

class EnvironmentSettingsObject {
  settingsObject = new EnvironmentSettingsObjectBase()
}

const environmentSettingsObject = new EnvironmentSettingsObject()

module.exports = {
  isAborted,
  isCancelled,
  isValidEncodedURL,
  createDeferredPromise,
  ReadableStreamFrom,
  tryUpgradeRequestToAPotentiallyTrustworthyURL,
  clampAndCoarsenConnectionTimingInfo,
  coarsenedSharedCurrentTime,
  determineRequestsReferrer,
  makePolicyContainer,
  clonePolicyContainer,
  appendFetchMetadata,
  appendRequestOriginHeader,
  TAOCheck,
  corsCheck,
  crossOriginResourcePolicyCheck,
  createOpaqueTimingInfo,
  setRequestReferrerPolicyOnRedirect,
  isValidHTTPToken,
  requestBadPort,
  requestCurrentURL,
  responseURL,
  responseLocationURL,
  isBlobLike,
  isURLPotentiallyTrustworthy,
  isValidReasonPhrase,
  sameOrigin,
  normalizeMethod,
  serializeJavascriptValueToJSONString,
  iteratorMixin,
  createIterator,
  isValidHeaderName,
  isValidHeaderValue,
  isErrorLike,
  fullyReadBody,
  bytesMatch,
  isReadableStreamLike,
  readableStreamClose,
  isomorphicEncode,
  urlIsLocal,
  urlHasHttpsScheme,
  urlIsHttpHttpsScheme,
  readAllBytes,
  simpleRangeHeaderValue,
  buildContentRange,
  parseMetadata,
  createInflate,
  extractMimeType,
  getDecodeSplit,
  utf8DecodeBytes,
  environmentSettingsObject
}


/***/ }),

/***/ 5893:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { types, inspect } = __nccwpck_require__(7975)
const { markAsUncloneable } = __nccwpck_require__(5919)
const { toUSVString } = __nccwpck_require__(3440)

/** @type {import('../../../types/webidl').Webidl} */
const webidl = {}
webidl.converters = {}
webidl.util = {}
webidl.errors = {}

webidl.errors.exception = function (message) {
  return new TypeError(`${message.header}: ${message.message}`)
}

webidl.errors.conversionFailed = function (context) {
  const plural = context.types.length === 1 ? '' : ' one of'
  const message =
    `${context.argument} could not be converted to` +
    `${plural}: ${context.types.join(', ')}.`

  return webidl.errors.exception({
    header: context.prefix,
    message
  })
}

webidl.errors.invalidArgument = function (context) {
  return webidl.errors.exception({
    header: context.prefix,
    message: `"${context.value}" is an invalid ${context.type}.`
  })
}

// https://webidl.spec.whatwg.org/#implements
webidl.brandCheck = function (V, I, opts) {
  if (opts?.strict !== false) {
    if (!(V instanceof I)) {
      const err = new TypeError('Illegal invocation')
      err.code = 'ERR_INVALID_THIS' // node compat.
      throw err
    }
  } else {
    if (V?.[Symbol.toStringTag] !== I.prototype[Symbol.toStringTag]) {
      const err = new TypeError('Illegal invocation')
      err.code = 'ERR_INVALID_THIS' // node compat.
      throw err
    }
  }
}

webidl.argumentLengthCheck = function ({ length }, min, ctx) {
  if (length < min) {
    throw webidl.errors.exception({
      message: `${min} argument${min !== 1 ? 's' : ''} required, ` +
               `but${length ? ' only' : ''} ${length} found.`,
      header: ctx
    })
  }
}

webidl.illegalConstructor = function () {
  throw webidl.errors.exception({
    header: 'TypeError',
    message: 'Illegal constructor'
  })
}

// https://tc39.es/ecma262/#sec-ecmascript-data-types-and-values
webidl.util.Type = function (V) {
  switch (typeof V) {
    case 'undefined': return 'Undefined'
    case 'boolean': return 'Boolean'
    case 'string': return 'String'
    case 'symbol': return 'Symbol'
    case 'number': return 'Number'
    case 'bigint': return 'BigInt'
    case 'function':
    case 'object': {
      if (V === null) {
        return 'Null'
      }

      return 'Object'
    }
  }
}

webidl.util.markAsUncloneable = markAsUncloneable || (() => {})
// https://webidl.spec.whatwg.org/#abstract-opdef-converttoint
webidl.util.ConvertToInt = function (V, bitLength, signedness, opts) {
  let upperBound
  let lowerBound

  // 1. If bitLength is 64, then:
  if (bitLength === 64) {
    // 1. Let upperBound be 2^53 − 1.
    upperBound = Math.pow(2, 53) - 1

    // 2. If signedness is "unsigned", then let lowerBound be 0.
    if (signedness === 'unsigned') {
      lowerBound = 0
    } else {
      // 3. Otherwise let lowerBound be −2^53 + 1.
      lowerBound = Math.pow(-2, 53) + 1
    }
  } else if (signedness === 'unsigned') {
    // 2. Otherwise, if signedness is "unsigned", then:

    // 1. Let lowerBound be 0.
    lowerBound = 0

    // 2. Let upperBound be 2^bitLength − 1.
    upperBound = Math.pow(2, bitLength) - 1
  } else {
    // 3. Otherwise:

    // 1. Let lowerBound be -2^bitLength − 1.
    lowerBound = Math.pow(-2, bitLength) - 1

    // 2. Let upperBound be 2^bitLength − 1 − 1.
    upperBound = Math.pow(2, bitLength - 1) - 1
  }

  // 4. Let x be ? ToNumber(V).
  let x = Number(V)

  // 5. If x is −0, then set x to +0.
  if (x === 0) {
    x = 0
  }

  // 6. If the conversion is to an IDL type associated
  //    with the [EnforceRange] extended attribute, then:
  if (opts?.enforceRange === true) {
    // 1. If x is NaN, +∞, or −∞, then throw a TypeError.
    if (
      Number.isNaN(x) ||
      x === Number.POSITIVE_INFINITY ||
      x === Number.NEGATIVE_INFINITY
    ) {
      throw webidl.errors.exception({
        header: 'Integer conversion',
        message: `Could not convert ${webidl.util.Stringify(V)} to an integer.`
      })
    }

    // 2. Set x to IntegerPart(x).
    x = webidl.util.IntegerPart(x)

    // 3. If x < lowerBound or x > upperBound, then
    //    throw a TypeError.
    if (x < lowerBound || x > upperBound) {
      throw webidl.errors.exception({
        header: 'Integer conversion',
        message: `Value must be between ${lowerBound}-${upperBound}, got ${x}.`
      })
    }

    // 4. Return x.
    return x
  }

  // 7. If x is not NaN and the conversion is to an IDL
  //    type associated with the [Clamp] extended
  //    attribute, then:
  if (!Number.isNaN(x) && opts?.clamp === true) {
    // 1. Set x to min(max(x, lowerBound), upperBound).
    x = Math.min(Math.max(x, lowerBound), upperBound)

    // 2. Round x to the nearest integer, choosing the
    //    even integer if it lies halfway between two,
    //    and choosing +0 rather than −0.
    if (Math.floor(x) % 2 === 0) {
      x = Math.floor(x)
    } else {
      x = Math.ceil(x)
    }

    // 3. Return x.
    return x
  }

  // 8. If x is NaN, +0, +∞, or −∞, then return +0.
  if (
    Number.isNaN(x) ||
    (x === 0 && Object.is(0, x)) ||
    x === Number.POSITIVE_INFINITY ||
    x === Number.NEGATIVE_INFINITY
  ) {
    return 0
  }

  // 9. Set x to IntegerPart(x).
  x = webidl.util.IntegerPart(x)

  // 10. Set x to x modulo 2^bitLength.
  x = x % Math.pow(2, bitLength)

  // 11. If signedness is "signed" and x ≥ 2^bitLength − 1,
  //    then return x − 2^bitLength.
  if (signedness === 'signed' && x >= Math.pow(2, bitLength) - 1) {
    return x - Math.pow(2, bitLength)
  }

  // 12. Otherwise, return x.
  return x
}

// https://webidl.spec.whatwg.org/#abstract-opdef-integerpart
webidl.util.IntegerPart = function (n) {
  // 1. Let r be floor(abs(n)).
  const r = Math.floor(Math.abs(n))

  // 2. If n < 0, then return -1 × r.
  if (n < 0) {
    return -1 * r
  }

  // 3. Otherwise, return r.
  return r
}

webidl.util.Stringify = function (V) {
  const type = webidl.util.Type(V)

  switch (type) {
    case 'Symbol':
      return `Symbol(${V.description})`
    case 'Object':
      return inspect(V)
    case 'String':
      return `"${V}"`
    default:
      return `${V}`
  }
}

// https://webidl.spec.whatwg.org/#es-sequence
webidl.sequenceConverter = function (converter) {
  return (V, prefix, argument, Iterable) => {
    // 1. If Type(V) is not Object, throw a TypeError.
    if (webidl.util.Type(V) !== 'Object') {
      throw webidl.errors.exception({
        header: prefix,
        message: `${argument} (${webidl.util.Stringify(V)}) is not iterable.`
      })
    }

    // 2. Let method be ? GetMethod(V, @@iterator).
    /** @type {Generator} */
    const method = typeof Iterable === 'function' ? Iterable() : V?.[Symbol.iterator]?.()
    const seq = []
    let index = 0

    // 3. If method is undefined, throw a TypeError.
    if (
      method === undefined ||
      typeof method.next !== 'function'
    ) {
      throw webidl.errors.exception({
        header: prefix,
        message: `${argument} is not iterable.`
      })
    }

    // https://webidl.spec.whatwg.org/#create-sequence-from-iterable
    while (true) {
      const { done, value } = method.next()

      if (done) {
        break
      }

      seq.push(converter(value, prefix, `${argument}[${index++}]`))
    }

    return seq
  }
}

// https://webidl.spec.whatwg.org/#es-to-record
webidl.recordConverter = function (keyConverter, valueConverter) {
  return (O, prefix, argument) => {
    // 1. If Type(O) is not Object, throw a TypeError.
    if (webidl.util.Type(O) !== 'Object') {
      throw webidl.errors.exception({
        header: prefix,
        message: `${argument} ("${webidl.util.Type(O)}") is not an Object.`
      })
    }

    // 2. Let result be a new empty instance of record<K, V>.
    const result = {}

    if (!types.isProxy(O)) {
      // 1. Let desc be ? O.[[GetOwnProperty]](key).
      const keys = [...Object.getOwnPropertyNames(O), ...Object.getOwnPropertySymbols(O)]

      for (const key of keys) {
        // 1. Let typedKey be key converted to an IDL value of type K.
        const typedKey = keyConverter(key, prefix, argument)

        // 2. Let value be ? Get(O, key).
        // 3. Let typedValue be value converted to an IDL value of type V.
        const typedValue = valueConverter(O[key], prefix, argument)

        // 4. Set result[typedKey] to typedValue.
        result[typedKey] = typedValue
      }

      // 5. Return result.
      return result
    }

    // 3. Let keys be ? O.[[OwnPropertyKeys]]().
    const keys = Reflect.ownKeys(O)

    // 4. For each key of keys.
    for (const key of keys) {
      // 1. Let desc be ? O.[[GetOwnProperty]](key).
      const desc = Reflect.getOwnPropertyDescriptor(O, key)

      // 2. If desc is not undefined and desc.[[Enumerable]] is true:
      if (desc?.enumerable) {
        // 1. Let typedKey be key converted to an IDL value of type K.
        const typedKey = keyConverter(key, prefix, argument)

        // 2. Let value be ? Get(O, key).
        // 3. Let typedValue be value converted to an IDL value of type V.
        const typedValue = valueConverter(O[key], prefix, argument)

        // 4. Set result[typedKey] to typedValue.
        result[typedKey] = typedValue
      }
    }

    // 5. Return result.
    return result
  }
}

webidl.interfaceConverter = function (i) {
  return (V, prefix, argument, opts) => {
    if (opts?.strict !== false && !(V instanceof i)) {
      throw webidl.errors.exception({
        header: prefix,
        message: `Expected ${argument} ("${webidl.util.Stringify(V)}") to be an instance of ${i.name}.`
      })
    }

    return V
  }
}

webidl.dictionaryConverter = function (converters) {
  return (dictionary, prefix, argument) => {
    const type = webidl.util.Type(dictionary)
    const dict = {}

    if (type === 'Null' || type === 'Undefined') {
      return dict
    } else if (type !== 'Object') {
      throw webidl.errors.exception({
        header: prefix,
        message: `Expected ${dictionary} to be one of: Null, Undefined, Object.`
      })
    }

    for (const options of converters) {
      const { key, defaultValue, required, converter } = options

      if (required === true) {
        if (!Object.hasOwn(dictionary, key)) {
          throw webidl.errors.exception({
            header: prefix,
            message: `Missing required key "${key}".`
          })
        }
      }

      let value = dictionary[key]
      const hasDefault = Object.hasOwn(options, 'defaultValue')

      // Only use defaultValue if value is undefined and
      // a defaultValue options was provided.
      if (hasDefault && value !== null) {
        value ??= defaultValue()
      }

      // A key can be optional and have no default value.
      // When this happens, do not perform a conversion,
      // and do not assign the key a value.
      if (required || hasDefault || value !== undefined) {
        value = converter(value, prefix, `${argument}.${key}`)

        if (
          options.allowedValues &&
          !options.allowedValues.includes(value)
        ) {
          throw webidl.errors.exception({
            header: prefix,
            message: `${value} is not an accepted type. Expected one of ${options.allowedValues.join(', ')}.`
          })
        }

        dict[key] = value
      }
    }

    return dict
  }
}

webidl.nullableConverter = function (converter) {
  return (V, prefix, argument) => {
    if (V === null) {
      return V
    }

    return converter(V, prefix, argument)
  }
}

// https://webidl.spec.whatwg.org/#es-DOMString
webidl.converters.DOMString = function (V, prefix, argument, opts) {
  // 1. If V is null and the conversion is to an IDL type
  //    associated with the [LegacyNullToEmptyString]
  //    extended attribute, then return the DOMString value
  //    that represents the empty string.
  if (V === null && opts?.legacyNullToEmptyString) {
    return ''
  }

  // 2. Let x be ? ToString(V).
  if (typeof V === 'symbol') {
    throw webidl.errors.exception({
      header: prefix,
      message: `${argument} is a symbol, which cannot be converted to a DOMString.`
    })
  }

  // 3. Return the IDL DOMString value that represents the
  //    same sequence of code units as the one the
  //    ECMAScript String value x represents.
  return String(V)
}

// https://webidl.spec.whatwg.org/#es-ByteString
webidl.converters.ByteString = function (V, prefix, argument) {
  // 1. Let x be ? ToString(V).
  // Note: DOMString converter perform ? ToString(V)
  const x = webidl.converters.DOMString(V, prefix, argument)

  // 2. If the value of any element of x is greater than
  //    255, then throw a TypeError.
  for (let index = 0; index < x.length; index++) {
    if (x.charCodeAt(index) > 255) {
      throw new TypeError(
        'Cannot convert argument to a ByteString because the character at ' +
        `index ${index} has a value of ${x.charCodeAt(index)} which is greater than 255.`
      )
    }
  }

  // 3. Return an IDL ByteString value whose length is the
  //    length of x, and where the value of each element is
  //    the value of the corresponding element of x.
  return x
}

// https://webidl.spec.whatwg.org/#es-USVString
// TODO: rewrite this so we can control the errors thrown
webidl.converters.USVString = toUSVString

// https://webidl.spec.whatwg.org/#es-boolean
webidl.converters.boolean = function (V) {
  // 1. Let x be the result of computing ToBoolean(V).
  const x = Boolean(V)

  // 2. Return the IDL boolean value that is the one that represents
  //    the same truth value as the ECMAScript Boolean value x.
  return x
}

// https://webidl.spec.whatwg.org/#es-any
webidl.converters.any = function (V) {
  return V
}

// https://webidl.spec.whatwg.org/#es-long-long
webidl.converters['long long'] = function (V, prefix, argument) {
  // 1. Let x be ? ConvertToInt(V, 64, "signed").
  const x = webidl.util.ConvertToInt(V, 64, 'signed', undefined, prefix, argument)

  // 2. Return the IDL long long value that represents
  //    the same numeric value as x.
  return x
}

// https://webidl.spec.whatwg.org/#es-unsigned-long-long
webidl.converters['unsigned long long'] = function (V, prefix, argument) {
  // 1. Let x be ? ConvertToInt(V, 64, "unsigned").
  const x = webidl.util.ConvertToInt(V, 64, 'unsigned', undefined, prefix, argument)

  // 2. Return the IDL unsigned long long value that
  //    represents the same numeric value as x.
  return x
}

// https://webidl.spec.whatwg.org/#es-unsigned-long
webidl.converters['unsigned long'] = function (V, prefix, argument) {
  // 1. Let x be ? ConvertToInt(V, 32, "unsigned").
  const x = webidl.util.ConvertToInt(V, 32, 'unsigned', undefined, prefix, argument)

  // 2. Return the IDL unsigned long value that
  //    represents the same numeric value as x.
  return x
}

// https://webidl.spec.whatwg.org/#es-unsigned-short
webidl.converters['unsigned short'] = function (V, prefix, argument, opts) {
  // 1. Let x be ? ConvertToInt(V, 16, "unsigned").
  const x = webidl.util.ConvertToInt(V, 16, 'unsigned', opts, prefix, argument)

  // 2. Return the IDL unsigned short value that represents
  //    the same numeric value as x.
  return x
}

// https://webidl.spec.whatwg.org/#idl-ArrayBuffer
webidl.converters.ArrayBuffer = function (V, prefix, argument, opts) {
  // 1. If Type(V) is not Object, or V does not have an
  //    [[ArrayBufferData]] internal slot, then throw a
  //    TypeError.
  // see: https://tc39.es/ecma262/#sec-properties-of-the-arraybuffer-instances
  // see: https://tc39.es/ecma262/#sec-properties-of-the-sharedarraybuffer-instances
  if (
    webidl.util.Type(V) !== 'Object' ||
    !types.isAnyArrayBuffer(V)
  ) {
    throw webidl.errors.conversionFailed({
      prefix,
      argument: `${argument} ("${webidl.util.Stringify(V)}")`,
      types: ['ArrayBuffer']
    })
  }

  // 2. If the conversion is not to an IDL type associated
  //    with the [AllowShared] extended attribute, and
  //    IsSharedArrayBuffer(V) is true, then throw a
  //    TypeError.
  if (opts?.allowShared === false && types.isSharedArrayBuffer(V)) {
    throw webidl.errors.exception({
      header: 'ArrayBuffer',
      message: 'SharedArrayBuffer is not allowed.'
    })
  }

  // 3. If the conversion is not to an IDL type associated
  //    with the [AllowResizable] extended attribute, and
  //    IsResizableArrayBuffer(V) is true, then throw a
  //    TypeError.
  if (V.resizable || V.growable) {
    throw webidl.errors.exception({
      header: 'ArrayBuffer',
      message: 'Received a resizable ArrayBuffer.'
    })
  }

  // 4. Return the IDL ArrayBuffer value that is a
  //    reference to the same object as V.
  return V
}

webidl.converters.TypedArray = function (V, T, prefix, name, opts) {
  // 1. Let T be the IDL type V is being converted to.

  // 2. If Type(V) is not Object, or V does not have a
  //    [[TypedArrayName]] internal slot with a value
  //    equal to T’s name, then throw a TypeError.
  if (
    webidl.util.Type(V) !== 'Object' ||
    !types.isTypedArray(V) ||
    V.constructor.name !== T.name
  ) {
    throw webidl.errors.conversionFailed({
      prefix,
      argument: `${name} ("${webidl.util.Stringify(V)}")`,
      types: [T.name]
    })
  }

  // 3. If the conversion is not to an IDL type associated
  //    with the [AllowShared] extended attribute, and
  //    IsSharedArrayBuffer(V.[[ViewedArrayBuffer]]) is
  //    true, then throw a TypeError.
  if (opts?.allowShared === false && types.isSharedArrayBuffer(V.buffer)) {
    throw webidl.errors.exception({
      header: 'ArrayBuffer',
      message: 'SharedArrayBuffer is not allowed.'
    })
  }

  // 4. If the conversion is not to an IDL type associated
  //    with the [AllowResizable] extended attribute, and
  //    IsResizableArrayBuffer(V.[[ViewedArrayBuffer]]) is
  //    true, then throw a TypeError.
  if (V.buffer.resizable || V.buffer.growable) {
    throw webidl.errors.exception({
      header: 'ArrayBuffer',
      message: 'Received a resizable ArrayBuffer.'
    })
  }

  // 5. Return the IDL value of type T that is a reference
  //    to the same object as V.
  return V
}

webidl.converters.DataView = function (V, prefix, name, opts) {
  // 1. If Type(V) is not Object, or V does not have a
  //    [[DataView]] internal slot, then throw a TypeError.
  if (webidl.util.Type(V) !== 'Object' || !types.isDataView(V)) {
    throw webidl.errors.exception({
      header: prefix,
      message: `${name} is not a DataView.`
    })
  }

  // 2. If the conversion is not to an IDL type associated
  //    with the [AllowShared] extended attribute, and
  //    IsSharedArrayBuffer(V.[[ViewedArrayBuffer]]) is true,
  //    then throw a TypeError.
  if (opts?.allowShared === false && types.isSharedArrayBuffer(V.buffer)) {
    throw webidl.errors.exception({
      header: 'ArrayBuffer',
      message: 'SharedArrayBuffer is not allowed.'
    })
  }

  // 3. If the conversion is not to an IDL type associated
  //    with the [AllowResizable] extended attribute, and
  //    IsResizableArrayBuffer(V.[[ViewedArrayBuffer]]) is
  //    true, then throw a TypeError.
  if (V.buffer.resizable || V.buffer.growable) {
    throw webidl.errors.exception({
      header: 'ArrayBuffer',
      message: 'Received a resizable ArrayBuffer.'
    })
  }

  // 4. Return the IDL DataView value that is a reference
  //    to the same object as V.
  return V
}

// https://webidl.spec.whatwg.org/#BufferSource
webidl.converters.BufferSource = function (V, prefix, name, opts) {
  if (types.isAnyArrayBuffer(V)) {
    return webidl.converters.ArrayBuffer(V, prefix, name, { ...opts, allowShared: false })
  }

  if (types.isTypedArray(V)) {
    return webidl.converters.TypedArray(V, V.constructor, prefix, name, { ...opts, allowShared: false })
  }

  if (types.isDataView(V)) {
    return webidl.converters.DataView(V, prefix, name, { ...opts, allowShared: false })
  }

  throw webidl.errors.conversionFailed({
    prefix,
    argument: `${name} ("${webidl.util.Stringify(V)}")`,
    types: ['BufferSource']
  })
}

webidl.converters['sequence<ByteString>'] = webidl.sequenceConverter(
  webidl.converters.ByteString
)

webidl.converters['sequence<sequence<ByteString>>'] = webidl.sequenceConverter(
  webidl.converters['sequence<ByteString>']
)

webidl.converters['record<ByteString, ByteString>'] = webidl.recordConverter(
  webidl.converters.ByteString,
  webidl.converters.ByteString
)

module.exports = {
  webidl
}


/***/ }),

/***/ 2607:
/***/ ((module) => {



/**
 * @see https://encoding.spec.whatwg.org/#concept-encoding-get
 * @param {string|undefined} label
 */
function getEncoding (label) {
  if (!label) {
    return 'failure'
  }

  // 1. Remove any leading and trailing ASCII whitespace from label.
  // 2. If label is an ASCII case-insensitive match for any of the
  //    labels listed in the table below, then return the
  //    corresponding encoding; otherwise return failure.
  switch (label.trim().toLowerCase()) {
    case 'unicode-1-1-utf-8':
    case 'unicode11utf8':
    case 'unicode20utf8':
    case 'utf-8':
    case 'utf8':
    case 'x-unicode20utf8':
      return 'UTF-8'
    case '866':
    case 'cp866':
    case 'csibm866':
    case 'ibm866':
      return 'IBM866'
    case 'csisolatin2':
    case 'iso-8859-2':
    case 'iso-ir-101':
    case 'iso8859-2':
    case 'iso88592':
    case 'iso_8859-2':
    case 'iso_8859-2:1987':
    case 'l2':
    case 'latin2':
      return 'ISO-8859-2'
    case 'csisolatin3':
    case 'iso-8859-3':
    case 'iso-ir-109':
    case 'iso8859-3':
    case 'iso88593':
    case 'iso_8859-3':
    case 'iso_8859-3:1988':
    case 'l3':
    case 'latin3':
      return 'ISO-8859-3'
    case 'csisolatin4':
    case 'iso-8859-4':
    case 'iso-ir-110':
    case 'iso8859-4':
    case 'iso88594':
    case 'iso_8859-4':
    case 'iso_8859-4:1988':
    case 'l4':
    case 'latin4':
      return 'ISO-8859-4'
    case 'csisolatincyrillic':
    case 'cyrillic':
    case 'iso-8859-5':
    case 'iso-ir-144':
    case 'iso8859-5':
    case 'iso88595':
    case 'iso_8859-5':
    case 'iso_8859-5:1988':
      return 'ISO-8859-5'
    case 'arabic':
    case 'asmo-708':
    case 'csiso88596e':
    case 'csiso88596i':
    case 'csisolatinarabic':
    case 'ecma-114':
    case 'iso-8859-6':
    case 'iso-8859-6-e':
    case 'iso-8859-6-i':
    case 'iso-ir-127':
    case 'iso8859-6':
    case 'iso88596':
    case 'iso_8859-6':
    case 'iso_8859-6:1987':
      return 'ISO-8859-6'
    case 'csisolatingreek':
    case 'ecma-118':
    case 'elot_928':
    case 'greek':
    case 'greek8':
    case 'iso-8859-7':
    case 'iso-ir-126':
    case 'iso8859-7':
    case 'iso88597':
    case 'iso_8859-7':
    case 'iso_8859-7:1987':
    case 'sun_eu_greek':
      return 'ISO-8859-7'
    case 'csiso88598e':
    case 'csisolatinhebrew':
    case 'hebrew':
    case 'iso-8859-8':
    case 'iso-8859-8-e':
    case 'iso-ir-138':
    case 'iso8859-8':
    case 'iso88598':
    case 'iso_8859-8':
    case 'iso_8859-8:1988':
    case 'visual':
      return 'ISO-8859-8'
    case 'csiso88598i':
    case 'iso-8859-8-i':
    case 'logical':
      return 'ISO-8859-8-I'
    case 'csisolatin6':
    case 'iso-8859-10':
    case 'iso-ir-157':
    case 'iso8859-10':
    case 'iso885910':
    case 'l6':
    case 'latin6':
      return 'ISO-8859-10'
    case 'iso-8859-13':
    case 'iso8859-13':
    case 'iso885913':
      return 'ISO-8859-13'
    case 'iso-8859-14':
    case 'iso8859-14':
    case 'iso885914':
      return 'ISO-8859-14'
    case 'csisolatin9':
    case 'iso-8859-15':
    case 'iso8859-15':
    case 'iso885915':
    case 'iso_8859-15':
    case 'l9':
      return 'ISO-8859-15'
    case 'iso-8859-16':
      return 'ISO-8859-16'
    case 'cskoi8r':
    case 'koi':
    case 'koi8':
    case 'koi8-r':
    case 'koi8_r':
      return 'KOI8-R'
    case 'koi8-ru':
    case 'koi8-u':
      return 'KOI8-U'
    case 'csmacintosh':
    case 'mac':
    case 'macintosh':
    case 'x-mac-roman':
      return 'macintosh'
    case 'iso-8859-11':
    case 'iso8859-11':
    case 'iso885911':
    case 'tis-620':
    case 'windows-874':
      return 'windows-874'
    case 'cp1250':
    case 'windows-1250':
    case 'x-cp1250':
      return 'windows-1250'
    case 'cp1251':
    case 'windows-1251':
    case 'x-cp1251':
      return 'windows-1251'
    case 'ansi_x3.4-1968':
    case 'ascii':
    case 'cp1252':
    case 'cp819':
    case 'csisolatin1':
    case 'ibm819':
    case 'iso-8859-1':
    case 'iso-ir-100':
    case 'iso8859-1':
    case 'iso88591':
    case 'iso_8859-1':
    case 'iso_8859-1:1987':
    case 'l1':
    case 'latin1':
    case 'us-ascii':
    case 'windows-1252':
    case 'x-cp1252':
      return 'windows-1252'
    case 'cp1253':
    case 'windows-1253':
    case 'x-cp1253':
      return 'windows-1253'
    case 'cp1254':
    case 'csisolatin5':
    case 'iso-8859-9':
    case 'iso-ir-148':
    case 'iso8859-9':
    case 'iso88599':
    case 'iso_8859-9':
    case 'iso_8859-9:1989':
    case 'l5':
    case 'latin5':
    case 'windows-1254':
    case 'x-cp1254':
      return 'windows-1254'
    case 'cp1255':
    case 'windows-1255':
    case 'x-cp1255':
      return 'windows-1255'
    case 'cp1256':
    case 'windows-1256':
    case 'x-cp1256':
      return 'windows-1256'
    case 'cp1257':
    case 'windows-1257':
    case 'x-cp1257':
      return 'windows-1257'
    case 'cp1258':
    case 'windows-1258':
    case 'x-cp1258':
      return 'windows-1258'
    case 'x-mac-cyrillic':
    case 'x-mac-ukrainian':
      return 'x-mac-cyrillic'
    case 'chinese':
    case 'csgb2312':
    case 'csiso58gb231280':
    case 'gb2312':
    case 'gb_2312':
    case 'gb_2312-80':
    case 'gbk':
    case 'iso-ir-58':
    case 'x-gbk':
      return 'GBK'
    case 'gb18030':
      return 'gb18030'
    case 'big5':
    case 'big5-hkscs':
    case 'cn-big5':
    case 'csbig5':
    case 'x-x-big5':
      return 'Big5'
    case 'cseucpkdfmtjapanese':
    case 'euc-jp':
    case 'x-euc-jp':
      return 'EUC-JP'
    case 'csiso2022jp':
    case 'iso-2022-jp':
      return 'ISO-2022-JP'
    case 'csshiftjis':
    case 'ms932':
    case 'ms_kanji':
    case 'shift-jis':
    case 'shift_jis':
    case 'sjis':
    case 'windows-31j':
    case 'x-sjis':
      return 'Shift_JIS'
    case 'cseuckr':
    case 'csksc56011987':
    case 'euc-kr':
    case 'iso-ir-149':
    case 'korean':
    case 'ks_c_5601-1987':
    case 'ks_c_5601-1989':
    case 'ksc5601':
    case 'ksc_5601':
    case 'windows-949':
      return 'EUC-KR'
    case 'csiso2022kr':
    case 'hz-gb-2312':
    case 'iso-2022-cn':
    case 'iso-2022-cn-ext':
    case 'iso-2022-kr':
    case 'replacement':
      return 'replacement'
    case 'unicodefffe':
    case 'utf-16be':
      return 'UTF-16BE'
    case 'csunicode':
    case 'iso-10646-ucs-2':
    case 'ucs-2':
    case 'unicode':
    case 'unicodefeff':
    case 'utf-16':
    case 'utf-16le':
      return 'UTF-16LE'
    case 'x-user-defined':
      return 'x-user-defined'
    default: return 'failure'
  }
}

module.exports = {
  getEncoding
}


/***/ }),

/***/ 8355:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const {
  staticPropertyDescriptors,
  readOperation,
  fireAProgressEvent
} = __nccwpck_require__(3610)
const {
  kState,
  kError,
  kResult,
  kEvents,
  kAborted
} = __nccwpck_require__(961)
const { webidl } = __nccwpck_require__(5893)
const { kEnumerableProperty } = __nccwpck_require__(3440)

class FileReader extends EventTarget {
  constructor () {
    super()

    this[kState] = 'empty'
    this[kResult] = null
    this[kError] = null
    this[kEvents] = {
      loadend: null,
      error: null,
      abort: null,
      load: null,
      progress: null,
      loadstart: null
    }
  }

  /**
   * @see https://w3c.github.io/FileAPI/#dfn-readAsArrayBuffer
   * @param {import('buffer').Blob} blob
   */
  readAsArrayBuffer (blob) {
    webidl.brandCheck(this, FileReader)

    webidl.argumentLengthCheck(arguments, 1, 'FileReader.readAsArrayBuffer')

    blob = webidl.converters.Blob(blob, { strict: false })

    // The readAsArrayBuffer(blob) method, when invoked,
    // must initiate a read operation for blob with ArrayBuffer.
    readOperation(this, blob, 'ArrayBuffer')
  }

  /**
   * @see https://w3c.github.io/FileAPI/#readAsBinaryString
   * @param {import('buffer').Blob} blob
   */
  readAsBinaryString (blob) {
    webidl.brandCheck(this, FileReader)

    webidl.argumentLengthCheck(arguments, 1, 'FileReader.readAsBinaryString')

    blob = webidl.converters.Blob(blob, { strict: false })

    // The readAsBinaryString(blob) method, when invoked,
    // must initiate a read operation for blob with BinaryString.
    readOperation(this, blob, 'BinaryString')
  }

  /**
   * @see https://w3c.github.io/FileAPI/#readAsDataText
   * @param {import('buffer').Blob} blob
   * @param {string?} encoding
   */
  readAsText (blob, encoding = undefined) {
    webidl.brandCheck(this, FileReader)

    webidl.argumentLengthCheck(arguments, 1, 'FileReader.readAsText')

    blob = webidl.converters.Blob(blob, { strict: false })

    if (encoding !== undefined) {
      encoding = webidl.converters.DOMString(encoding, 'FileReader.readAsText', 'encoding')
    }

    // The readAsText(blob, encoding) method, when invoked,
    // must initiate a read operation for blob with Text and encoding.
    readOperation(this, blob, 'Text', encoding)
  }

  /**
   * @see https://w3c.github.io/FileAPI/#dfn-readAsDataURL
   * @param {import('buffer').Blob} blob
   */
  readAsDataURL (blob) {
    webidl.brandCheck(this, FileReader)

    webidl.argumentLengthCheck(arguments, 1, 'FileReader.readAsDataURL')

    blob = webidl.converters.Blob(blob, { strict: false })

    // The readAsDataURL(blob) method, when invoked, must
    // initiate a read operation for blob with DataURL.
    readOperation(this, blob, 'DataURL')
  }

  /**
   * @see https://w3c.github.io/FileAPI/#dfn-abort
   */
  abort () {
    // 1. If this's state is "empty" or if this's state is
    //    "done" set this's result to null and terminate
    //    this algorithm.
    if (this[kState] === 'empty' || this[kState] === 'done') {
      this[kResult] = null
      return
    }

    // 2. If this's state is "loading" set this's state to
    //    "done" and set this's result to null.
    if (this[kState] === 'loading') {
      this[kState] = 'done'
      this[kResult] = null
    }

    // 3. If there are any tasks from this on the file reading
    //    task source in an affiliated task queue, then remove
    //    those tasks from that task queue.
    this[kAborted] = true

    // 4. Terminate the algorithm for the read method being processed.
    // TODO

    // 5. Fire a progress event called abort at this.
    fireAProgressEvent('abort', this)

    // 6. If this's state is not "loading", fire a progress
    //    event called loadend at this.
    if (this[kState] !== 'loading') {
      fireAProgressEvent('loadend', this)
    }
  }

  /**
   * @see https://w3c.github.io/FileAPI/#dom-filereader-readystate
   */
  get readyState () {
    webidl.brandCheck(this, FileReader)

    switch (this[kState]) {
      case 'empty': return this.EMPTY
      case 'loading': return this.LOADING
      case 'done': return this.DONE
    }
  }

  /**
   * @see https://w3c.github.io/FileAPI/#dom-filereader-result
   */
  get result () {
    webidl.brandCheck(this, FileReader)

    // The result attribute’s getter, when invoked, must return
    // this's result.
    return this[kResult]
  }

  /**
   * @see https://w3c.github.io/FileAPI/#dom-filereader-error
   */
  get error () {
    webidl.brandCheck(this, FileReader)

    // The error attribute’s getter, when invoked, must return
    // this's error.
    return this[kError]
  }

  get onloadend () {
    webidl.brandCheck(this, FileReader)

    return this[kEvents].loadend
  }

  set onloadend (fn) {
    webidl.brandCheck(this, FileReader)

    if (this[kEvents].loadend) {
      this.removeEventListener('loadend', this[kEvents].loadend)
    }

    if (typeof fn === 'function') {
      this[kEvents].loadend = fn
      this.addEventListener('loadend', fn)
    } else {
      this[kEvents].loadend = null
    }
  }

  get onerror () {
    webidl.brandCheck(this, FileReader)

    return this[kEvents].error
  }

  set onerror (fn) {
    webidl.brandCheck(this, FileReader)

    if (this[kEvents].error) {
      this.removeEventListener('error', this[kEvents].error)
    }

    if (typeof fn === 'function') {
      this[kEvents].error = fn
      this.addEventListener('error', fn)
    } else {
      this[kEvents].error = null
    }
  }

  get onloadstart () {
    webidl.brandCheck(this, FileReader)

    return this[kEvents].loadstart
  }

  set onloadstart (fn) {
    webidl.brandCheck(this, FileReader)

    if (this[kEvents].loadstart) {
      this.removeEventListener('loadstart', this[kEvents].loadstart)
    }

    if (typeof fn === 'function') {
      this[kEvents].loadstart = fn
      this.addEventListener('loadstart', fn)
    } else {
      this[kEvents].loadstart = null
    }
  }

  get onprogress () {
    webidl.brandCheck(this, FileReader)

    return this[kEvents].progress
  }

  set onprogress (fn) {
    webidl.brandCheck(this, FileReader)

    if (this[kEvents].progress) {
      this.removeEventListener('progress', this[kEvents].progress)
    }

    if (typeof fn === 'function') {
      this[kEvents].progress = fn
      this.addEventListener('progress', fn)
    } else {
      this[kEvents].progress = null
    }
  }

  get onload () {
    webidl.brandCheck(this, FileReader)

    return this[kEvents].load
  }

  set onload (fn) {
    webidl.brandCheck(this, FileReader)

    if (this[kEvents].load) {
      this.removeEventListener('load', this[kEvents].load)
    }

    if (typeof fn === 'function') {
      this[kEvents].load = fn
      this.addEventListener('load', fn)
    } else {
      this[kEvents].load = null
    }
  }

  get onabort () {
    webidl.brandCheck(this, FileReader)

    return this[kEvents].abort
  }

  set onabort (fn) {
    webidl.brandCheck(this, FileReader)

    if (this[kEvents].abort) {
      this.removeEventListener('abort', this[kEvents].abort)
    }

    if (typeof fn === 'function') {
      this[kEvents].abort = fn
      this.addEventListener('abort', fn)
    } else {
      this[kEvents].abort = null
    }
  }
}

// https://w3c.github.io/FileAPI/#dom-filereader-empty
FileReader.EMPTY = FileReader.prototype.EMPTY = 0
// https://w3c.github.io/FileAPI/#dom-filereader-loading
FileReader.LOADING = FileReader.prototype.LOADING = 1
// https://w3c.github.io/FileAPI/#dom-filereader-done
FileReader.DONE = FileReader.prototype.DONE = 2

Object.defineProperties(FileReader.prototype, {
  EMPTY: staticPropertyDescriptors,
  LOADING: staticPropertyDescriptors,
  DONE: staticPropertyDescriptors,
  readAsArrayBuffer: kEnumerableProperty,
  readAsBinaryString: kEnumerableProperty,
  readAsText: kEnumerableProperty,
  readAsDataURL: kEnumerableProperty,
  abort: kEnumerableProperty,
  readyState: kEnumerableProperty,
  result: kEnumerableProperty,
  error: kEnumerableProperty,
  onloadstart: kEnumerableProperty,
  onprogress: kEnumerableProperty,
  onload: kEnumerableProperty,
  onabort: kEnumerableProperty,
  onerror: kEnumerableProperty,
  onloadend: kEnumerableProperty,
  [Symbol.toStringTag]: {
    value: 'FileReader',
    writable: false,
    enumerable: false,
    configurable: true
  }
})

Object.defineProperties(FileReader, {
  EMPTY: staticPropertyDescriptors,
  LOADING: staticPropertyDescriptors,
  DONE: staticPropertyDescriptors
})

module.exports = {
  FileReader
}


/***/ }),

/***/ 8573:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { webidl } = __nccwpck_require__(5893)

const kState = Symbol('ProgressEvent state')

/**
 * @see https://xhr.spec.whatwg.org/#progressevent
 */
class ProgressEvent extends Event {
  constructor (type, eventInitDict = {}) {
    type = webidl.converters.DOMString(type, 'ProgressEvent constructor', 'type')
    eventInitDict = webidl.converters.ProgressEventInit(eventInitDict ?? {})

    super(type, eventInitDict)

    this[kState] = {
      lengthComputable: eventInitDict.lengthComputable,
      loaded: eventInitDict.loaded,
      total: eventInitDict.total
    }
  }

  get lengthComputable () {
    webidl.brandCheck(this, ProgressEvent)

    return this[kState].lengthComputable
  }

  get loaded () {
    webidl.brandCheck(this, ProgressEvent)

    return this[kState].loaded
  }

  get total () {
    webidl.brandCheck(this, ProgressEvent)

    return this[kState].total
  }
}

webidl.converters.ProgressEventInit = webidl.dictionaryConverter([
  {
    key: 'lengthComputable',
    converter: webidl.converters.boolean,
    defaultValue: () => false
  },
  {
    key: 'loaded',
    converter: webidl.converters['unsigned long long'],
    defaultValue: () => 0
  },
  {
    key: 'total',
    converter: webidl.converters['unsigned long long'],
    defaultValue: () => 0
  },
  {
    key: 'bubbles',
    converter: webidl.converters.boolean,
    defaultValue: () => false
  },
  {
    key: 'cancelable',
    converter: webidl.converters.boolean,
    defaultValue: () => false
  },
  {
    key: 'composed',
    converter: webidl.converters.boolean,
    defaultValue: () => false
  }
])

module.exports = {
  ProgressEvent
}


/***/ }),

/***/ 961:
/***/ ((module) => {



module.exports = {
  kState: Symbol('FileReader state'),
  kResult: Symbol('FileReader result'),
  kError: Symbol('FileReader error'),
  kLastProgressEventFired: Symbol('FileReader last progress event fired timestamp'),
  kEvents: Symbol('FileReader events'),
  kAborted: Symbol('FileReader aborted')
}


/***/ }),

/***/ 3610:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const {
  kState,
  kError,
  kResult,
  kAborted,
  kLastProgressEventFired
} = __nccwpck_require__(961)
const { ProgressEvent } = __nccwpck_require__(8573)
const { getEncoding } = __nccwpck_require__(2607)
const { serializeAMimeType, parseMIMEType } = __nccwpck_require__(1900)
const { types } = __nccwpck_require__(7975)
const { StringDecoder } = __nccwpck_require__(3193)
const { btoa } = __nccwpck_require__(4573)

/** @type {PropertyDescriptor} */
const staticPropertyDescriptors = {
  enumerable: true,
  writable: false,
  configurable: false
}

/**
 * @see https://w3c.github.io/FileAPI/#readOperation
 * @param {import('./filereader').FileReader} fr
 * @param {import('buffer').Blob} blob
 * @param {string} type
 * @param {string?} encodingName
 */
function readOperation (fr, blob, type, encodingName) {
  // 1. If fr’s state is "loading", throw an InvalidStateError
  //    DOMException.
  if (fr[kState] === 'loading') {
    throw new DOMException('Invalid state', 'InvalidStateError')
  }

  // 2. Set fr’s state to "loading".
  fr[kState] = 'loading'

  // 3. Set fr’s result to null.
  fr[kResult] = null

  // 4. Set fr’s error to null.
  fr[kError] = null

  // 5. Let stream be the result of calling get stream on blob.
  /** @type {import('stream/web').ReadableStream} */
  const stream = blob.stream()

  // 6. Let reader be the result of getting a reader from stream.
  const reader = stream.getReader()

  // 7. Let bytes be an empty byte sequence.
  /** @type {Uint8Array[]} */
  const bytes = []

  // 8. Let chunkPromise be the result of reading a chunk from
  //    stream with reader.
  let chunkPromise = reader.read()

  // 9. Let isFirstChunk be true.
  let isFirstChunk = true

  // 10. In parallel, while true:
  // Note: "In parallel" just means non-blocking
  // Note 2: readOperation itself cannot be async as double
  // reading the body would then reject the promise, instead
  // of throwing an error.
  ;(async () => {
    while (!fr[kAborted]) {
      // 1. Wait for chunkPromise to be fulfilled or rejected.
      try {
        const { done, value } = await chunkPromise

        // 2. If chunkPromise is fulfilled, and isFirstChunk is
        //    true, queue a task to fire a progress event called
        //    loadstart at fr.
        if (isFirstChunk && !fr[kAborted]) {
          queueMicrotask(() => {
            fireAProgressEvent('loadstart', fr)
          })
        }

        // 3. Set isFirstChunk to false.
        isFirstChunk = false

        // 4. If chunkPromise is fulfilled with an object whose
        //    done property is false and whose value property is
        //    a Uint8Array object, run these steps:
        if (!done && types.isUint8Array(value)) {
          // 1. Let bs be the byte sequence represented by the
          //    Uint8Array object.

          // 2. Append bs to bytes.
          bytes.push(value)

          // 3. If roughly 50ms have passed since these steps
          //    were last invoked, queue a task to fire a
          //    progress event called progress at fr.
          if (
            (
              fr[kLastProgressEventFired] === undefined ||
              Date.now() - fr[kLastProgressEventFired] >= 50
            ) &&
            !fr[kAborted]
          ) {
            fr[kLastProgressEventFired] = Date.now()
            queueMicrotask(() => {
              fireAProgressEvent('progress', fr)
            })
          }

          // 4. Set chunkPromise to the result of reading a
          //    chunk from stream with reader.
          chunkPromise = reader.read()
        } else if (done) {
          // 5. Otherwise, if chunkPromise is fulfilled with an
          //    object whose done property is true, queue a task
          //    to run the following steps and abort this algorithm:
          queueMicrotask(() => {
            // 1. Set fr’s state to "done".
            fr[kState] = 'done'

            // 2. Let result be the result of package data given
            //    bytes, type, blob’s type, and encodingName.
            try {
              const result = packageData(bytes, type, blob.type, encodingName)

              // 4. Else:

              if (fr[kAborted]) {
                return
              }

              // 1. Set fr’s result to result.
              fr[kResult] = result

              // 2. Fire a progress event called load at the fr.
              fireAProgressEvent('load', fr)
            } catch (error) {
              // 3. If package data threw an exception error:

              // 1. Set fr’s error to error.
              fr[kError] = error

              // 2. Fire a progress event called error at fr.
              fireAProgressEvent('error', fr)
            }

            // 5. If fr’s state is not "loading", fire a progress
            //    event called loadend at the fr.
            if (fr[kState] !== 'loading') {
              fireAProgressEvent('loadend', fr)
            }
          })

          break
        }
      } catch (error) {
        if (fr[kAborted]) {
          return
        }

        // 6. Otherwise, if chunkPromise is rejected with an
        //    error error, queue a task to run the following
        //    steps and abort this algorithm:
        queueMicrotask(() => {
          // 1. Set fr’s state to "done".
          fr[kState] = 'done'

          // 2. Set fr’s error to error.
          fr[kError] = error

          // 3. Fire a progress event called error at fr.
          fireAProgressEvent('error', fr)

          // 4. If fr’s state is not "loading", fire a progress
          //    event called loadend at fr.
          if (fr[kState] !== 'loading') {
            fireAProgressEvent('loadend', fr)
          }
        })

        break
      }
    }
  })()
}

/**
 * @see https://w3c.github.io/FileAPI/#fire-a-progress-event
 * @see https://dom.spec.whatwg.org/#concept-event-fire
 * @param {string} e The name of the event
 * @param {import('./filereader').FileReader} reader
 */
function fireAProgressEvent (e, reader) {
  // The progress event e does not bubble. e.bubbles must be false
  // The progress event e is NOT cancelable. e.cancelable must be false
  const event = new ProgressEvent(e, {
    bubbles: false,
    cancelable: false
  })

  reader.dispatchEvent(event)
}

/**
 * @see https://w3c.github.io/FileAPI/#blob-package-data
 * @param {Uint8Array[]} bytes
 * @param {string} type
 * @param {string?} mimeType
 * @param {string?} encodingName
 */
function packageData (bytes, type, mimeType, encodingName) {
  // 1. A Blob has an associated package data algorithm, given
  //    bytes, a type, a optional mimeType, and a optional
  //    encodingName, which switches on type and runs the
  //    associated steps:

  switch (type) {
    case 'DataURL': {
      // 1. Return bytes as a DataURL [RFC2397] subject to
      //    the considerations below:
      //  * Use mimeType as part of the Data URL if it is
      //    available in keeping with the Data URL
      //    specification [RFC2397].
      //  * If mimeType is not available return a Data URL
      //    without a media-type. [RFC2397].

      // https://datatracker.ietf.org/doc/html/rfc2397#section-3
      // dataurl    := "data:" [ mediatype ] [ ";base64" ] "," data
      // mediatype  := [ type "/" subtype ] *( ";" parameter )
      // data       := *urlchar
      // parameter  := attribute "=" value
      let dataURL = 'data:'

      const parsed = parseMIMEType(mimeType || 'application/octet-stream')

      if (parsed !== 'failure') {
        dataURL += serializeAMimeType(parsed)
      }

      dataURL += ';base64,'

      const decoder = new StringDecoder('latin1')

      for (const chunk of bytes) {
        dataURL += btoa(decoder.write(chunk))
      }

      dataURL += btoa(decoder.end())

      return dataURL
    }
    case 'Text': {
      // 1. Let encoding be failure
      let encoding = 'failure'

      // 2. If the encodingName is present, set encoding to the
      //    result of getting an encoding from encodingName.
      if (encodingName) {
        encoding = getEncoding(encodingName)
      }

      // 3. If encoding is failure, and mimeType is present:
      if (encoding === 'failure' && mimeType) {
        // 1. Let type be the result of parse a MIME type
        //    given mimeType.
        const type = parseMIMEType(mimeType)

        // 2. If type is not failure, set encoding to the result
        //    of getting an encoding from type’s parameters["charset"].
        if (type !== 'failure') {
          encoding = getEncoding(type.parameters.get('charset'))
        }
      }

      // 4. If encoding is failure, then set encoding to UTF-8.
      if (encoding === 'failure') {
        encoding = 'UTF-8'
      }

      // 5. Decode bytes using fallback encoding encoding, and
      //    return the result.
      return decode(bytes, encoding)
    }
    case 'ArrayBuffer': {
      // Return a new ArrayBuffer whose contents are bytes.
      const sequence = combineByteSequences(bytes)

      return sequence.buffer
    }
    case 'BinaryString': {
      // Return bytes as a binary string, in which every byte
      //  is represented by a code unit of equal value [0..255].
      let binaryString = ''

      const decoder = new StringDecoder('latin1')

      for (const chunk of bytes) {
        binaryString += decoder.write(chunk)
      }

      binaryString += decoder.end()

      return binaryString
    }
  }
}

/**
 * @see https://encoding.spec.whatwg.org/#decode
 * @param {Uint8Array[]} ioQueue
 * @param {string} encoding
 */
function decode (ioQueue, encoding) {
  const bytes = combineByteSequences(ioQueue)

  // 1. Let BOMEncoding be the result of BOM sniffing ioQueue.
  const BOMEncoding = BOMSniffing(bytes)

  let slice = 0

  // 2. If BOMEncoding is non-null:
  if (BOMEncoding !== null) {
    // 1. Set encoding to BOMEncoding.
    encoding = BOMEncoding

    // 2. Read three bytes from ioQueue, if BOMEncoding is
    //    UTF-8; otherwise read two bytes.
    //    (Do nothing with those bytes.)
    slice = BOMEncoding === 'UTF-8' ? 3 : 2
  }

  // 3. Process a queue with an instance of encoding’s
  //    decoder, ioQueue, output, and "replacement".

  // 4. Return output.

  const sliced = bytes.slice(slice)
  return new TextDecoder(encoding).decode(sliced)
}

/**
 * @see https://encoding.spec.whatwg.org/#bom-sniff
 * @param {Uint8Array} ioQueue
 */
function BOMSniffing (ioQueue) {
  // 1. Let BOM be the result of peeking 3 bytes from ioQueue,
  //    converted to a byte sequence.
  const [a, b, c] = ioQueue

  // 2. For each of the rows in the table below, starting with
  //    the first one and going down, if BOM starts with the
  //    bytes given in the first column, then return the
  //    encoding given in the cell in the second column of that
  //    row. Otherwise, return null.
  if (a === 0xEF && b === 0xBB && c === 0xBF) {
    return 'UTF-8'
  } else if (a === 0xFE && b === 0xFF) {
    return 'UTF-16BE'
  } else if (a === 0xFF && b === 0xFE) {
    return 'UTF-16LE'
  }

  return null
}

/**
 * @param {Uint8Array[]} sequences
 */
function combineByteSequences (sequences) {
  const size = sequences.reduce((a, b) => {
    return a + b.byteLength
  }, 0)

  let offset = 0

  return sequences.reduce((a, b) => {
    a.set(b, offset)
    offset += b.byteLength
    return a
  }, new Uint8Array(size))
}

module.exports = {
  staticPropertyDescriptors,
  readOperation,
  fireAProgressEvent
}


/***/ }),

/***/ 6897:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { uid, states, sentCloseFrameState, emptyBuffer, opcodes } = __nccwpck_require__(736)
const {
  kReadyState,
  kSentClose,
  kByteParser,
  kReceivedClose,
  kResponse
} = __nccwpck_require__(1216)
const { fireEvent, failWebsocketConnection, isClosing, isClosed, isEstablished, parseExtensions } = __nccwpck_require__(8625)
const { channels } = __nccwpck_require__(2414)
const { CloseEvent } = __nccwpck_require__(5188)
const { makeRequest } = __nccwpck_require__(9967)
const { fetching } = __nccwpck_require__(4398)
const { Headers, getHeadersList } = __nccwpck_require__(660)
const { getDecodeSplit } = __nccwpck_require__(3168)
const { WebsocketFrameSend } = __nccwpck_require__(3264)

/** @type {import('crypto')} */
let crypto
try {
  crypto = __nccwpck_require__(7598)
/* c8 ignore next 3 */
} catch {

}

/**
 * @see https://websockets.spec.whatwg.org/#concept-websocket-establish
 * @param {URL} url
 * @param {string|string[]} protocols
 * @param {import('./websocket').WebSocket} ws
 * @param {(response: any, extensions: string[] | undefined) => void} onEstablish
 * @param {Partial<import('../../types/websocket').WebSocketInit>} options
 */
function establishWebSocketConnection (url, protocols, client, ws, onEstablish, options) {
  // 1. Let requestURL be a copy of url, with its scheme set to "http", if url’s
  //    scheme is "ws", and to "https" otherwise.
  const requestURL = url

  requestURL.protocol = url.protocol === 'ws:' ? 'http:' : 'https:'

  // 2. Let request be a new request, whose URL is requestURL, client is client,
  //    service-workers mode is "none", referrer is "no-referrer", mode is
  //    "websocket", credentials mode is "include", cache mode is "no-store" ,
  //    and redirect mode is "error".
  const request = makeRequest({
    urlList: [requestURL],
    client,
    serviceWorkers: 'none',
    referrer: 'no-referrer',
    mode: 'websocket',
    credentials: 'include',
    cache: 'no-store',
    redirect: 'error'
  })

  // Note: undici extension, allow setting custom headers.
  if (options.headers) {
    const headersList = getHeadersList(new Headers(options.headers))

    request.headersList = headersList
  }

  // 3. Append (`Upgrade`, `websocket`) to request’s header list.
  // 4. Append (`Connection`, `Upgrade`) to request’s header list.
  // Note: both of these are handled by undici currently.
  // https://github.com/nodejs/undici/blob/68c269c4144c446f3f1220951338daef4a6b5ec4/lib/client.js#L1397

  // 5. Let keyValue be a nonce consisting of a randomly selected
  //    16-byte value that has been forgiving-base64-encoded and
  //    isomorphic encoded.
  const keyValue = crypto.randomBytes(16).toString('base64')

  // 6. Append (`Sec-WebSocket-Key`, keyValue) to request’s
  //    header list.
  request.headersList.append('sec-websocket-key', keyValue)

  // 7. Append (`Sec-WebSocket-Version`, `13`) to request’s
  //    header list.
  request.headersList.append('sec-websocket-version', '13')

  // 8. For each protocol in protocols, combine
  //    (`Sec-WebSocket-Protocol`, protocol) in request’s header
  //    list.
  for (const protocol of protocols) {
    request.headersList.append('sec-websocket-protocol', protocol)
  }

  // 9. Let permessageDeflate be a user-agent defined
  //    "permessage-deflate" extension header value.
  // https://github.com/mozilla/gecko-dev/blob/ce78234f5e653a5d3916813ff990f053510227bc/netwerk/protocol/websocket/WebSocketChannel.cpp#L2673
  const permessageDeflate = 'permessage-deflate; client_max_window_bits'

  // 10. Append (`Sec-WebSocket-Extensions`, permessageDeflate) to
  //     request’s header list.
  request.headersList.append('sec-websocket-extensions', permessageDeflate)

  // 11. Fetch request with useParallelQueue set to true, and
  //     processResponse given response being these steps:
  const controller = fetching({
    request,
    useParallelQueue: true,
    dispatcher: options.dispatcher,
    processResponse (response) {
      // 1. If response is a network error or its status is not 101,
      //    fail the WebSocket connection.
      if (response.type === 'error' || response.status !== 101) {
        failWebsocketConnection(ws, 'Received network error or non-101 status code.')
        return
      }

      // 2. If protocols is not the empty list and extracting header
      //    list values given `Sec-WebSocket-Protocol` and response’s
      //    header list results in null, failure, or the empty byte
      //    sequence, then fail the WebSocket connection.
      if (protocols.length !== 0 && !response.headersList.get('Sec-WebSocket-Protocol')) {
        failWebsocketConnection(ws, 'Server did not respond with sent protocols.')
        return
      }

      // 3. Follow the requirements stated step 2 to step 6, inclusive,
      //    of the last set of steps in section 4.1 of The WebSocket
      //    Protocol to validate response. This either results in fail
      //    the WebSocket connection or the WebSocket connection is
      //    established.

      // 2. If the response lacks an |Upgrade| header field or the |Upgrade|
      //    header field contains a value that is not an ASCII case-
      //    insensitive match for the value "websocket", the client MUST
      //    _Fail the WebSocket Connection_.
      if (response.headersList.get('Upgrade')?.toLowerCase() !== 'websocket') {
        failWebsocketConnection(ws, 'Server did not set Upgrade header to "websocket".')
        return
      }

      // 3. If the response lacks a |Connection| header field or the
      //    |Connection| header field doesn't contain a token that is an
      //    ASCII case-insensitive match for the value "Upgrade", the client
      //    MUST _Fail the WebSocket Connection_.
      if (response.headersList.get('Connection')?.toLowerCase() !== 'upgrade') {
        failWebsocketConnection(ws, 'Server did not set Connection header to "upgrade".')
        return
      }

      // 4. If the response lacks a |Sec-WebSocket-Accept| header field or
      //    the |Sec-WebSocket-Accept| contains a value other than the
      //    base64-encoded SHA-1 of the concatenation of the |Sec-WebSocket-
      //    Key| (as a string, not base64-decoded) with the string "258EAFA5-
      //    E914-47DA-95CA-C5AB0DC85B11" but ignoring any leading and
      //    trailing whitespace, the client MUST _Fail the WebSocket
      //    Connection_.
      const secWSAccept = response.headersList.get('Sec-WebSocket-Accept')
      const digest = crypto.createHash('sha1').update(keyValue + uid).digest('base64')
      if (secWSAccept !== digest) {
        failWebsocketConnection(ws, 'Incorrect hash received in Sec-WebSocket-Accept header.')
        return
      }

      // 5. If the response includes a |Sec-WebSocket-Extensions| header
      //    field and this header field indicates the use of an extension
      //    that was not present in the client's handshake (the server has
      //    indicated an extension not requested by the client), the client
      //    MUST _Fail the WebSocket Connection_.  (The parsing of this
      //    header field to determine which extensions are requested is
      //    discussed in Section 9.1.)
      const secExtension = response.headersList.get('Sec-WebSocket-Extensions')
      let extensions

      if (secExtension !== null) {
        extensions = parseExtensions(secExtension)

        if (!extensions.has('permessage-deflate')) {
          failWebsocketConnection(ws, 'Sec-WebSocket-Extensions header does not match.')
          return
        }
      }

      // 6. If the response includes a |Sec-WebSocket-Protocol| header field
      //    and this header field indicates the use of a subprotocol that was
      //    not present in the client's handshake (the server has indicated a
      //    subprotocol not requested by the client), the client MUST _Fail
      //    the WebSocket Connection_.
      const secProtocol = response.headersList.get('Sec-WebSocket-Protocol')

      if (secProtocol !== null) {
        const requestProtocols = getDecodeSplit('sec-websocket-protocol', request.headersList)

        // The client can request that the server use a specific subprotocol by
        // including the |Sec-WebSocket-Protocol| field in its handshake.  If it
        // is specified, the server needs to include the same field and one of
        // the selected subprotocol values in its response for the connection to
        // be established.
        if (!requestProtocols.includes(secProtocol)) {
          failWebsocketConnection(ws, 'Protocol was not set in the opening handshake.')
          return
        }
      }

      response.socket.on('data', onSocketData)
      response.socket.on('close', onSocketClose)
      response.socket.on('error', onSocketError)

      if (channels.open.hasSubscribers) {
        channels.open.publish({
          address: response.socket.address(),
          protocol: secProtocol,
          extensions: secExtension
        })
      }

      onEstablish(response, extensions)
    }
  })

  return controller
}

function closeWebSocketConnection (ws, code, reason, reasonByteLength) {
  if (isClosing(ws) || isClosed(ws)) {
    // If this's ready state is CLOSING (2) or CLOSED (3)
    // Do nothing.
  } else if (!isEstablished(ws)) {
    // If the WebSocket connection is not yet established
    // Fail the WebSocket connection and set this's ready state
    // to CLOSING (2).
    failWebsocketConnection(ws, 'Connection was closed before it was established.')
    ws[kReadyState] = states.CLOSING
  } else if (ws[kSentClose] === sentCloseFrameState.NOT_SENT) {
    // If the WebSocket closing handshake has not yet been started
    // Start the WebSocket closing handshake and set this's ready
    // state to CLOSING (2).
    // - If neither code nor reason is present, the WebSocket Close
    //   message must not have a body.
    // - If code is present, then the status code to use in the
    //   WebSocket Close message must be the integer given by code.
    // - If reason is also present, then reasonBytes must be
    //   provided in the Close message after the status code.

    ws[kSentClose] = sentCloseFrameState.PROCESSING

    const frame = new WebsocketFrameSend()

    // If neither code nor reason is present, the WebSocket Close
    // message must not have a body.

    // If code is present, then the status code to use in the
    // WebSocket Close message must be the integer given by code.
    if (code !== undefined && reason === undefined) {
      frame.frameData = Buffer.allocUnsafe(2)
      frame.frameData.writeUInt16BE(code, 0)
    } else if (code !== undefined && reason !== undefined) {
      // If reason is also present, then reasonBytes must be
      // provided in the Close message after the status code.
      frame.frameData = Buffer.allocUnsafe(2 + reasonByteLength)
      frame.frameData.writeUInt16BE(code, 0)
      // the body MAY contain UTF-8-encoded data with value /reason/
      frame.frameData.write(reason, 2, 'utf-8')
    } else {
      frame.frameData = emptyBuffer
    }

    /** @type {import('stream').Duplex} */
    const socket = ws[kResponse].socket

    socket.write(frame.createFrame(opcodes.CLOSE))

    ws[kSentClose] = sentCloseFrameState.SENT

    // Upon either sending or receiving a Close control frame, it is said
    // that _The WebSocket Closing Handshake is Started_ and that the
    // WebSocket connection is in the CLOSING state.
    ws[kReadyState] = states.CLOSING
  } else {
    // Otherwise
    // Set this's ready state to CLOSING (2).
    ws[kReadyState] = states.CLOSING
  }
}

/**
 * @param {Buffer} chunk
 */
function onSocketData (chunk) {
  if (!this.ws[kByteParser].write(chunk)) {
    this.pause()
  }
}

/**
 * @see https://websockets.spec.whatwg.org/#feedback-from-the-protocol
 * @see https://datatracker.ietf.org/doc/html/rfc6455#section-7.1.4
 */
function onSocketClose () {
  const { ws } = this
  const { [kResponse]: response } = ws

  response.socket.off('data', onSocketData)
  response.socket.off('close', onSocketClose)
  response.socket.off('error', onSocketError)

  // If the TCP connection was closed after the
  // WebSocket closing handshake was completed, the WebSocket connection
  // is said to have been closed _cleanly_.
  const wasClean = ws[kSentClose] === sentCloseFrameState.SENT && ws[kReceivedClose]

  let code = 1005
  let reason = ''

  const result = ws[kByteParser].closingInfo

  if (result && !result.error) {
    code = result.code ?? 1005
    reason = result.reason
  } else if (!ws[kReceivedClose]) {
    // If _The WebSocket
    // Connection is Closed_ and no Close control frame was received by the
    // endpoint (such as could occur if the underlying transport connection
    // is lost), _The WebSocket Connection Close Code_ is considered to be
    // 1006.
    code = 1006
  }

  // 1. Change the ready state to CLOSED (3).
  ws[kReadyState] = states.CLOSED

  // 2. If the user agent was required to fail the WebSocket
  //    connection, or if the WebSocket connection was closed
  //    after being flagged as full, fire an event named error
  //    at the WebSocket object.
  // TODO

  // 3. Fire an event named close at the WebSocket object,
  //    using CloseEvent, with the wasClean attribute
  //    initialized to true if the connection closed cleanly
  //    and false otherwise, the code attribute initialized to
  //    the WebSocket connection close code, and the reason
  //    attribute initialized to the result of applying UTF-8
  //    decode without BOM to the WebSocket connection close
  //    reason.
  // TODO: process.nextTick
  fireEvent('close', ws, (type, init) => new CloseEvent(type, init), {
    wasClean, code, reason
  })

  if (channels.close.hasSubscribers) {
    channels.close.publish({
      websocket: ws,
      code,
      reason
    })
  }
}

function onSocketError (error) {
  const { ws } = this

  ws[kReadyState] = states.CLOSING

  if (channels.socketError.hasSubscribers) {
    channels.socketError.publish(error)
  }

  this.destroy()
}

module.exports = {
  establishWebSocketConnection,
  closeWebSocketConnection
}


/***/ }),

/***/ 736:
/***/ ((module) => {



// This is a Globally Unique Identifier unique used
// to validate that the endpoint accepts websocket
// connections.
// See https://www.rfc-editor.org/rfc/rfc6455.html#section-1.3
const uid = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

/** @type {PropertyDescriptor} */
const staticPropertyDescriptors = {
  enumerable: true,
  writable: false,
  configurable: false
}

const states = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3
}

const sentCloseFrameState = {
  NOT_SENT: 0,
  PROCESSING: 1,
  SENT: 2
}

const opcodes = {
  CONTINUATION: 0x0,
  TEXT: 0x1,
  BINARY: 0x2,
  CLOSE: 0x8,
  PING: 0x9,
  PONG: 0xA
}

const maxUnsigned16Bit = 2 ** 16 - 1 // 65535

const parserStates = {
  INFO: 0,
  PAYLOADLENGTH_16: 2,
  PAYLOADLENGTH_64: 3,
  READ_DATA: 4
}

const emptyBuffer = Buffer.allocUnsafe(0)

const sendHints = {
  string: 1,
  typedArray: 2,
  arrayBuffer: 3,
  blob: 4
}

module.exports = {
  uid,
  sentCloseFrameState,
  staticPropertyDescriptors,
  states,
  opcodes,
  maxUnsigned16Bit,
  parserStates,
  emptyBuffer,
  sendHints
}


/***/ }),

/***/ 5188:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { webidl } = __nccwpck_require__(5893)
const { kEnumerableProperty } = __nccwpck_require__(3440)
const { kConstruct } = __nccwpck_require__(6443)
const { MessagePort } = __nccwpck_require__(5919)

/**
 * @see https://html.spec.whatwg.org/multipage/comms.html#messageevent
 */
class MessageEvent extends Event {
  #eventInit

  constructor (type, eventInitDict = {}) {
    if (type === kConstruct) {
      super(arguments[1], arguments[2])
      webidl.util.markAsUncloneable(this)
      return
    }

    const prefix = 'MessageEvent constructor'
    webidl.argumentLengthCheck(arguments, 1, prefix)

    type = webidl.converters.DOMString(type, prefix, 'type')
    eventInitDict = webidl.converters.MessageEventInit(eventInitDict, prefix, 'eventInitDict')

    super(type, eventInitDict)

    this.#eventInit = eventInitDict
    webidl.util.markAsUncloneable(this)
  }

  get data () {
    webidl.brandCheck(this, MessageEvent)

    return this.#eventInit.data
  }

  get origin () {
    webidl.brandCheck(this, MessageEvent)

    return this.#eventInit.origin
  }

  get lastEventId () {
    webidl.brandCheck(this, MessageEvent)

    return this.#eventInit.lastEventId
  }

  get source () {
    webidl.brandCheck(this, MessageEvent)

    return this.#eventInit.source
  }

  get ports () {
    webidl.brandCheck(this, MessageEvent)

    if (!Object.isFrozen(this.#eventInit.ports)) {
      Object.freeze(this.#eventInit.ports)
    }

    return this.#eventInit.ports
  }

  initMessageEvent (
    type,
    bubbles = false,
    cancelable = false,
    data = null,
    origin = '',
    lastEventId = '',
    source = null,
    ports = []
  ) {
    webidl.brandCheck(this, MessageEvent)

    webidl.argumentLengthCheck(arguments, 1, 'MessageEvent.initMessageEvent')

    return new MessageEvent(type, {
      bubbles, cancelable, data, origin, lastEventId, source, ports
    })
  }

  static createFastMessageEvent (type, init) {
    const messageEvent = new MessageEvent(kConstruct, type, init)
    messageEvent.#eventInit = init
    messageEvent.#eventInit.data ??= null
    messageEvent.#eventInit.origin ??= ''
    messageEvent.#eventInit.lastEventId ??= ''
    messageEvent.#eventInit.source ??= null
    messageEvent.#eventInit.ports ??= []
    return messageEvent
  }
}

const { createFastMessageEvent } = MessageEvent
delete MessageEvent.createFastMessageEvent

/**
 * @see https://websockets.spec.whatwg.org/#the-closeevent-interface
 */
class CloseEvent extends Event {
  #eventInit

  constructor (type, eventInitDict = {}) {
    const prefix = 'CloseEvent constructor'
    webidl.argumentLengthCheck(arguments, 1, prefix)

    type = webidl.converters.DOMString(type, prefix, 'type')
    eventInitDict = webidl.converters.CloseEventInit(eventInitDict)

    super(type, eventInitDict)

    this.#eventInit = eventInitDict
    webidl.util.markAsUncloneable(this)
  }

  get wasClean () {
    webidl.brandCheck(this, CloseEvent)

    return this.#eventInit.wasClean
  }

  get code () {
    webidl.brandCheck(this, CloseEvent)

    return this.#eventInit.code
  }

  get reason () {
    webidl.brandCheck(this, CloseEvent)

    return this.#eventInit.reason
  }
}

// https://html.spec.whatwg.org/multipage/webappapis.html#the-errorevent-interface
class ErrorEvent extends Event {
  #eventInit

  constructor (type, eventInitDict) {
    const prefix = 'ErrorEvent constructor'
    webidl.argumentLengthCheck(arguments, 1, prefix)

    super(type, eventInitDict)
    webidl.util.markAsUncloneable(this)

    type = webidl.converters.DOMString(type, prefix, 'type')
    eventInitDict = webidl.converters.ErrorEventInit(eventInitDict ?? {})

    this.#eventInit = eventInitDict
  }

  get message () {
    webidl.brandCheck(this, ErrorEvent)

    return this.#eventInit.message
  }

  get filename () {
    webidl.brandCheck(this, ErrorEvent)

    return this.#eventInit.filename
  }

  get lineno () {
    webidl.brandCheck(this, ErrorEvent)

    return this.#eventInit.lineno
  }

  get colno () {
    webidl.brandCheck(this, ErrorEvent)

    return this.#eventInit.colno
  }

  get error () {
    webidl.brandCheck(this, ErrorEvent)

    return this.#eventInit.error
  }
}

Object.defineProperties(MessageEvent.prototype, {
  [Symbol.toStringTag]: {
    value: 'MessageEvent',
    configurable: true
  },
  data: kEnumerableProperty,
  origin: kEnumerableProperty,
  lastEventId: kEnumerableProperty,
  source: kEnumerableProperty,
  ports: kEnumerableProperty,
  initMessageEvent: kEnumerableProperty
})

Object.defineProperties(CloseEvent.prototype, {
  [Symbol.toStringTag]: {
    value: 'CloseEvent',
    configurable: true
  },
  reason: kEnumerableProperty,
  code: kEnumerableProperty,
  wasClean: kEnumerableProperty
})

Object.defineProperties(ErrorEvent.prototype, {
  [Symbol.toStringTag]: {
    value: 'ErrorEvent',
    configurable: true
  },
  message: kEnumerableProperty,
  filename: kEnumerableProperty,
  lineno: kEnumerableProperty,
  colno: kEnumerableProperty,
  error: kEnumerableProperty
})

webidl.converters.MessagePort = webidl.interfaceConverter(MessagePort)

webidl.converters['sequence<MessagePort>'] = webidl.sequenceConverter(
  webidl.converters.MessagePort
)

const eventInit = [
  {
    key: 'bubbles',
    converter: webidl.converters.boolean,
    defaultValue: () => false
  },
  {
    key: 'cancelable',
    converter: webidl.converters.boolean,
    defaultValue: () => false
  },
  {
    key: 'composed',
    converter: webidl.converters.boolean,
    defaultValue: () => false
  }
]

webidl.converters.MessageEventInit = webidl.dictionaryConverter([
  ...eventInit,
  {
    key: 'data',
    converter: webidl.converters.any,
    defaultValue: () => null
  },
  {
    key: 'origin',
    converter: webidl.converters.USVString,
    defaultValue: () => ''
  },
  {
    key: 'lastEventId',
    converter: webidl.converters.DOMString,
    defaultValue: () => ''
  },
  {
    key: 'source',
    // Node doesn't implement WindowProxy or ServiceWorker, so the only
    // valid value for source is a MessagePort.
    converter: webidl.nullableConverter(webidl.converters.MessagePort),
    defaultValue: () => null
  },
  {
    key: 'ports',
    converter: webidl.converters['sequence<MessagePort>'],
    defaultValue: () => new Array(0)
  }
])

webidl.converters.CloseEventInit = webidl.dictionaryConverter([
  ...eventInit,
  {
    key: 'wasClean',
    converter: webidl.converters.boolean,
    defaultValue: () => false
  },
  {
    key: 'code',
    converter: webidl.converters['unsigned short'],
    defaultValue: () => 0
  },
  {
    key: 'reason',
    converter: webidl.converters.USVString,
    defaultValue: () => ''
  }
])

webidl.converters.ErrorEventInit = webidl.dictionaryConverter([
  ...eventInit,
  {
    key: 'message',
    converter: webidl.converters.DOMString,
    defaultValue: () => ''
  },
  {
    key: 'filename',
    converter: webidl.converters.USVString,
    defaultValue: () => ''
  },
  {
    key: 'lineno',
    converter: webidl.converters['unsigned long'],
    defaultValue: () => 0
  },
  {
    key: 'colno',
    converter: webidl.converters['unsigned long'],
    defaultValue: () => 0
  },
  {
    key: 'error',
    converter: webidl.converters.any
  }
])

module.exports = {
  MessageEvent,
  CloseEvent,
  ErrorEvent,
  createFastMessageEvent
}


/***/ }),

/***/ 3264:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { maxUnsigned16Bit } = __nccwpck_require__(736)

const BUFFER_SIZE = 16386

/** @type {import('crypto')} */
let crypto
let buffer = null
let bufIdx = BUFFER_SIZE

try {
  crypto = __nccwpck_require__(7598)
/* c8 ignore next 3 */
} catch {
  crypto = {
    // not full compatibility, but minimum.
    randomFillSync: function randomFillSync (buffer, _offset, _size) {
      for (let i = 0; i < buffer.length; ++i) {
        buffer[i] = Math.random() * 255 | 0
      }
      return buffer
    }
  }
}

function generateMask () {
  if (bufIdx === BUFFER_SIZE) {
    bufIdx = 0
    crypto.randomFillSync((buffer ??= Buffer.allocUnsafe(BUFFER_SIZE)), 0, BUFFER_SIZE)
  }
  return [buffer[bufIdx++], buffer[bufIdx++], buffer[bufIdx++], buffer[bufIdx++]]
}

class WebsocketFrameSend {
  /**
   * @param {Buffer|undefined} data
   */
  constructor (data) {
    this.frameData = data
  }

  createFrame (opcode) {
    const frameData = this.frameData
    const maskKey = generateMask()
    const bodyLength = frameData?.byteLength ?? 0

    /** @type {number} */
    let payloadLength = bodyLength // 0-125
    let offset = 6

    if (bodyLength > maxUnsigned16Bit) {
      offset += 8 // payload length is next 8 bytes
      payloadLength = 127
    } else if (bodyLength > 125) {
      offset += 2 // payload length is next 2 bytes
      payloadLength = 126
    }

    const buffer = Buffer.allocUnsafe(bodyLength + offset)

    // Clear first 2 bytes, everything else is overwritten
    buffer[0] = buffer[1] = 0
    buffer[0] |= 0x80 // FIN
    buffer[0] = (buffer[0] & 0xF0) + opcode // opcode

    /*! ws. MIT License. Einar Otto Stangvik <einaros@gmail.com> */
    buffer[offset - 4] = maskKey[0]
    buffer[offset - 3] = maskKey[1]
    buffer[offset - 2] = maskKey[2]
    buffer[offset - 1] = maskKey[3]

    buffer[1] = payloadLength

    if (payloadLength === 126) {
      buffer.writeUInt16BE(bodyLength, 2)
    } else if (payloadLength === 127) {
      // Clear extended payload length
      buffer[2] = buffer[3] = 0
      buffer.writeUIntBE(bodyLength, 4, 6)
    }

    buffer[1] |= 0x80 // MASK

    // mask body
    for (let i = 0; i < bodyLength; ++i) {
      buffer[offset + i] = frameData[i] ^ maskKey[i & 3]
    }

    return buffer
  }
}

module.exports = {
  WebsocketFrameSend
}


/***/ }),

/***/ 9469:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { createInflateRaw, Z_DEFAULT_WINDOWBITS } = __nccwpck_require__(8522)
const { isValidClientWindowBits } = __nccwpck_require__(8625)

const tail = Buffer.from([0x00, 0x00, 0xff, 0xff])
const kBuffer = Symbol('kBuffer')
const kLength = Symbol('kLength')

class PerMessageDeflate {
  /** @type {import('node:zlib').InflateRaw} */
  #inflate

  #options = {}

  constructor (extensions) {
    this.#options.serverNoContextTakeover = extensions.has('server_no_context_takeover')
    this.#options.serverMaxWindowBits = extensions.get('server_max_window_bits')
  }

  decompress (chunk, fin, callback) {
    // An endpoint uses the following algorithm to decompress a message.
    // 1.  Append 4 octets of 0x00 0x00 0xff 0xff to the tail end of the
    //     payload of the message.
    // 2.  Decompress the resulting data using DEFLATE.

    if (!this.#inflate) {
      let windowBits = Z_DEFAULT_WINDOWBITS

      if (this.#options.serverMaxWindowBits) { // empty values default to Z_DEFAULT_WINDOWBITS
        if (!isValidClientWindowBits(this.#options.serverMaxWindowBits)) {
          callback(new Error('Invalid server_max_window_bits'))
          return
        }

        windowBits = Number.parseInt(this.#options.serverMaxWindowBits)
      }

      this.#inflate = createInflateRaw({ windowBits })
      this.#inflate[kBuffer] = []
      this.#inflate[kLength] = 0

      this.#inflate.on('data', (data) => {
        this.#inflate[kBuffer].push(data)
        this.#inflate[kLength] += data.length
      })

      this.#inflate.on('error', (err) => {
        this.#inflate = null
        callback(err)
      })
    }

    this.#inflate.write(chunk)
    if (fin) {
      this.#inflate.write(tail)
    }

    this.#inflate.flush(() => {
      const full = Buffer.concat(this.#inflate[kBuffer], this.#inflate[kLength])

      this.#inflate[kBuffer].length = 0
      this.#inflate[kLength] = 0

      callback(null, full)
    })
  }
}

module.exports = { PerMessageDeflate }


/***/ }),

/***/ 1652:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { Writable } = __nccwpck_require__(7075)
const assert = __nccwpck_require__(4589)
const { parserStates, opcodes, states, emptyBuffer, sentCloseFrameState } = __nccwpck_require__(736)
const { kReadyState, kSentClose, kResponse, kReceivedClose } = __nccwpck_require__(1216)
const { channels } = __nccwpck_require__(2414)
const {
  isValidStatusCode,
  isValidOpcode,
  failWebsocketConnection,
  websocketMessageReceived,
  utf8Decode,
  isControlFrame,
  isTextBinaryFrame,
  isContinuationFrame
} = __nccwpck_require__(8625)
const { WebsocketFrameSend } = __nccwpck_require__(3264)
const { closeWebSocketConnection } = __nccwpck_require__(6897)
const { PerMessageDeflate } = __nccwpck_require__(9469)

// This code was influenced by ws released under the MIT license.
// Copyright (c) 2011 Einar Otto Stangvik <einaros@gmail.com>
// Copyright (c) 2013 Arnout Kazemier and contributors
// Copyright (c) 2016 Luigi Pinca and contributors

class ByteParser extends Writable {
  #buffers = []
  #byteOffset = 0
  #loop = false

  #state = parserStates.INFO

  #info = {}
  #fragments = []

  /** @type {Map<string, PerMessageDeflate>} */
  #extensions

  constructor (ws, extensions) {
    super()

    this.ws = ws
    this.#extensions = extensions == null ? new Map() : extensions

    if (this.#extensions.has('permessage-deflate')) {
      this.#extensions.set('permessage-deflate', new PerMessageDeflate(extensions))
    }
  }

  /**
   * @param {Buffer} chunk
   * @param {() => void} callback
   */
  _write (chunk, _, callback) {
    this.#buffers.push(chunk)
    this.#byteOffset += chunk.length
    this.#loop = true

    this.run(callback)
  }

  /**
   * Runs whenever a new chunk is received.
   * Callback is called whenever there are no more chunks buffering,
   * or not enough bytes are buffered to parse.
   */
  run (callback) {
    while (this.#loop) {
      if (this.#state === parserStates.INFO) {
        // If there aren't enough bytes to parse the payload length, etc.
        if (this.#byteOffset < 2) {
          return callback()
        }

        const buffer = this.consume(2)
        const fin = (buffer[0] & 0x80) !== 0
        const opcode = buffer[0] & 0x0F
        const masked = (buffer[1] & 0x80) === 0x80

        const fragmented = !fin && opcode !== opcodes.CONTINUATION
        const payloadLength = buffer[1] & 0x7F

        const rsv1 = buffer[0] & 0x40
        const rsv2 = buffer[0] & 0x20
        const rsv3 = buffer[0] & 0x10

        if (!isValidOpcode(opcode)) {
          failWebsocketConnection(this.ws, 'Invalid opcode received')
          return callback()
        }

        if (masked) {
          failWebsocketConnection(this.ws, 'Frame cannot be masked')
          return callback()
        }

        // MUST be 0 unless an extension is negotiated that defines meanings
        // for non-zero values.  If a nonzero value is received and none of
        // the negotiated extensions defines the meaning of such a nonzero
        // value, the receiving endpoint MUST _Fail the WebSocket
        // Connection_.
        // This document allocates the RSV1 bit of the WebSocket header for
        // PMCEs and calls the bit the "Per-Message Compressed" bit.  On a
        // WebSocket connection where a PMCE is in use, this bit indicates
        // whether a message is compressed or not.
        if (rsv1 !== 0 && !this.#extensions.has('permessage-deflate')) {
          failWebsocketConnection(this.ws, 'Expected RSV1 to be clear.')
          return
        }

        if (rsv2 !== 0 || rsv3 !== 0) {
          failWebsocketConnection(this.ws, 'RSV1, RSV2, RSV3 must be clear')
          return
        }

        if (fragmented && !isTextBinaryFrame(opcode)) {
          // Only text and binary frames can be fragmented
          failWebsocketConnection(this.ws, 'Invalid frame type was fragmented.')
          return
        }

        // If we are already parsing a text/binary frame and do not receive either
        // a continuation frame or close frame, fail the connection.
        if (isTextBinaryFrame(opcode) && this.#fragments.length > 0) {
          failWebsocketConnection(this.ws, 'Expected continuation frame')
          return
        }

        if (this.#info.fragmented && fragmented) {
          // A fragmented frame can't be fragmented itself
          failWebsocketConnection(this.ws, 'Fragmented frame exceeded 125 bytes.')
          return
        }

        // "All control frames MUST have a payload length of 125 bytes or less
        // and MUST NOT be fragmented."
        if ((payloadLength > 125 || fragmented) && isControlFrame(opcode)) {
          failWebsocketConnection(this.ws, 'Control frame either too large or fragmented')
          return
        }

        if (isContinuationFrame(opcode) && this.#fragments.length === 0 && !this.#info.compressed) {
          failWebsocketConnection(this.ws, 'Unexpected continuation frame')
          return
        }

        if (payloadLength <= 125) {
          this.#info.payloadLength = payloadLength
          this.#state = parserStates.READ_DATA
        } else if (payloadLength === 126) {
          this.#state = parserStates.PAYLOADLENGTH_16
        } else if (payloadLength === 127) {
          this.#state = parserStates.PAYLOADLENGTH_64
        }

        if (isTextBinaryFrame(opcode)) {
          this.#info.binaryType = opcode
          this.#info.compressed = rsv1 !== 0
        }

        this.#info.opcode = opcode
        this.#info.masked = masked
        this.#info.fin = fin
        this.#info.fragmented = fragmented
      } else if (this.#state === parserStates.PAYLOADLENGTH_16) {
        if (this.#byteOffset < 2) {
          return callback()
        }

        const buffer = this.consume(2)

        this.#info.payloadLength = buffer.readUInt16BE(0)
        this.#state = parserStates.READ_DATA
      } else if (this.#state === parserStates.PAYLOADLENGTH_64) {
        if (this.#byteOffset < 8) {
          return callback()
        }

        const buffer = this.consume(8)
        const upper = buffer.readUInt32BE(0)

        // 2^31 is the maximum bytes an arraybuffer can contain
        // on 32-bit systems. Although, on 64-bit systems, this is
        // 2^53-1 bytes.
        // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Errors/Invalid_array_length
        // https://source.chromium.org/chromium/chromium/src/+/main:v8/src/common/globals.h;drc=1946212ac0100668f14eb9e2843bdd846e510a1e;bpv=1;bpt=1;l=1275
        // https://source.chromium.org/chromium/chromium/src/+/main:v8/src/objects/js-array-buffer.h;l=34;drc=1946212ac0100668f14eb9e2843bdd846e510a1e
        if (upper > 2 ** 31 - 1) {
          failWebsocketConnection(this.ws, 'Received payload length > 2^31 bytes.')
          return
        }

        const lower = buffer.readUInt32BE(4)

        this.#info.payloadLength = (upper << 8) + lower
        this.#state = parserStates.READ_DATA
      } else if (this.#state === parserStates.READ_DATA) {
        if (this.#byteOffset < this.#info.payloadLength) {
          return callback()
        }

        const body = this.consume(this.#info.payloadLength)

        if (isControlFrame(this.#info.opcode)) {
          this.#loop = this.parseControlFrame(body)
          this.#state = parserStates.INFO
        } else {
          if (!this.#info.compressed) {
            this.#fragments.push(body)

            // If the frame is not fragmented, a message has been received.
            // If the frame is fragmented, it will terminate with a fin bit set
            // and an opcode of 0 (continuation), therefore we handle that when
            // parsing continuation frames, not here.
            if (!this.#info.fragmented && this.#info.fin) {
              const fullMessage = Buffer.concat(this.#fragments)
              websocketMessageReceived(this.ws, this.#info.binaryType, fullMessage)
              this.#fragments.length = 0
            }

            this.#state = parserStates.INFO
          } else {
            this.#extensions.get('permessage-deflate').decompress(body, this.#info.fin, (error, data) => {
              if (error) {
                closeWebSocketConnection(this.ws, 1007, error.message, error.message.length)
                return
              }

              this.#fragments.push(data)

              if (!this.#info.fin) {
                this.#state = parserStates.INFO
                this.#loop = true
                this.run(callback)
                return
              }

              websocketMessageReceived(this.ws, this.#info.binaryType, Buffer.concat(this.#fragments))

              this.#loop = true
              this.#state = parserStates.INFO
              this.#fragments.length = 0
              this.run(callback)
            })

            this.#loop = false
            break
          }
        }
      }
    }
  }

  /**
   * Take n bytes from the buffered Buffers
   * @param {number} n
   * @returns {Buffer}
   */
  consume (n) {
    if (n > this.#byteOffset) {
      throw new Error('Called consume() before buffers satiated.')
    } else if (n === 0) {
      return emptyBuffer
    }

    if (this.#buffers[0].length === n) {
      this.#byteOffset -= this.#buffers[0].length
      return this.#buffers.shift()
    }

    const buffer = Buffer.allocUnsafe(n)
    let offset = 0

    while (offset !== n) {
      const next = this.#buffers[0]
      const { length } = next

      if (length + offset === n) {
        buffer.set(this.#buffers.shift(), offset)
        break
      } else if (length + offset > n) {
        buffer.set(next.subarray(0, n - offset), offset)
        this.#buffers[0] = next.subarray(n - offset)
        break
      } else {
        buffer.set(this.#buffers.shift(), offset)
        offset += next.length
      }
    }

    this.#byteOffset -= n

    return buffer
  }

  parseCloseBody (data) {
    assert(data.length !== 1)

    // https://datatracker.ietf.org/doc/html/rfc6455#section-7.1.5
    /** @type {number|undefined} */
    let code

    if (data.length >= 2) {
      // _The WebSocket Connection Close Code_ is
      // defined as the status code (Section 7.4) contained in the first Close
      // control frame received by the application
      code = data.readUInt16BE(0)
    }

    if (code !== undefined && !isValidStatusCode(code)) {
      return { code: 1002, reason: 'Invalid status code', error: true }
    }

    // https://datatracker.ietf.org/doc/html/rfc6455#section-7.1.6
    /** @type {Buffer} */
    let reason = data.subarray(2)

    // Remove BOM
    if (reason[0] === 0xEF && reason[1] === 0xBB && reason[2] === 0xBF) {
      reason = reason.subarray(3)
    }

    try {
      reason = utf8Decode(reason)
    } catch {
      return { code: 1007, reason: 'Invalid UTF-8', error: true }
    }

    return { code, reason, error: false }
  }

  /**
   * Parses control frames.
   * @param {Buffer} body
   */
  parseControlFrame (body) {
    const { opcode, payloadLength } = this.#info

    if (opcode === opcodes.CLOSE) {
      if (payloadLength === 1) {
        failWebsocketConnection(this.ws, 'Received close frame with a 1-byte body.')
        return false
      }

      this.#info.closeInfo = this.parseCloseBody(body)

      if (this.#info.closeInfo.error) {
        const { code, reason } = this.#info.closeInfo

        closeWebSocketConnection(this.ws, code, reason, reason.length)
        failWebsocketConnection(this.ws, reason)
        return false
      }

      if (this.ws[kSentClose] !== sentCloseFrameState.SENT) {
        // If an endpoint receives a Close frame and did not previously send a
        // Close frame, the endpoint MUST send a Close frame in response.  (When
        // sending a Close frame in response, the endpoint typically echos the
        // status code it received.)
        let body = emptyBuffer
        if (this.#info.closeInfo.code) {
          body = Buffer.allocUnsafe(2)
          body.writeUInt16BE(this.#info.closeInfo.code, 0)
        }
        const closeFrame = new WebsocketFrameSend(body)

        this.ws[kResponse].socket.write(
          closeFrame.createFrame(opcodes.CLOSE),
          (err) => {
            if (!err) {
              this.ws[kSentClose] = sentCloseFrameState.SENT
            }
          }
        )
      }

      // Upon either sending or receiving a Close control frame, it is said
      // that _The WebSocket Closing Handshake is Started_ and that the
      // WebSocket connection is in the CLOSING state.
      this.ws[kReadyState] = states.CLOSING
      this.ws[kReceivedClose] = true

      return false
    } else if (opcode === opcodes.PING) {
      // Upon receipt of a Ping frame, an endpoint MUST send a Pong frame in
      // response, unless it already received a Close frame.
      // A Pong frame sent in response to a Ping frame must have identical
      // "Application data"

      if (!this.ws[kReceivedClose]) {
        const frame = new WebsocketFrameSend(body)

        this.ws[kResponse].socket.write(frame.createFrame(opcodes.PONG))

        if (channels.ping.hasSubscribers) {
          channels.ping.publish({
            payload: body
          })
        }
      }
    } else if (opcode === opcodes.PONG) {
      // A Pong frame MAY be sent unsolicited.  This serves as a
      // unidirectional heartbeat.  A response to an unsolicited Pong frame is
      // not expected.

      if (channels.pong.hasSubscribers) {
        channels.pong.publish({
          payload: body
        })
      }
    }

    return true
  }

  get closingInfo () {
    return this.#info.closeInfo
  }
}

module.exports = {
  ByteParser
}


/***/ }),

/***/ 3900:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { WebsocketFrameSend } = __nccwpck_require__(3264)
const { opcodes, sendHints } = __nccwpck_require__(736)
const FixedQueue = __nccwpck_require__(4660)

/** @type {typeof Uint8Array} */
const FastBuffer = Buffer[Symbol.species]

/**
 * @typedef {object} SendQueueNode
 * @property {Promise<void> | null} promise
 * @property {((...args: any[]) => any)} callback
 * @property {Buffer | null} frame
 */

class SendQueue {
  /**
   * @type {FixedQueue}
   */
  #queue = new FixedQueue()

  /**
   * @type {boolean}
   */
  #running = false

  /** @type {import('node:net').Socket} */
  #socket

  constructor (socket) {
    this.#socket = socket
  }

  add (item, cb, hint) {
    if (hint !== sendHints.blob) {
      const frame = createFrame(item, hint)
      if (!this.#running) {
        // fast-path
        this.#socket.write(frame, cb)
      } else {
        /** @type {SendQueueNode} */
        const node = {
          promise: null,
          callback: cb,
          frame
        }
        this.#queue.push(node)
      }
      return
    }

    /** @type {SendQueueNode} */
    const node = {
      promise: item.arrayBuffer().then((ab) => {
        node.promise = null
        node.frame = createFrame(ab, hint)
      }),
      callback: cb,
      frame: null
    }

    this.#queue.push(node)

    if (!this.#running) {
      this.#run()
    }
  }

  async #run () {
    this.#running = true
    const queue = this.#queue
    while (!queue.isEmpty()) {
      const node = queue.shift()
      // wait pending promise
      if (node.promise !== null) {
        await node.promise
      }
      // write
      this.#socket.write(node.frame, node.callback)
      // cleanup
      node.callback = node.frame = null
    }
    this.#running = false
  }
}

function createFrame (data, hint) {
  return new WebsocketFrameSend(toBuffer(data, hint)).createFrame(hint === sendHints.string ? opcodes.TEXT : opcodes.BINARY)
}

function toBuffer (data, hint) {
  switch (hint) {
    case sendHints.string:
      return Buffer.from(data)
    case sendHints.arrayBuffer:
    case sendHints.blob:
      return new FastBuffer(data)
    case sendHints.typedArray:
      return new FastBuffer(data.buffer, data.byteOffset, data.byteLength)
  }
}

module.exports = { SendQueue }


/***/ }),

/***/ 1216:
/***/ ((module) => {



module.exports = {
  kWebSocketURL: Symbol('url'),
  kReadyState: Symbol('ready state'),
  kController: Symbol('controller'),
  kResponse: Symbol('response'),
  kBinaryType: Symbol('binary type'),
  kSentClose: Symbol('sent close'),
  kReceivedClose: Symbol('received close'),
  kByteParser: Symbol('byte parser')
}


/***/ }),

/***/ 8625:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { kReadyState, kController, kResponse, kBinaryType, kWebSocketURL } = __nccwpck_require__(1216)
const { states, opcodes } = __nccwpck_require__(736)
const { ErrorEvent, createFastMessageEvent } = __nccwpck_require__(5188)
const { isUtf8 } = __nccwpck_require__(4573)
const { collectASequenceOfCodePointsFast, removeHTTPWhitespace } = __nccwpck_require__(1900)

/* globals Blob */

/**
 * @param {import('./websocket').WebSocket} ws
 * @returns {boolean}
 */
function isConnecting (ws) {
  // If the WebSocket connection is not yet established, and the connection
  // is not yet closed, then the WebSocket connection is in the CONNECTING state.
  return ws[kReadyState] === states.CONNECTING
}

/**
 * @param {import('./websocket').WebSocket} ws
 * @returns {boolean}
 */
function isEstablished (ws) {
  // If the server's response is validated as provided for above, it is
  // said that _The WebSocket Connection is Established_ and that the
  // WebSocket Connection is in the OPEN state.
  return ws[kReadyState] === states.OPEN
}

/**
 * @param {import('./websocket').WebSocket} ws
 * @returns {boolean}
 */
function isClosing (ws) {
  // Upon either sending or receiving a Close control frame, it is said
  // that _The WebSocket Closing Handshake is Started_ and that the
  // WebSocket connection is in the CLOSING state.
  return ws[kReadyState] === states.CLOSING
}

/**
 * @param {import('./websocket').WebSocket} ws
 * @returns {boolean}
 */
function isClosed (ws) {
  return ws[kReadyState] === states.CLOSED
}

/**
 * @see https://dom.spec.whatwg.org/#concept-event-fire
 * @param {string} e
 * @param {EventTarget} target
 * @param {(...args: ConstructorParameters<typeof Event>) => Event} eventFactory
 * @param {EventInit | undefined} eventInitDict
 */
function fireEvent (e, target, eventFactory = (type, init) => new Event(type, init), eventInitDict = {}) {
  // 1. If eventConstructor is not given, then let eventConstructor be Event.

  // 2. Let event be the result of creating an event given eventConstructor,
  //    in the relevant realm of target.
  // 3. Initialize event’s type attribute to e.
  const event = eventFactory(e, eventInitDict)

  // 4. Initialize any other IDL attributes of event as described in the
  //    invocation of this algorithm.

  // 5. Return the result of dispatching event at target, with legacy target
  //    override flag set if set.
  target.dispatchEvent(event)
}

/**
 * @see https://websockets.spec.whatwg.org/#feedback-from-the-protocol
 * @param {import('./websocket').WebSocket} ws
 * @param {number} type Opcode
 * @param {Buffer} data application data
 */
function websocketMessageReceived (ws, type, data) {
  // 1. If ready state is not OPEN (1), then return.
  if (ws[kReadyState] !== states.OPEN) {
    return
  }

  // 2. Let dataForEvent be determined by switching on type and binary type:
  let dataForEvent

  if (type === opcodes.TEXT) {
    // -> type indicates that the data is Text
    //      a new DOMString containing data
    try {
      dataForEvent = utf8Decode(data)
    } catch {
      failWebsocketConnection(ws, 'Received invalid UTF-8 in text frame.')
      return
    }
  } else if (type === opcodes.BINARY) {
    if (ws[kBinaryType] === 'blob') {
      // -> type indicates that the data is Binary and binary type is "blob"
      //      a new Blob object, created in the relevant Realm of the WebSocket
      //      object, that represents data as its raw data
      dataForEvent = new Blob([data])
    } else {
      // -> type indicates that the data is Binary and binary type is "arraybuffer"
      //      a new ArrayBuffer object, created in the relevant Realm of the
      //      WebSocket object, whose contents are data
      dataForEvent = toArrayBuffer(data)
    }
  }

  // 3. Fire an event named message at the WebSocket object, using MessageEvent,
  //    with the origin attribute initialized to the serialization of the WebSocket
  //    object’s url's origin, and the data attribute initialized to dataForEvent.
  fireEvent('message', ws, createFastMessageEvent, {
    origin: ws[kWebSocketURL].origin,
    data: dataForEvent
  })
}

function toArrayBuffer (buffer) {
  if (buffer.byteLength === buffer.buffer.byteLength) {
    return buffer.buffer
  }
  return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength)
}

/**
 * @see https://datatracker.ietf.org/doc/html/rfc6455
 * @see https://datatracker.ietf.org/doc/html/rfc2616
 * @see https://bugs.chromium.org/p/chromium/issues/detail?id=398407
 * @param {string} protocol
 */
function isValidSubprotocol (protocol) {
  // If present, this value indicates one
  // or more comma-separated subprotocol the client wishes to speak,
  // ordered by preference.  The elements that comprise this value
  // MUST be non-empty strings with characters in the range U+0021 to
  // U+007E not including separator characters as defined in
  // [RFC2616] and MUST all be unique strings.
  if (protocol.length === 0) {
    return false
  }

  for (let i = 0; i < protocol.length; ++i) {
    const code = protocol.charCodeAt(i)

    if (
      code < 0x21 || // CTL, contains SP (0x20) and HT (0x09)
      code > 0x7E ||
      code === 0x22 || // "
      code === 0x28 || // (
      code === 0x29 || // )
      code === 0x2C || // ,
      code === 0x2F || // /
      code === 0x3A || // :
      code === 0x3B || // ;
      code === 0x3C || // <
      code === 0x3D || // =
      code === 0x3E || // >
      code === 0x3F || // ?
      code === 0x40 || // @
      code === 0x5B || // [
      code === 0x5C || // \
      code === 0x5D || // ]
      code === 0x7B || // {
      code === 0x7D // }
    ) {
      return false
    }
  }

  return true
}

/**
 * @see https://datatracker.ietf.org/doc/html/rfc6455#section-7-4
 * @param {number} code
 */
function isValidStatusCode (code) {
  if (code >= 1000 && code < 1015) {
    return (
      code !== 1004 && // reserved
      code !== 1005 && // "MUST NOT be set as a status code"
      code !== 1006 // "MUST NOT be set as a status code"
    )
  }

  return code >= 3000 && code <= 4999
}

/**
 * @param {import('./websocket').WebSocket} ws
 * @param {string|undefined} reason
 */
function failWebsocketConnection (ws, reason) {
  const { [kController]: controller, [kResponse]: response } = ws

  controller.abort()

  if (response?.socket && !response.socket.destroyed) {
    response.socket.destroy()
  }

  if (reason) {
    // TODO: process.nextTick
    fireEvent('error', ws, (type, init) => new ErrorEvent(type, init), {
      error: new Error(reason),
      message: reason
    })
  }
}

/**
 * @see https://datatracker.ietf.org/doc/html/rfc6455#section-5.5
 * @param {number} opcode
 */
function isControlFrame (opcode) {
  return (
    opcode === opcodes.CLOSE ||
    opcode === opcodes.PING ||
    opcode === opcodes.PONG
  )
}

function isContinuationFrame (opcode) {
  return opcode === opcodes.CONTINUATION
}

function isTextBinaryFrame (opcode) {
  return opcode === opcodes.TEXT || opcode === opcodes.BINARY
}

function isValidOpcode (opcode) {
  return isTextBinaryFrame(opcode) || isContinuationFrame(opcode) || isControlFrame(opcode)
}

/**
 * Parses a Sec-WebSocket-Extensions header value.
 * @param {string} extensions
 * @returns {Map<string, string>}
 */
// TODO(@Uzlopak, @KhafraDev): make compliant https://datatracker.ietf.org/doc/html/rfc6455#section-9.1
function parseExtensions (extensions) {
  const position = { position: 0 }
  const extensionList = new Map()

  while (position.position < extensions.length) {
    const pair = collectASequenceOfCodePointsFast(';', extensions, position)
    const [name, value = ''] = pair.split('=')

    extensionList.set(
      removeHTTPWhitespace(name, true, false),
      removeHTTPWhitespace(value, false, true)
    )

    position.position++
  }

  return extensionList
}

/**
 * @see https://www.rfc-editor.org/rfc/rfc7692#section-7.1.2.2
 * @description "client-max-window-bits = 1*DIGIT"
 * @param {string} value
 */
function isValidClientWindowBits (value) {
  for (let i = 0; i < value.length; i++) {
    const byte = value.charCodeAt(i)

    if (byte < 0x30 || byte > 0x39) {
      return false
    }
  }

  return true
}

// https://nodejs.org/api/intl.html#detecting-internationalization-support
const hasIntl = typeof process.versions.icu === 'string'
const fatalDecoder = hasIntl ? new TextDecoder('utf-8', { fatal: true }) : undefined

/**
 * Converts a Buffer to utf-8, even on platforms without icu.
 * @param {Buffer} buffer
 */
const utf8Decode = hasIntl
  ? fatalDecoder.decode.bind(fatalDecoder)
  : function (buffer) {
    if (isUtf8(buffer)) {
      return buffer.toString('utf-8')
    }
    throw new TypeError('Invalid utf-8 received.')
  }

module.exports = {
  isConnecting,
  isEstablished,
  isClosing,
  isClosed,
  fireEvent,
  isValidSubprotocol,
  isValidStatusCode,
  failWebsocketConnection,
  websocketMessageReceived,
  utf8Decode,
  isControlFrame,
  isContinuationFrame,
  isTextBinaryFrame,
  isValidOpcode,
  parseExtensions,
  isValidClientWindowBits
}


/***/ }),

/***/ 3726:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



const { webidl } = __nccwpck_require__(5893)
const { URLSerializer } = __nccwpck_require__(1900)
const { environmentSettingsObject } = __nccwpck_require__(3168)
const { staticPropertyDescriptors, states, sentCloseFrameState, sendHints } = __nccwpck_require__(736)
const {
  kWebSocketURL,
  kReadyState,
  kController,
  kBinaryType,
  kResponse,
  kSentClose,
  kByteParser
} = __nccwpck_require__(1216)
const {
  isConnecting,
  isEstablished,
  isClosing,
  isValidSubprotocol,
  fireEvent
} = __nccwpck_require__(8625)
const { establishWebSocketConnection, closeWebSocketConnection } = __nccwpck_require__(6897)
const { ByteParser } = __nccwpck_require__(1652)
const { kEnumerableProperty, isBlobLike } = __nccwpck_require__(3440)
const { getGlobalDispatcher } = __nccwpck_require__(2581)
const { types } = __nccwpck_require__(7975)
const { ErrorEvent, CloseEvent } = __nccwpck_require__(5188)
const { SendQueue } = __nccwpck_require__(3900)

// https://websockets.spec.whatwg.org/#interface-definition
class WebSocket extends EventTarget {
  #events = {
    open: null,
    error: null,
    close: null,
    message: null
  }

  #bufferedAmount = 0
  #protocol = ''
  #extensions = ''

  /** @type {SendQueue} */
  #sendQueue

  /**
   * @param {string} url
   * @param {string|string[]} protocols
   */
  constructor (url, protocols = []) {
    super()

    webidl.util.markAsUncloneable(this)

    const prefix = 'WebSocket constructor'
    webidl.argumentLengthCheck(arguments, 1, prefix)

    const options = webidl.converters['DOMString or sequence<DOMString> or WebSocketInit'](protocols, prefix, 'options')

    url = webidl.converters.USVString(url, prefix, 'url')
    protocols = options.protocols

    // 1. Let baseURL be this's relevant settings object's API base URL.
    const baseURL = environmentSettingsObject.settingsObject.baseUrl

    // 1. Let urlRecord be the result of applying the URL parser to url with baseURL.
    let urlRecord

    try {
      urlRecord = new URL(url, baseURL)
    } catch (e) {
      // 3. If urlRecord is failure, then throw a "SyntaxError" DOMException.
      throw new DOMException(e, 'SyntaxError')
    }

    // 4. If urlRecord’s scheme is "http", then set urlRecord’s scheme to "ws".
    if (urlRecord.protocol === 'http:') {
      urlRecord.protocol = 'ws:'
    } else if (urlRecord.protocol === 'https:') {
      // 5. Otherwise, if urlRecord’s scheme is "https", set urlRecord’s scheme to "wss".
      urlRecord.protocol = 'wss:'
    }

    // 6. If urlRecord’s scheme is not "ws" or "wss", then throw a "SyntaxError" DOMException.
    if (urlRecord.protocol !== 'ws:' && urlRecord.protocol !== 'wss:') {
      throw new DOMException(
        `Expected a ws: or wss: protocol, got ${urlRecord.protocol}`,
        'SyntaxError'
      )
    }

    // 7. If urlRecord’s fragment is non-null, then throw a "SyntaxError"
    //    DOMException.
    if (urlRecord.hash || urlRecord.href.endsWith('#')) {
      throw new DOMException('Got fragment', 'SyntaxError')
    }

    // 8. If protocols is a string, set protocols to a sequence consisting
    //    of just that string.
    if (typeof protocols === 'string') {
      protocols = [protocols]
    }

    // 9. If any of the values in protocols occur more than once or otherwise
    //    fail to match the requirements for elements that comprise the value
    //    of `Sec-WebSocket-Protocol` fields as defined by The WebSocket
    //    protocol, then throw a "SyntaxError" DOMException.
    if (protocols.length !== new Set(protocols.map(p => p.toLowerCase())).size) {
      throw new DOMException('Invalid Sec-WebSocket-Protocol value', 'SyntaxError')
    }

    if (protocols.length > 0 && !protocols.every(p => isValidSubprotocol(p))) {
      throw new DOMException('Invalid Sec-WebSocket-Protocol value', 'SyntaxError')
    }

    // 10. Set this's url to urlRecord.
    this[kWebSocketURL] = new URL(urlRecord.href)

    // 11. Let client be this's relevant settings object.
    const client = environmentSettingsObject.settingsObject

    // 12. Run this step in parallel:

    //    1. Establish a WebSocket connection given urlRecord, protocols,
    //       and client.
    this[kController] = establishWebSocketConnection(
      urlRecord,
      protocols,
      client,
      this,
      (response, extensions) => this.#onConnectionEstablished(response, extensions),
      options
    )

    // Each WebSocket object has an associated ready state, which is a
    // number representing the state of the connection. Initially it must
    // be CONNECTING (0).
    this[kReadyState] = WebSocket.CONNECTING

    this[kSentClose] = sentCloseFrameState.NOT_SENT

    // The extensions attribute must initially return the empty string.

    // The protocol attribute must initially return the empty string.

    // Each WebSocket object has an associated binary type, which is a
    // BinaryType. Initially it must be "blob".
    this[kBinaryType] = 'blob'
  }

  /**
   * @see https://websockets.spec.whatwg.org/#dom-websocket-close
   * @param {number|undefined} code
   * @param {string|undefined} reason
   */
  close (code = undefined, reason = undefined) {
    webidl.brandCheck(this, WebSocket)

    const prefix = 'WebSocket.close'

    if (code !== undefined) {
      code = webidl.converters['unsigned short'](code, prefix, 'code', { clamp: true })
    }

    if (reason !== undefined) {
      reason = webidl.converters.USVString(reason, prefix, 'reason')
    }

    // 1. If code is present, but is neither an integer equal to 1000 nor an
    //    integer in the range 3000 to 4999, inclusive, throw an
    //    "InvalidAccessError" DOMException.
    if (code !== undefined) {
      if (code !== 1000 && (code < 3000 || code > 4999)) {
        throw new DOMException('invalid code', 'InvalidAccessError')
      }
    }

    let reasonByteLength = 0

    // 2. If reason is present, then run these substeps:
    if (reason !== undefined) {
      // 1. Let reasonBytes be the result of encoding reason.
      // 2. If reasonBytes is longer than 123 bytes, then throw a
      //    "SyntaxError" DOMException.
      reasonByteLength = Buffer.byteLength(reason)

      if (reasonByteLength > 123) {
        throw new DOMException(
          `Reason must be less than 123 bytes; received ${reasonByteLength}`,
          'SyntaxError'
        )
      }
    }

    // 3. Run the first matching steps from the following list:
    closeWebSocketConnection(this, code, reason, reasonByteLength)
  }

  /**
   * @see https://websockets.spec.whatwg.org/#dom-websocket-send
   * @param {NodeJS.TypedArray|ArrayBuffer|Blob|string} data
   */
  send (data) {
    webidl.brandCheck(this, WebSocket)

    const prefix = 'WebSocket.send'
    webidl.argumentLengthCheck(arguments, 1, prefix)

    data = webidl.converters.WebSocketSendData(data, prefix, 'data')

    // 1. If this's ready state is CONNECTING, then throw an
    //    "InvalidStateError" DOMException.
    if (isConnecting(this)) {
      throw new DOMException('Sent before connected.', 'InvalidStateError')
    }

    // 2. Run the appropriate set of steps from the following list:
    // https://datatracker.ietf.org/doc/html/rfc6455#section-6.1
    // https://datatracker.ietf.org/doc/html/rfc6455#section-5.2

    if (!isEstablished(this) || isClosing(this)) {
      return
    }

    // If data is a string
    if (typeof data === 'string') {
      // If the WebSocket connection is established and the WebSocket
      // closing handshake has not yet started, then the user agent
      // must send a WebSocket Message comprised of the data argument
      // using a text frame opcode; if the data cannot be sent, e.g.
      // because it would need to be buffered but the buffer is full,
      // the user agent must flag the WebSocket as full and then close
      // the WebSocket connection. Any invocation of this method with a
      // string argument that does not throw an exception must increase
      // the bufferedAmount attribute by the number of bytes needed to
      // express the argument as UTF-8.

      const length = Buffer.byteLength(data)

      this.#bufferedAmount += length
      this.#sendQueue.add(data, () => {
        this.#bufferedAmount -= length
      }, sendHints.string)
    } else if (types.isArrayBuffer(data)) {
      // If the WebSocket connection is established, and the WebSocket
      // closing handshake has not yet started, then the user agent must
      // send a WebSocket Message comprised of data using a binary frame
      // opcode; if the data cannot be sent, e.g. because it would need
      // to be buffered but the buffer is full, the user agent must flag
      // the WebSocket as full and then close the WebSocket connection.
      // The data to be sent is the data stored in the buffer described
      // by the ArrayBuffer object. Any invocation of this method with an
      // ArrayBuffer argument that does not throw an exception must
      // increase the bufferedAmount attribute by the length of the
      // ArrayBuffer in bytes.

      this.#bufferedAmount += data.byteLength
      this.#sendQueue.add(data, () => {
        this.#bufferedAmount -= data.byteLength
      }, sendHints.arrayBuffer)
    } else if (ArrayBuffer.isView(data)) {
      // If the WebSocket connection is established, and the WebSocket
      // closing handshake has not yet started, then the user agent must
      // send a WebSocket Message comprised of data using a binary frame
      // opcode; if the data cannot be sent, e.g. because it would need to
      // be buffered but the buffer is full, the user agent must flag the
      // WebSocket as full and then close the WebSocket connection. The
      // data to be sent is the data stored in the section of the buffer
      // described by the ArrayBuffer object that data references. Any
      // invocation of this method with this kind of argument that does
      // not throw an exception must increase the bufferedAmount attribute
      // by the length of data’s buffer in bytes.

      this.#bufferedAmount += data.byteLength
      this.#sendQueue.add(data, () => {
        this.#bufferedAmount -= data.byteLength
      }, sendHints.typedArray)
    } else if (isBlobLike(data)) {
      // If the WebSocket connection is established, and the WebSocket
      // closing handshake has not yet started, then the user agent must
      // send a WebSocket Message comprised of data using a binary frame
      // opcode; if the data cannot be sent, e.g. because it would need to
      // be buffered but the buffer is full, the user agent must flag the
      // WebSocket as full and then close the WebSocket connection. The data
      // to be sent is the raw data represented by the Blob object. Any
      // invocation of this method with a Blob argument that does not throw
      // an exception must increase the bufferedAmount attribute by the size
      // of the Blob object’s raw data, in bytes.

      this.#bufferedAmount += data.size
      this.#sendQueue.add(data, () => {
        this.#bufferedAmount -= data.size
      }, sendHints.blob)
    }
  }

  get readyState () {
    webidl.brandCheck(this, WebSocket)

    // The readyState getter steps are to return this's ready state.
    return this[kReadyState]
  }

  get bufferedAmount () {
    webidl.brandCheck(this, WebSocket)

    return this.#bufferedAmount
  }

  get url () {
    webidl.brandCheck(this, WebSocket)

    // The url getter steps are to return this's url, serialized.
    return URLSerializer(this[kWebSocketURL])
  }

  get extensions () {
    webidl.brandCheck(this, WebSocket)

    return this.#extensions
  }

  get protocol () {
    webidl.brandCheck(this, WebSocket)

    return this.#protocol
  }

  get onopen () {
    webidl.brandCheck(this, WebSocket)

    return this.#events.open
  }

  set onopen (fn) {
    webidl.brandCheck(this, WebSocket)

    if (this.#events.open) {
      this.removeEventListener('open', this.#events.open)
    }

    if (typeof fn === 'function') {
      this.#events.open = fn
      this.addEventListener('open', fn)
    } else {
      this.#events.open = null
    }
  }

  get onerror () {
    webidl.brandCheck(this, WebSocket)

    return this.#events.error
  }

  set onerror (fn) {
    webidl.brandCheck(this, WebSocket)

    if (this.#events.error) {
      this.removeEventListener('error', this.#events.error)
    }

    if (typeof fn === 'function') {
      this.#events.error = fn
      this.addEventListener('error', fn)
    } else {
      this.#events.error = null
    }
  }

  get onclose () {
    webidl.brandCheck(this, WebSocket)

    return this.#events.close
  }

  set onclose (fn) {
    webidl.brandCheck(this, WebSocket)

    if (this.#events.close) {
      this.removeEventListener('close', this.#events.close)
    }

    if (typeof fn === 'function') {
      this.#events.close = fn
      this.addEventListener('close', fn)
    } else {
      this.#events.close = null
    }
  }

  get onmessage () {
    webidl.brandCheck(this, WebSocket)

    return this.#events.message
  }

  set onmessage (fn) {
    webidl.brandCheck(this, WebSocket)

    if (this.#events.message) {
      this.removeEventListener('message', this.#events.message)
    }

    if (typeof fn === 'function') {
      this.#events.message = fn
      this.addEventListener('message', fn)
    } else {
      this.#events.message = null
    }
  }

  get binaryType () {
    webidl.brandCheck(this, WebSocket)

    return this[kBinaryType]
  }

  set binaryType (type) {
    webidl.brandCheck(this, WebSocket)

    if (type !== 'blob' && type !== 'arraybuffer') {
      this[kBinaryType] = 'blob'
    } else {
      this[kBinaryType] = type
    }
  }

  /**
   * @see https://websockets.spec.whatwg.org/#feedback-from-the-protocol
   */
  #onConnectionEstablished (response, parsedExtensions) {
    // processResponse is called when the "response’s header list has been received and initialized."
    // once this happens, the connection is open
    this[kResponse] = response

    const parser = new ByteParser(this, parsedExtensions)
    parser.on('drain', onParserDrain)
    parser.on('error', onParserError.bind(this))

    response.socket.ws = this
    this[kByteParser] = parser

    this.#sendQueue = new SendQueue(response.socket)

    // 1. Change the ready state to OPEN (1).
    this[kReadyState] = states.OPEN

    // 2. Change the extensions attribute’s value to the extensions in use, if
    //    it is not the null value.
    // https://datatracker.ietf.org/doc/html/rfc6455#section-9.1
    const extensions = response.headersList.get('sec-websocket-extensions')

    if (extensions !== null) {
      this.#extensions = extensions
    }

    // 3. Change the protocol attribute’s value to the subprotocol in use, if
    //    it is not the null value.
    // https://datatracker.ietf.org/doc/html/rfc6455#section-1.9
    const protocol = response.headersList.get('sec-websocket-protocol')

    if (protocol !== null) {
      this.#protocol = protocol
    }

    // 4. Fire an event named open at the WebSocket object.
    fireEvent('open', this)
  }
}

// https://websockets.spec.whatwg.org/#dom-websocket-connecting
WebSocket.CONNECTING = WebSocket.prototype.CONNECTING = states.CONNECTING
// https://websockets.spec.whatwg.org/#dom-websocket-open
WebSocket.OPEN = WebSocket.prototype.OPEN = states.OPEN
// https://websockets.spec.whatwg.org/#dom-websocket-closing
WebSocket.CLOSING = WebSocket.prototype.CLOSING = states.CLOSING
// https://websockets.spec.whatwg.org/#dom-websocket-closed
WebSocket.CLOSED = WebSocket.prototype.CLOSED = states.CLOSED

Object.defineProperties(WebSocket.prototype, {
  CONNECTING: staticPropertyDescriptors,
  OPEN: staticPropertyDescriptors,
  CLOSING: staticPropertyDescriptors,
  CLOSED: staticPropertyDescriptors,
  url: kEnumerableProperty,
  readyState: kEnumerableProperty,
  bufferedAmount: kEnumerableProperty,
  onopen: kEnumerableProperty,
  onerror: kEnumerableProperty,
  onclose: kEnumerableProperty,
  close: kEnumerableProperty,
  onmessage: kEnumerableProperty,
  binaryType: kEnumerableProperty,
  send: kEnumerableProperty,
  extensions: kEnumerableProperty,
  protocol: kEnumerableProperty,
  [Symbol.toStringTag]: {
    value: 'WebSocket',
    writable: false,
    enumerable: false,
    configurable: true
  }
})

Object.defineProperties(WebSocket, {
  CONNECTING: staticPropertyDescriptors,
  OPEN: staticPropertyDescriptors,
  CLOSING: staticPropertyDescriptors,
  CLOSED: staticPropertyDescriptors
})

webidl.converters['sequence<DOMString>'] = webidl.sequenceConverter(
  webidl.converters.DOMString
)

webidl.converters['DOMString or sequence<DOMString>'] = function (V, prefix, argument) {
  if (webidl.util.Type(V) === 'Object' && Symbol.iterator in V) {
    return webidl.converters['sequence<DOMString>'](V)
  }

  return webidl.converters.DOMString(V, prefix, argument)
}

// This implements the proposal made in https://github.com/whatwg/websockets/issues/42
webidl.converters.WebSocketInit = webidl.dictionaryConverter([
  {
    key: 'protocols',
    converter: webidl.converters['DOMString or sequence<DOMString>'],
    defaultValue: () => new Array(0)
  },
  {
    key: 'dispatcher',
    converter: webidl.converters.any,
    defaultValue: () => getGlobalDispatcher()
  },
  {
    key: 'headers',
    converter: webidl.nullableConverter(webidl.converters.HeadersInit)
  }
])

webidl.converters['DOMString or sequence<DOMString> or WebSocketInit'] = function (V) {
  if (webidl.util.Type(V) === 'Object' && !(Symbol.iterator in V)) {
    return webidl.converters.WebSocketInit(V)
  }

  return { protocols: webidl.converters['DOMString or sequence<DOMString>'](V) }
}

webidl.converters.WebSocketSendData = function (V) {
  if (webidl.util.Type(V) === 'Object') {
    if (isBlobLike(V)) {
      return webidl.converters.Blob(V, { strict: false })
    }

    if (ArrayBuffer.isView(V) || types.isArrayBuffer(V)) {
      return webidl.converters.BufferSource(V)
    }
  }

  return webidl.converters.USVString(V)
}

function onParserDrain () {
  this.ws[kResponse].socket.resume()
}

function onParserError (err) {
  let message
  let code

  if (err instanceof CloseEvent) {
    message = err.reason
    code = err.code
  } else {
    message = err.message
  }

  fireEvent('error', this, () => new ErrorEvent('error', { error: err, message }))

  closeWebSocketConnection(this, code)
}

module.exports = {
  WebSocket
}


/***/ }),

/***/ 5389:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



var stream = __nccwpck_require__(2203);
var inherits = (__nccwpck_require__(9023).inherits);

function Entry() {
    if (!(this instanceof Entry)) {
        return new Entry();
    }

    stream.PassThrough.call(this);

    this.path = null;
    this.type = null;
    this.isDirectory = false;
}

inherits(Entry, stream.PassThrough);

Entry.prototype.autodrain = function () {
    return this.pipe(new stream.Transform({ transform: function (d, e, cb) { cb(); } }));
}

module.exports = Entry;

/***/ }),

/***/ 5700:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {

var fs = __nccwpck_require__(9896);
var path = __nccwpck_require__(6928);
var util = __nccwpck_require__(9023);
var mkdirp = __nccwpck_require__(4469);
var Transform = (__nccwpck_require__(2203).Transform);
var UnzipStream = __nccwpck_require__(5580);

function Extract (opts) {
    if (!(this instanceof Extract))
    return new Extract(opts);

    Transform.call(this);

    this.opts = opts || {};
    this.unzipStream = new UnzipStream(this.opts);
    this.unfinishedEntries = 0;
    this.afterFlushWait = false;
    this.createdDirectories = {};

    var self = this;
    this.unzipStream.on('entry', this._processEntry.bind(this));
    this.unzipStream.on('error', function(error) {
        self.emit('error', error);
    });
}

util.inherits(Extract, Transform);

Extract.prototype._transform = function (chunk, encoding, cb) {
    this.unzipStream.write(chunk, encoding, cb);
}

Extract.prototype._flush = function (cb) {
    var self = this;

    var allDone = function() {
        process.nextTick(function() { self.emit('close'); });
        cb();
    }

    this.unzipStream.end(function() {
        if (self.unfinishedEntries > 0) {
            self.afterFlushWait = true;
            return self.on('await-finished', allDone);
        }
        allDone();
    });
}

Extract.prototype._processEntry = function (entry) {
    var self = this;
    var destPath = path.join(this.opts.path, entry.path);
    var directory = entry.isDirectory ? destPath : path.dirname(destPath);

    this.unfinishedEntries++;

    var writeFileFn = function() {
        var pipedStream = fs.createWriteStream(destPath);

        pipedStream.on('close', function() {
            self.unfinishedEntries--;
            self._notifyAwaiter();
        });
        pipedStream.on('error', function (error) {
            self.emit('error', error);
        });
        entry.pipe(pipedStream);
    }

    if (this.createdDirectories[directory] || directory === '.') {
        return writeFileFn();
    }

    // FIXME: calls to mkdirp can still be duplicated
    mkdirp(directory, function(err) {
        if (err) return self.emit('error', err);

        self.createdDirectories[directory] = true;

        if (entry.isDirectory) {
            self.unfinishedEntries--;
            self._notifyAwaiter();
            return;
        }

        writeFileFn();
    });
}

Extract.prototype._notifyAwaiter = function() {
    if (this.afterFlushWait && this.unfinishedEntries === 0) {
        this.emit('await-finished');
        this.afterFlushWait = false;
    }
}

module.exports = Extract;

/***/ }),

/***/ 2092:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {

var Transform = (__nccwpck_require__(2203).Transform);
var util = __nccwpck_require__(9023);

function MatcherStream(patternDesc, matchFn) {
    if (!(this instanceof MatcherStream)) {
        return new MatcherStream();
    }

    Transform.call(this);

    var p = typeof patternDesc === 'object' ? patternDesc.pattern : patternDesc;

    this.pattern = Buffer.isBuffer(p) ? p : Buffer.from(p);
    this.requiredLength = this.pattern.length;
    if (patternDesc.requiredExtraSize) this.requiredLength += patternDesc.requiredExtraSize;

    this.data = new Buffer('');
    this.bytesSoFar = 0;

    this.matchFn = matchFn;
}

util.inherits(MatcherStream, Transform);

MatcherStream.prototype.checkDataChunk = function (ignoreMatchZero) {
    var enoughData = this.data.length >= this.requiredLength; // strict more than ?
    if (!enoughData) { return; }

    var matchIndex = this.data.indexOf(this.pattern, ignoreMatchZero ? 1 : 0);
    if (matchIndex >= 0 && matchIndex + this.requiredLength > this.data.length) {
        if (matchIndex > 0) {
            var packet = this.data.slice(0, matchIndex);
            this.push(packet);
            this.bytesSoFar += matchIndex;
            this.data = this.data.slice(matchIndex);
        }
        return;
    }

    if (matchIndex === -1) {
        var packetLen = this.data.length - this.requiredLength + 1;

        var packet = this.data.slice(0, packetLen);
        this.push(packet);
        this.bytesSoFar += packetLen;
        this.data = this.data.slice(packetLen);
        return;
    }

    // found match
    if (matchIndex > 0) {
        var packet = this.data.slice(0, matchIndex);
        this.data = this.data.slice(matchIndex);
        this.push(packet);
        this.bytesSoFar += matchIndex;
    }

    var finished = this.matchFn ? this.matchFn(this.data, this.bytesSoFar) : true;
    if (finished) {
        this.data = new Buffer('');
        return;
    }

    return true;
}

MatcherStream.prototype._transform = function (chunk, encoding, cb) {
    this.data = Buffer.concat([this.data, chunk]);

    var firstIteration = true;
    while (this.checkDataChunk(!firstIteration)) {
        firstIteration = false;
    }

    cb();
}

MatcherStream.prototype._flush = function (cb) {
    if (this.data.length > 0) {
        var firstIteration = true;
        while (this.checkDataChunk(!firstIteration)) {
            firstIteration = false;
        }
    }

    if (this.data.length > 0) {
        this.push(this.data);
        this.data = null;
    }

    cb();
}

module.exports = MatcherStream;

/***/ }),

/***/ 1879:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {

var Transform = (__nccwpck_require__(2203).Transform);
var util = __nccwpck_require__(9023);
var UnzipStream = __nccwpck_require__(5580);

function ParserStream(opts) {
    if (!(this instanceof ParserStream)) {
        return new ParserStream(opts);
    }

    var transformOpts = opts || {};
    Transform.call(this, { readableObjectMode: true });

    this.opts = opts || {};
    this.unzipStream = new UnzipStream(this.opts);

    var self = this;
    this.unzipStream.on('entry', function(entry) {
        self.push(entry);
    });
    this.unzipStream.on('error', function(error) {
        self.emit('error', error);
    });
}

util.inherits(ParserStream, Transform);

ParserStream.prototype._transform = function (chunk, encoding, cb) {
    this.unzipStream.write(chunk, encoding, cb);
}

ParserStream.prototype._flush = function (cb) {
    var self = this;
    this.unzipStream.end(function() {
        process.nextTick(function() { self.emit('close'); });
        cb();
    });
}

ParserStream.prototype.on = function(eventName, fn) {
    if (eventName === 'entry') {
        return Transform.prototype.on.call(this, 'data', fn);
    }
    return Transform.prototype.on.call(this, eventName, fn);
}

ParserStream.prototype.drainAll = function () {
    this.unzipStream.drainAll();
    return this.pipe(new Transform({ objectMode: true, transform: function (d, e, cb) { cb(); } }));
}

module.exports = ParserStream;


/***/ }),

/***/ 5580:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {



var binary = __nccwpck_require__(8769);
var stream = __nccwpck_require__(2203);
var util = __nccwpck_require__(9023);
var zlib = __nccwpck_require__(725);
var MatcherStream = __nccwpck_require__(2092);
var Entry = __nccwpck_require__(5389);

const states = {
    STREAM_START:                         0,
    START:                                1,
    LOCAL_FILE_HEADER:                    2,
    LOCAL_FILE_HEADER_SUFFIX:             3,
    FILE_DATA:                            4,
    FILE_DATA_END:                        5,
    DATA_DESCRIPTOR:                      6,
    CENTRAL_DIRECTORY_FILE_HEADER:        7,
    CENTRAL_DIRECTORY_FILE_HEADER_SUFFIX: 8,
    CDIR64_END:                           9,
    CDIR64_END_DATA_SECTOR:               10,
    CDIR64_LOCATOR:                       11,
    CENTRAL_DIRECTORY_END:                12,
    CENTRAL_DIRECTORY_END_COMMENT:        13,
    TRAILING_JUNK:                        14,

    ERROR: 99
}

const FOUR_GIGS = 4294967296;

const SIG_LOCAL_FILE_HEADER  = 0x04034b50;
const SIG_DATA_DESCRIPTOR    = 0x08074b50;
const SIG_CDIR_RECORD        = 0x02014b50;
const SIG_CDIR64_RECORD_END  = 0x06064b50;
const SIG_CDIR64_LOCATOR_END = 0x07064b50;
const SIG_CDIR_RECORD_END    = 0x06054b50;

function UnzipStream(options) {
    if (!(this instanceof UnzipStream)) {
        return new UnzipStream(options);
    }

    stream.Transform.call(this);

    this.options = options || {};
    this.data = new Buffer('');
    this.state = states.STREAM_START;
    this.skippedBytes = 0;
    this.parsedEntity = null;
    this.outStreamInfo = {};
}

util.inherits(UnzipStream, stream.Transform);

UnzipStream.prototype.processDataChunk = function (chunk) {
    var requiredLength;

    switch (this.state) {
        case states.STREAM_START:
        case states.START:
            requiredLength = 4;
            break;
        case states.LOCAL_FILE_HEADER:
            requiredLength = 26;
            break;
        case states.LOCAL_FILE_HEADER_SUFFIX:
            requiredLength = this.parsedEntity.fileNameLength + this.parsedEntity.extraFieldLength;
            break;
        case states.DATA_DESCRIPTOR:
            requiredLength = 12;
            break;
        case states.CENTRAL_DIRECTORY_FILE_HEADER:
            requiredLength = 42;
            break;
        case states.CENTRAL_DIRECTORY_FILE_HEADER_SUFFIX:
            requiredLength = this.parsedEntity.fileNameLength + this.parsedEntity.extraFieldLength + this.parsedEntity.fileCommentLength;
            break;
        case states.CDIR64_END:
            requiredLength = 52;
            break;
        case states.CDIR64_END_DATA_SECTOR:
            requiredLength = this.parsedEntity.centralDirectoryRecordSize - 44;
            break;
        case states.CDIR64_LOCATOR:
            requiredLength = 16;
            break;
        case states.CENTRAL_DIRECTORY_END:
            requiredLength = 18;
            break;
        case states.CENTRAL_DIRECTORY_END_COMMENT:
            requiredLength = this.parsedEntity.commentLength;
            break;
        case states.FILE_DATA:
            return 0;
        case states.FILE_DATA_END:
            return 0;
        case states.TRAILING_JUNK:
            if (this.options.debug) console.log("found", chunk.length, "bytes of TRAILING_JUNK");
            return chunk.length;
        default:
            return chunk.length;
    }

    var chunkLength = chunk.length;
    if (chunkLength < requiredLength) {
        return 0;
    }

    switch (this.state) {
        case states.STREAM_START:
        case states.START:
            var signature = chunk.readUInt32LE(0);
            switch (signature) {
                case SIG_LOCAL_FILE_HEADER:
                    this.state = states.LOCAL_FILE_HEADER;
                    break;
                case SIG_CDIR_RECORD:
                    this.state = states.CENTRAL_DIRECTORY_FILE_HEADER;
                    break;
                case SIG_CDIR64_RECORD_END:
                    this.state = states.CDIR64_END;
                    break;
                case SIG_CDIR64_LOCATOR_END:
                    this.state = states.CDIR64_LOCATOR;
                    break;
                case SIG_CDIR_RECORD_END:
                    this.state = states.CENTRAL_DIRECTORY_END;
                    break;
                default:
                    var isStreamStart = this.state === states.STREAM_START;
                    if (!isStreamStart && (signature & 0xffff) !== 0x4b50 && this.skippedBytes < 26) {
                        // we'll allow a padding of max 28 bytes
                        var remaining = signature;
                        var toSkip = 4;
                        for (var i = 1; i < 4 && remaining !== 0; i++) {
                            remaining = remaining >>> 8;
                            if ((remaining & 0xff) === 0x50) {
                                toSkip = i;
                                break;
                            }
                        }
                        this.skippedBytes += toSkip;
                        if (this.options.debug) console.log('Skipped', this.skippedBytes, 'bytes');
                        return toSkip;
                    }
                    this.state = states.ERROR;
                    var errMsg = isStreamStart ? "Not a valid zip file" : "Invalid signature in zip file";
                    if (this.options.debug) {
                        var sig = chunk.readUInt32LE(0);
                        var asString;
                        try { asString = chunk.slice(0, 4).toString(); } catch (e) {}
                        console.log("Unexpected signature in zip file: 0x" + sig.toString(16), '"' + asString + '", skipped', this.skippedBytes, 'bytes');
                    }
                    this.emit("error", new Error(errMsg));
                    return chunk.length;
            }
            this.skippedBytes = 0;
            return requiredLength;

        case states.LOCAL_FILE_HEADER:
            this.parsedEntity = this._readFile(chunk);
            this.state = states.LOCAL_FILE_HEADER_SUFFIX;

            return requiredLength;

        case states.LOCAL_FILE_HEADER_SUFFIX:
            var entry = new Entry();
            var isUtf8 = (this.parsedEntity.flags & 0x800) !== 0;
            entry.path = this._decodeString(chunk.slice(0, this.parsedEntity.fileNameLength), isUtf8);
            var extraDataBuffer = chunk.slice(this.parsedEntity.fileNameLength, this.parsedEntity.fileNameLength + this.parsedEntity.extraFieldLength);
            var extra = this._readExtraFields(extraDataBuffer);
            if (extra && extra.parsed) {
                if (extra.parsed.path && !isUtf8) {
                    entry.path = extra.parsed.path;
                }
                if (Number.isFinite(extra.parsed.uncompressedSize) && this.parsedEntity.uncompressedSize === FOUR_GIGS-1) {
                    this.parsedEntity.uncompressedSize = extra.parsed.uncompressedSize;
                }
                if (Number.isFinite(extra.parsed.compressedSize) && this.parsedEntity.compressedSize === FOUR_GIGS-1) {
                    this.parsedEntity.compressedSize = extra.parsed.compressedSize;
                }
            }
            this.parsedEntity.extra = extra.parsed || {};

            if (this.options.debug) {
                const debugObj = Object.assign({}, this.parsedEntity, {
                    path: entry.path,
                    flags: '0x' + this.parsedEntity.flags.toString(16),
                    extraFields: extra && extra.debug
                });
                console.log("decoded LOCAL_FILE_HEADER:", JSON.stringify(debugObj, null, 2));
            }
            this._prepareOutStream(this.parsedEntity, entry);

            this.emit("entry", entry);

            this.state = states.FILE_DATA;

            return requiredLength;

        case states.CENTRAL_DIRECTORY_FILE_HEADER:
            this.parsedEntity = this._readCentralDirectoryEntry(chunk);
            this.state = states.CENTRAL_DIRECTORY_FILE_HEADER_SUFFIX;

            return requiredLength;

        case states.CENTRAL_DIRECTORY_FILE_HEADER_SUFFIX:
            // got file name in chunk[0..]
            var isUtf8 = (this.parsedEntity.flags & 0x800) !== 0;
            var path = this._decodeString(chunk.slice(0, this.parsedEntity.fileNameLength), isUtf8);
            var extraDataBuffer = chunk.slice(this.parsedEntity.fileNameLength, this.parsedEntity.fileNameLength + this.parsedEntity.extraFieldLength);
            var extra = this._readExtraFields(extraDataBuffer);
            if (extra && extra.parsed && extra.parsed.path && !isUtf8) {
                path = extra.parsed.path;
            }
            this.parsedEntity.extra = extra.parsed;

            var isUnix = ((this.parsedEntity.versionMadeBy & 0xff00) >> 8) === 3;
            var unixAttrs, isSymlink;
            if (isUnix) {
                unixAttrs = this.parsedEntity.externalFileAttributes >>> 16;
                var fileType = unixAttrs >>> 12;
                isSymlink = (fileType & 0o12) === 0o12; // __S_IFLNK
            }
            if (this.options.debug) {
                const debugObj = Object.assign({}, this.parsedEntity, {
                    path: path,
                    flags: '0x' + this.parsedEntity.flags.toString(16),
                    unixAttrs: unixAttrs && '0' + unixAttrs.toString(8),
                    isSymlink: isSymlink,
                    extraFields: extra.debug,
                });
                console.log("decoded CENTRAL_DIRECTORY_FILE_HEADER:", JSON.stringify(debugObj, null, 2));
            }
            this.state = states.START;

            return requiredLength;

        case states.CDIR64_END:
            this.parsedEntity = this._readEndOfCentralDirectory64(chunk);
            if (this.options.debug) {
                console.log("decoded CDIR64_END_RECORD:", this.parsedEntity);
            }
            this.state = states.CDIR64_END_DATA_SECTOR;

            return requiredLength;

        case states.CDIR64_END_DATA_SECTOR:
            this.state = states.START;

            return requiredLength;

        case states.CDIR64_LOCATOR:
            // ignore, nothing interesting
            this.state = states.START;

            return requiredLength;

        case states.CENTRAL_DIRECTORY_END:
            this.parsedEntity = this._readEndOfCentralDirectory(chunk);
            if (this.options.debug) {
                console.log("decoded CENTRAL_DIRECTORY_END:", this.parsedEntity);
            }
            this.state = states.CENTRAL_DIRECTORY_END_COMMENT;

            return requiredLength;

        case states.CENTRAL_DIRECTORY_END_COMMENT:
            if (this.options.debug) {
                console.log("decoded CENTRAL_DIRECTORY_END_COMMENT:", chunk.slice(0, requiredLength).toString());
            }
            this.state = states.TRAILING_JUNK;

            return requiredLength;

        case states.ERROR:
            return chunk.length; // discard

        default:
            console.log("didn't handle state #", this.state, "discarding");
            return chunk.length;
    }
}

UnzipStream.prototype._prepareOutStream = function (vars, entry) {
    var self = this;

    var isDirectory = vars.uncompressedSize === 0 && /[\/\\]$/.test(entry.path);
    // protect against malicious zip files which want to extract to parent dirs
    entry.path = entry.path.replace(/(?<=^|[/\\]+)[.][.]+(?=[/\\]+|$)/g, ".");
    entry.type = isDirectory ? 'Directory' : 'File';
    entry.isDirectory = isDirectory;

    var fileSizeKnown = !(vars.flags & 0x08);
    if (fileSizeKnown) {
        entry.size = vars.uncompressedSize;
    }

    var isVersionSupported = vars.versionsNeededToExtract <= 45;

    this.outStreamInfo = {
        stream: null,
        limit: fileSizeKnown ? vars.compressedSize : -1,
        written: 0
    };

    if (!fileSizeKnown) {
        var pattern = new Buffer(4);
        pattern.writeUInt32LE(SIG_DATA_DESCRIPTOR, 0);
        var zip64Mode = vars.extra.zip64Mode;
        var extraSize = zip64Mode ? 20 : 12;
        var searchPattern = {
            pattern: pattern,
            requiredExtraSize: extraSize
        }

        var matcherStream = new MatcherStream(searchPattern, function (matchedChunk, sizeSoFar) {
            var vars = self._readDataDescriptor(matchedChunk, zip64Mode);

            var compressedSizeMatches = vars.compressedSize === sizeSoFar;
            // let's also deal with archives with 4GiB+ files without zip64
            if (!zip64Mode && !compressedSizeMatches && sizeSoFar >= FOUR_GIGS) {
                var overflown = sizeSoFar - FOUR_GIGS;
                while (overflown >= 0) {
                    compressedSizeMatches = vars.compressedSize === overflown;
                    if (compressedSizeMatches) break;
                    overflown -= FOUR_GIGS;
                }
            }
            if (!compressedSizeMatches) { return; }

            self.state = states.FILE_DATA_END;
            var sliceOffset = zip64Mode ? 24 : 16;
            if (self.data.length > 0) {
                self.data = Buffer.concat([matchedChunk.slice(sliceOffset), self.data]);
            } else {
                self.data = matchedChunk.slice(sliceOffset);
            }

            return true;
        });
        this.outStreamInfo.stream = matcherStream;
    } else {
        this.outStreamInfo.stream = new stream.PassThrough();
    }

    var isEncrypted = (vars.flags & 0x01) || (vars.flags & 0x40);
    if (isEncrypted || !isVersionSupported) {
        var message = isEncrypted ? "Encrypted files are not supported!"
            : ("Zip version " + Math.floor(vars.versionsNeededToExtract / 10) + "." + vars.versionsNeededToExtract % 10 + " is not supported");

        entry.skip = true;
        setImmediate(() => {
            self.emit('error', new Error(message));
        });

        // try to skip over this entry
        this.outStreamInfo.stream.pipe(new Entry().autodrain());
        return;
    }

    var isCompressed = vars.compressionMethod > 0;
    if (isCompressed) {
        var inflater = zlib.createInflateRaw();
        inflater.on('error', function (err) {
            self.state = states.ERROR;
            self.emit('error', err);
        });
        this.outStreamInfo.stream.pipe(inflater).pipe(entry);
    } else {
        this.outStreamInfo.stream.pipe(entry);
    }

    if (this._drainAllEntries) {
        entry.autodrain();
    }
}

UnzipStream.prototype._readFile = function (data) {
    var vars = binary.parse(data)
        .word16lu('versionsNeededToExtract')
        .word16lu('flags')
        .word16lu('compressionMethod')
        .word16lu('lastModifiedTime')
        .word16lu('lastModifiedDate')
        .word32lu('crc32')
        .word32lu('compressedSize')
        .word32lu('uncompressedSize')
        .word16lu('fileNameLength')
        .word16lu('extraFieldLength')
        .vars;

    return vars;
}

UnzipStream.prototype._readExtraFields = function (data) {
    var extra = {};
    var result = { parsed: extra };
    if (this.options.debug) {
        result.debug = [];
    }
    var index = 0;
    while (index < data.length) {
        var vars = binary.parse(data)
            .skip(index)
            .word16lu('extraId')
            .word16lu('extraSize')
            .vars;

        index += 4;

        var fieldType = undefined;
        switch (vars.extraId) {
            case 0x0001:
                fieldType = "Zip64 extended information extra field";
                var z64vars = binary.parse(data.slice(index, index+vars.extraSize))
                    .word64lu('uncompressedSize')
                    .word64lu('compressedSize')
                    .word64lu('offsetToLocalHeader')
                    .word32lu('diskStartNumber')
                    .vars;
                if (z64vars.uncompressedSize !== null) {
                    extra.uncompressedSize = z64vars.uncompressedSize;
                }
                if (z64vars.compressedSize !== null) {
                    extra.compressedSize = z64vars.compressedSize;
                }
                extra.zip64Mode = true;
                break;
            case 0x000a:
                fieldType = "NTFS extra field";
                break;
            case 0x5455:
                fieldType = "extended timestamp";
                var timestampFields = data.readUInt8(index);
                var offset = 1;
                if (vars.extraSize >= offset + 4 && timestampFields & 1) {
                    extra.mtime = new Date(data.readUInt32LE(index + offset) * 1000);
                    offset += 4;
                }
                if (vars.extraSize >= offset + 4 && timestampFields & 2) {
                    extra.atime = new Date(data.readUInt32LE(index + offset) * 1000);
                    offset += 4;
                }
                if (vars.extraSize >= offset + 4 && timestampFields & 4) {
                    extra.ctime = new Date(data.readUInt32LE(index + offset) * 1000);
                }
                break;
            case 0x7075:
                fieldType = "Info-ZIP Unicode Path Extra Field";
                var fieldVer = data.readUInt8(index);
                if (fieldVer === 1) {
                    var offset = 1;
                    // TODO: should be checking this against our path buffer
                    var nameCrc32 = data.readUInt32LE(index + offset);
                    offset += 4;
                    var pathBuffer = data.slice(index + offset);
                    extra.path = pathBuffer.toString();
                }
                break;
            case 0x000d:
            case 0x5855:
                fieldType = vars.extraId === 0x000d ? "PKWARE Unix" : "Info-ZIP UNIX (type 1)";
                var offset = 0;
                if (vars.extraSize >= 8) {
                    var atime = new Date(data.readUInt32LE(index + offset) * 1000);
                    offset += 4;
                    var mtime = new Date(data.readUInt32LE(index + offset) * 1000);
                    offset += 4;
                    extra.atime = atime;
                    extra.mtime = mtime;

                    if (vars.extraSize >= 12) {
                        var uid = data.readUInt16LE(index + offset);
                        offset += 2;
                        var gid = data.readUInt16LE(index + offset);
                        offset += 2;
                        extra.uid = uid;
                        extra.gid = gid;
                    }
                }
                break;
            case 0x7855:
                fieldType = "Info-ZIP UNIX (type 2)";
                var offset = 0;
                if (vars.extraSize >= 4) {
                    var uid = data.readUInt16LE(index + offset);
                    offset += 2;
                    var gid = data.readUInt16LE(index + offset);
                    offset += 2;
                    extra.uid = uid;
                    extra.gid = gid;
                }
                break;
            case 0x7875:
                fieldType = "Info-ZIP New Unix";
                var offset = 0;
                var extraVer = data.readUInt8(index);
                offset += 1;
                if (extraVer === 1) {
                    var uidSize = data.readUInt8(index + offset);
                    offset += 1;
                    if (uidSize <= 6) {
                        extra.uid = data.readUIntLE(index + offset, uidSize);
                    }
                    offset += uidSize;

                    var gidSize = data.readUInt8(index + offset);
                    offset += 1;
                    if (gidSize <= 6) {
                        extra.gid = data.readUIntLE(index + offset, gidSize);
                    }
                }
                break;
            case 0x756e:
                fieldType = "ASi Unix";
                var offset = 0;
                if (vars.extraSize >= 14) {
                    var crc = data.readUInt32LE(index + offset);
                    offset += 4;
                    var mode = data.readUInt16LE(index + offset);
                    offset += 2;
                    var sizdev = data.readUInt32LE(index + offset);
                    offset += 4;
                    var uid = data.readUInt16LE(index + offset);
                    offset += 2;
                    var gid = data.readUInt16LE(index + offset);
                    offset += 2;
                    extra.mode = mode;
                    extra.uid = uid;
                    extra.gid = gid;
                    if (vars.extraSize > 14) {
                        var start = index + offset;
                        var end = index + vars.extraSize - 14;
                        var symlinkName = this._decodeString(data.slice(start, end));
                        extra.symlink = symlinkName;
                    }
                }
                break;
        }

        if (this.options.debug) {
            result.debug.push({
                extraId: '0x' + vars.extraId.toString(16),
                description: fieldType,
                data: data.slice(index, index + vars.extraSize).inspect()
            });
        }

        index += vars.extraSize;
    }

    return result;
}

UnzipStream.prototype._readDataDescriptor = function (data, zip64Mode) {
    if (zip64Mode) {
        var vars = binary.parse(data)
            .word32lu('dataDescriptorSignature')
            .word32lu('crc32')
            .word64lu('compressedSize')
            .word64lu('uncompressedSize')
            .vars;

        return vars;
    }

    var vars = binary.parse(data)
        .word32lu('dataDescriptorSignature')
        .word32lu('crc32')
        .word32lu('compressedSize')
        .word32lu('uncompressedSize')
        .vars;

    return vars;
}

UnzipStream.prototype._readCentralDirectoryEntry = function (data) {
    var vars = binary.parse(data)
        .word16lu('versionMadeBy')
        .word16lu('versionsNeededToExtract')
        .word16lu('flags')
        .word16lu('compressionMethod')
        .word16lu('lastModifiedTime')
        .word16lu('lastModifiedDate')
        .word32lu('crc32')
        .word32lu('compressedSize')
        .word32lu('uncompressedSize')
        .word16lu('fileNameLength')
        .word16lu('extraFieldLength')
        .word16lu('fileCommentLength')
        .word16lu('diskNumber')
        .word16lu('internalFileAttributes')
        .word32lu('externalFileAttributes')
        .word32lu('offsetToLocalFileHeader')
        .vars;

    return vars;
}

UnzipStream.prototype._readEndOfCentralDirectory64 = function (data) {
    var vars = binary.parse(data)
        .word64lu('centralDirectoryRecordSize')
        .word16lu('versionMadeBy')
        .word16lu('versionsNeededToExtract')
        .word32lu('diskNumber')
        .word32lu('diskNumberWithCentralDirectoryStart')
        .word64lu('centralDirectoryEntries')
        .word64lu('totalCentralDirectoryEntries')
        .word64lu('sizeOfCentralDirectory')
        .word64lu('offsetToStartOfCentralDirectory')
        .vars;

    return vars;
}

UnzipStream.prototype._readEndOfCentralDirectory = function (data) {
    var vars = binary.parse(data)
        .word16lu('diskNumber')
        .word16lu('diskStart')
        .word16lu('centralDirectoryEntries')
        .word16lu('totalCentralDirectoryEntries')
        .word32lu('sizeOfCentralDirectory')
        .word32lu('offsetToStartOfCentralDirectory')
        .word16lu('commentLength')
        .vars;

    return vars;
}

const cp437 = '\u0000☺☻♥♦♣♠•◘○◙♂♀♪♫☼►◄↕‼¶§▬↨↑↓→←∟↔▲▼ !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~⌂ÇüéâäàåçêëèïîìÄÅÉæÆôöòûùÿÖÜ¢£¥₧ƒáíóúñÑªº¿⌐¬½¼¡«»░▒▓│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌█▄▌▐▀αßΓπΣσµτΦΘΩδ∞φε∩≡±≥≤⌠⌡÷≈°∙·√ⁿ²■ ';

UnzipStream.prototype._decodeString = function (buffer, isUtf8) {
    if (isUtf8) {
        return buffer.toString('utf8');
    }
    // allow passing custom decoder
    if (this.options.decodeString) {
        return this.options.decodeString(buffer);
    }
    let result = "";
    for (var i=0; i<buffer.length; i++) {
        result += cp437[buffer[i]];
    }
    return result;
}

UnzipStream.prototype._parseOrOutput = function (encoding, cb) {
    var consume;
    while ((consume = this.processDataChunk(this.data)) > 0) {
        this.data = this.data.slice(consume);
        if (this.data.length === 0) break;
    }

    if (this.state === states.FILE_DATA) {
        if (this.outStreamInfo.limit >= 0) {
            var remaining = this.outStreamInfo.limit - this.outStreamInfo.written;
            var packet;
            if (remaining < this.data.length) {
                packet = this.data.slice(0, remaining);
                this.data = this.data.slice(remaining);
            } else {
                packet = this.data;
                this.data = new Buffer('');
            }

            this.outStreamInfo.written += packet.length;
            if (this.outStreamInfo.limit === this.outStreamInfo.written) {
                this.state = states.START;

                this.outStreamInfo.stream.end(packet, encoding, cb);
            } else {
                this.outStreamInfo.stream.write(packet, encoding, cb);
            }
        } else {
            var packet = this.data;
            this.data = new Buffer('');

            this.outStreamInfo.written += packet.length;
            var outputStream = this.outStreamInfo.stream;
            outputStream.write(packet, encoding, () => {
                if (this.state === states.FILE_DATA_END) {
                    this.state = states.START;
                    return outputStream.end(cb);
                }
                cb();
            });
        }
        // we've written to the output stream, letting that write deal with the callback
        return;
    }

    cb();
}

UnzipStream.prototype.drainAll = function () {
    this._drainAllEntries = true;
}

UnzipStream.prototype._transform = function (chunk, encoding, cb) {
    var self = this;
    if (self.data.length > 0) {
        self.data = Buffer.concat([self.data, chunk]);
    } else {
        self.data = chunk;
    }

    var startDataLength = self.data.length;
    var done = function () {
        if (self.data.length > 0 && self.data.length < startDataLength) {
            startDataLength = self.data.length;
            self._parseOrOutput(encoding, done);
            return;
        }
        cb();
    };
    self._parseOrOutput(encoding, done);
}

UnzipStream.prototype._flush = function (cb) {
    var self = this;
    if (self.data.length > 0) {
        self._parseOrOutput('buffer', function () {
            if (self.data.length > 0) return setImmediate(function () { self._flush(cb); });
            cb();
        });

        return;
    }

    if (self.state === states.FILE_DATA) {
        // uh oh, something went wrong
        return cb(new Error("Stream finished in an invalid state, uncompression failed"));
    }

    setImmediate(cb);
}

module.exports = UnzipStream;


/***/ }),

/***/ 3991:
/***/ ((__unused_webpack_module, exports, __nccwpck_require__) => {



exports.Parse = __nccwpck_require__(1879);
exports.Extract = __nccwpck_require__(5700);

/***/ }),

/***/ 4488:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {


/**
 * For Node.js, simply re-export the core `util.deprecate` function.
 */

module.exports = __nccwpck_require__(9023).deprecate;


/***/ }),

/***/ 1622:
/***/ ((module, __unused_webpack_exports, __nccwpck_require__) => {

/**
 * ZipStream
 *
 * @ignore
 * @license [MIT]{@link https://github.com/archiverjs/node-zip-stream/blob/master/LICENSE}
 * @copyright (c) 2014 Chris Talkington, contributors.
 */
var inherits = (__nccwpck_require__(9023).inherits);

var ZipArchiveOutputStream = (__nccwpck_require__(7544).ZipArchiveOutputStream);
var ZipArchiveEntry = (__nccwpck_require__(7544).ZipArchiveEntry);

var util = __nccwpck_require__(3296);

/**
 * @constructor
 * @extends external:ZipArchiveOutputStream
 * @param {Object} [options]
 * @param {String} [options.comment] Sets the zip archive comment.
 * @param {Boolean} [options.forceLocalTime=false] Forces the archive to contain local file times instead of UTC.
 * @param {Boolean} [options.forceZip64=false] Forces the archive to contain ZIP64 headers.
 * @param {Boolean} [options.store=false] Sets the compression method to STORE.
 * @param {Object} [options.zlib] Passed to [zlib]{@link https://nodejs.org/api/zlib.html#zlib_class_options}
 * to control compression.
 */
var ZipStream = module.exports = function(options) {
  if (!(this instanceof ZipStream)) {
    return new ZipStream(options);
  }

  options = this.options = options || {};
  options.zlib = options.zlib || {};

  ZipArchiveOutputStream.call(this, options);

  if (typeof options.level === 'number' && options.level >= 0) {
    options.zlib.level = options.level;
    delete options.level;
  }

  if (!options.forceZip64 && typeof options.zlib.level === 'number' && options.zlib.level === 0) {
    options.store = true;
  }

  options.namePrependSlash = options.namePrependSlash || false;

  if (options.comment && options.comment.length > 0) {
    this.setComment(options.comment);
  }
};

inherits(ZipStream, ZipArchiveOutputStream);

/**
 * Normalizes entry data with fallbacks for key properties.
 *
 * @private
 * @param  {Object} data
 * @return {Object}
 */
ZipStream.prototype._normalizeFileData = function(data) {
  data = util.defaults(data, {
    type: 'file',
    name: null,
    namePrependSlash: this.options.namePrependSlash,
    linkname: null,
    date: null,
    mode: null,
    store: this.options.store,
    comment: ''
  });

  var isDir = data.type === 'directory';
  var isSymlink = data.type === 'symlink';

  if (data.name) {
    data.name = util.sanitizePath(data.name);

    if (!isSymlink && data.name.slice(-1) === '/') {
      isDir = true;
      data.type = 'directory';
    } else if (isDir) {
      data.name += '/';
    }
  }

  if (isDir || isSymlink) {
    data.store = true;
  }

  data.date = util.dateify(data.date);

  return data;
};

/**
 * Appends an entry given an input source (text string, buffer, or stream).
 *
 * @param  {(Buffer|Stream|String)} source The input source.
 * @param  {Object} data
 * @param  {String} data.name Sets the entry name including internal path.
 * @param  {String} [data.comment] Sets the entry comment.
 * @param  {(String|Date)} [data.date=NOW()] Sets the entry date.
 * @param  {Number} [data.mode=D:0755/F:0644] Sets the entry permissions.
 * @param  {Boolean} [data.store=options.store] Sets the compression method to STORE.
 * @param  {String} [data.type=file] Sets the entry type. Defaults to `directory`
 * if name ends with trailing slash.
 * @param  {Function} callback
 * @return this
 */
ZipStream.prototype.entry = function(source, data, callback) {
  if (typeof callback !== 'function') {
    callback = this._emitErrorCallback.bind(this);
  }

  data = this._normalizeFileData(data);

  if (data.type !== 'file' && data.type !== 'directory' && data.type !== 'symlink') {
    callback(new Error(data.type + ' entries not currently supported'));
    return;
  }

  if (typeof data.name !== 'string' || data.name.length === 0) {
    callback(new Error('entry name must be a non-empty string value'));
    return;
  }

  if (data.type === 'symlink' && typeof data.linkname !== 'string') {
    callback(new Error('entry linkname must be a non-empty string value when type equals symlink'));
    return;
  }

  var entry = new ZipArchiveEntry(data.name);
  entry.setTime(data.date, this.options.forceLocalTime);

  if (data.namePrependSlash) {
    entry.setName(data.name, true);
  }

  if (data.store) {
    entry.setMethod(0);
  }

  if (data.comment.length > 0) {
    entry.setComment(data.comment);
  }

  if (data.type === 'symlink' && typeof data.mode !== 'number') {
    data.mode = 40960; // 0120000
  }

  if (typeof data.mode === 'number') {
    if (data.type === 'symlink') {
      data.mode |= 40960;
    }

    entry.setUnixMode(data.mode);
  }

  if (data.type === 'symlink' && typeof data.linkname === 'string') {
    source = Buffer.from(data.linkname);
  }

  return ZipArchiveOutputStream.prototype.entry.call(this, entry, source, callback);
};

/**
 * Finalizes the instance and prevents further appending to the archive
 * structure (queue will continue til drained).
 *
 * @return void
 */
ZipStream.prototype.finalize = function() {
  this.finish();
};

/**
 * Returns the current number of bytes written to this stream.
 * @function ZipStream#getBytesWritten
 * @returns {Number}
 */

/**
 * Compress Commons ZipArchiveOutputStream
 * @external ZipArchiveOutputStream
 * @see {@link https://github.com/archiverjs/node-compress-commons}
 */


/***/ }),

/***/ 2613:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("assert");

/***/ }),

/***/ 181:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("buffer");

/***/ }),

/***/ 9140:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("constants");

/***/ }),

/***/ 4434:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("events");

/***/ }),

/***/ 9896:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("fs");

/***/ }),

/***/ 8611:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("http");

/***/ }),

/***/ 5692:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("https");

/***/ }),

/***/ 9278:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("net");

/***/ }),

/***/ 4589:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:assert");

/***/ }),

/***/ 6698:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:async_hooks");

/***/ }),

/***/ 4573:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:buffer");

/***/ }),

/***/ 7540:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:console");

/***/ }),

/***/ 7598:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:crypto");

/***/ }),

/***/ 3053:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:diagnostics_channel");

/***/ }),

/***/ 610:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:dns");

/***/ }),

/***/ 8474:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:events");

/***/ }),

/***/ 3024:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:fs");

/***/ }),

/***/ 1455:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:fs/promises");

/***/ }),

/***/ 7067:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:http");

/***/ }),

/***/ 2467:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:http2");

/***/ }),

/***/ 7030:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:net");

/***/ }),

/***/ 6760:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:path");

/***/ }),

/***/ 643:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:perf_hooks");

/***/ }),

/***/ 1792:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:querystring");

/***/ }),

/***/ 7075:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:stream");

/***/ }),

/***/ 6193:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:string_decoder");

/***/ }),

/***/ 1692:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:tls");

/***/ }),

/***/ 3136:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:url");

/***/ }),

/***/ 7975:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:util");

/***/ }),

/***/ 3429:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:util/types");

/***/ }),

/***/ 5919:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:worker_threads");

/***/ }),

/***/ 8522:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:zlib");

/***/ }),

/***/ 857:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("os");

/***/ }),

/***/ 6928:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("path");

/***/ }),

/***/ 2203:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("stream");

/***/ }),

/***/ 3193:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("string_decoder");

/***/ }),

/***/ 4756:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("tls");

/***/ }),

/***/ 2018:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("tty");

/***/ }),

/***/ 7016:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("url");

/***/ }),

/***/ 9023:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("util");

/***/ }),

/***/ 725:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("zlib");

/***/ }),

/***/ 3345:
/***/ ((__unused_webpack_module, exports) => {

var __webpack_unused_export__;

// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
__webpack_unused_export__ = ({ value: true });
exports.w = void 0;
/**
 * Holds the singleton operationRequestMap, to be shared across CJS and ESM imports.
 */
exports.w = {
    operationRequestMap: new WeakMap(),
};
//# sourceMappingURL=state-cjs.cjs.map

/***/ }),

/***/ 8914:
/***/ ((__unused_webpack_module, exports) => {

var __webpack_unused_export__;

// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
__webpack_unused_export__ = ({ value: true });
exports.w = void 0;
/**
 * @internal
 *
 * Holds the singleton instrumenter, to be shared across CJS and ESM imports.
 */
exports.w = {
    instrumenterImplementation: undefined,
};
//# sourceMappingURL=state-cjs.cjs.map

/***/ }),

/***/ 2649:
/***/ ((__unused_webpack_module, exports) => {


Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.range = exports.balanced = void 0;
const balanced = (a, b, str) => {
    const ma = a instanceof RegExp ? maybeMatch(a, str) : a;
    const mb = b instanceof RegExp ? maybeMatch(b, str) : b;
    const r = ma !== null && mb != null && (0, exports.range)(ma, mb, str);
    return (r && {
        start: r[0],
        end: r[1],
        pre: str.slice(0, r[0]),
        body: str.slice(r[0] + ma.length, r[1]),
        post: str.slice(r[1] + mb.length),
    });
};
exports.balanced = balanced;
const maybeMatch = (reg, str) => {
    const m = str.match(reg);
    return m ? m[0] : null;
};
const range = (a, b, str) => {
    let begs, beg, left, right = undefined, result;
    let ai = str.indexOf(a);
    let bi = str.indexOf(b, ai + 1);
    let i = ai;
    if (ai >= 0 && bi > 0) {
        if (a === b) {
            return [ai, bi];
        }
        begs = [];
        left = str.length;
        while (i >= 0 && !result) {
            if (i === ai) {
                begs.push(i);
                ai = str.indexOf(a, i + 1);
            }
            else if (begs.length === 1) {
                const r = begs.pop();
                if (r !== undefined)
                    result = [r, bi];
            }
            else {
                beg = begs.pop();
                if (beg !== undefined && beg < left) {
                    left = beg;
                    right = bi;
                }
                bi = str.indexOf(b, i + 1);
            }
            i = ai < bi && ai >= 0 ? ai : bi;
        }
        if (begs.length && right !== undefined) {
            result = [left, right];
        }
    }
    return result;
};
exports.range = range;
//# sourceMappingURL=index.js.map

/***/ }),

/***/ 8968:
/***/ ((__unused_webpack_module, exports, __nccwpck_require__) => {


Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.EXPANSION_MAX = void 0;
exports.expand = expand;
const balanced_match_1 = __nccwpck_require__(2649);
const escSlash = '\0SLASH' + Math.random() + '\0';
const escOpen = '\0OPEN' + Math.random() + '\0';
const escClose = '\0CLOSE' + Math.random() + '\0';
const escComma = '\0COMMA' + Math.random() + '\0';
const escPeriod = '\0PERIOD' + Math.random() + '\0';
const escSlashPattern = new RegExp(escSlash, 'g');
const escOpenPattern = new RegExp(escOpen, 'g');
const escClosePattern = new RegExp(escClose, 'g');
const escCommaPattern = new RegExp(escComma, 'g');
const escPeriodPattern = new RegExp(escPeriod, 'g');
const slashPattern = /\\\\/g;
const openPattern = /\\{/g;
const closePattern = /\\}/g;
const commaPattern = /\\,/g;
const periodPattern = /\\./g;
exports.EXPANSION_MAX = 100_000;
function numeric(str) {
    return !isNaN(str) ? parseInt(str, 10) : str.charCodeAt(0);
}
function escapeBraces(str) {
    return str
        .replace(slashPattern, escSlash)
        .replace(openPattern, escOpen)
        .replace(closePattern, escClose)
        .replace(commaPattern, escComma)
        .replace(periodPattern, escPeriod);
}
function unescapeBraces(str) {
    return str
        .replace(escSlashPattern, '\\')
        .replace(escOpenPattern, '{')
        .replace(escClosePattern, '}')
        .replace(escCommaPattern, ',')
        .replace(escPeriodPattern, '.');
}
/**
 * Basically just str.split(","), but handling cases
 * where we have nested braced sections, which should be
 * treated as individual members, like {a,{b,c},d}
 */
function parseCommaParts(str) {
    if (!str) {
        return [''];
    }
    const parts = [];
    const m = (0, balanced_match_1.balanced)('{', '}', str);
    if (!m) {
        return str.split(',');
    }
    const { pre, body, post } = m;
    const p = pre.split(',');
    p[p.length - 1] += '{' + body + '}';
    const postParts = parseCommaParts(post);
    if (post.length) {
        ;
        p[p.length - 1] += postParts.shift();
        p.push.apply(p, postParts);
    }
    parts.push.apply(parts, p);
    return parts;
}
function expand(str, options = {}) {
    if (!str) {
        return [];
    }
    const { max = exports.EXPANSION_MAX } = options;
    // I don't know why Bash 4.3 does this, but it does.
    // Anything starting with {} will have the first two bytes preserved
    // but *only* at the top level, so {},a}b will not expand to anything,
    // but a{},b}c will be expanded to [a}c,abc].
    // One could argue that this is a bug in Bash, but since the goal of
    // this module is to match Bash's rules, we escape a leading {}
    if (str.slice(0, 2) === '{}') {
        str = '\\{\\}' + str.slice(2);
    }
    return expand_(escapeBraces(str), max, true).map(unescapeBraces);
}
function embrace(str) {
    return '{' + str + '}';
}
function isPadded(el) {
    return /^-?0\d/.test(el);
}
function lte(i, y) {
    return i <= y;
}
function gte(i, y) {
    return i >= y;
}
function expand_(str, max, isTop) {
    /** @type {string[]} */
    const expansions = [];
    const m = (0, balanced_match_1.balanced)('{', '}', str);
    if (!m)
        return [str];
    // no need to expand pre, since it is guaranteed to be free of brace-sets
    const pre = m.pre;
    const post = m.post.length ? expand_(m.post, max, false) : [''];
    if (/\$$/.test(m.pre)) {
        for (let k = 0; k < post.length && k < max; k++) {
            const expansion = pre + '{' + m.body + '}' + post[k];
            expansions.push(expansion);
        }
    }
    else {
        const isNumericSequence = /^-?\d+\.\.-?\d+(?:\.\.-?\d+)?$/.test(m.body);
        const isAlphaSequence = /^[a-zA-Z]\.\.[a-zA-Z](?:\.\.-?\d+)?$/.test(m.body);
        const isSequence = isNumericSequence || isAlphaSequence;
        const isOptions = m.body.indexOf(',') >= 0;
        if (!isSequence && !isOptions) {
            // {a},b}
            if (m.post.match(/,(?!,).*\}/)) {
                str = m.pre + '{' + m.body + escClose + m.post;
                return expand_(str, max, true);
            }
            return [str];
        }
        let n;
        if (isSequence) {
            n = m.body.split(/\.\./);
        }
        else {
            n = parseCommaParts(m.body);
            if (n.length === 1 && n[0] !== undefined) {
                // x{{a,b}}y ==> x{a}y x{b}y
                n = expand_(n[0], max, false).map(embrace);
                //XXX is this necessary? Can't seem to hit it in tests.
                /* c8 ignore start */
                if (n.length === 1) {
                    return post.map(p => m.pre + n[0] + p);
                }
                /* c8 ignore stop */
            }
        }
        // at this point, n is the parts, and we know it's not a comma set
        // with a single entry.
        let N;
        if (isSequence && n[0] !== undefined && n[1] !== undefined) {
            const x = numeric(n[0]);
            const y = numeric(n[1]);
            const width = Math.max(n[0].length, n[1].length);
            let incr = n.length === 3 && n[2] !== undefined ? Math.abs(numeric(n[2])) : 1;
            let test = lte;
            const reverse = y < x;
            if (reverse) {
                incr *= -1;
                test = gte;
            }
            const pad = n.some(isPadded);
            N = [];
            for (let i = x; test(i, y); i += incr) {
                let c;
                if (isAlphaSequence) {
                    c = String.fromCharCode(i);
                    if (c === '\\') {
                        c = '';
                    }
                }
                else {
                    c = String(i);
                    if (pad) {
                        const need = width - c.length;
                        if (need > 0) {
                            const z = new Array(need + 1).join('0');
                            if (i < 0) {
                                c = '-' + z + c.slice(1);
                            }
                            else {
                                c = z + c;
                            }
                        }
                    }
                }
                N.push(c);
            }
        }
        else {
            N = [];
            for (let j = 0; j < n.length; j++) {
                N.push.apply(N, expand_(n[j], max, false));
            }
        }
        for (let j = 0; j < N.length; j++) {
            for (let k = 0; k < post.length && expansions.length < max; k++) {
                const expansion = pre + N[j] + post[k];
                if (!isTop || isSequence || expansion) {
                    expansions.push(expansion);
                }
            }
        }
    }
    return expansions;
}
//# sourceMappingURL=index.js.map

/***/ }),

/***/ 1120:
/***/ ((module) => {

var __webpack_unused_export__;


const NullObject = function NullObject () { }
NullObject.prototype = Object.create(null)

/**
 * RegExp to match *( ";" parameter ) in RFC 7231 sec 3.1.1.1
 *
 * parameter     = token "=" ( token / quoted-string )
 * token         = 1*tchar
 * tchar         = "!" / "#" / "$" / "%" / "&" / "'" / "*"
 *               / "+" / "-" / "." / "^" / "_" / "`" / "|" / "~"
 *               / DIGIT / ALPHA
 *               ; any VCHAR, except delimiters
 * quoted-string = DQUOTE *( qdtext / quoted-pair ) DQUOTE
 * qdtext        = HTAB / SP / %x21 / %x23-5B / %x5D-7E / obs-text
 * obs-text      = %x80-FF
 * quoted-pair   = "\" ( HTAB / SP / VCHAR / obs-text )
 */
const paramRE = /; *([!#$%&'*+.^\w`|~-]+)=("(?:[\v\u0020\u0021\u0023-\u005b\u005d-\u007e\u0080-\u00ff]|\\[\v\u0020-\u00ff])*"|[!#$%&'*+.^\w`|~-]+) */gu

/**
 * RegExp to match quoted-pair in RFC 7230 sec 3.2.6
 *
 * quoted-pair = "\" ( HTAB / SP / VCHAR / obs-text )
 * obs-text    = %x80-FF
 */
const quotedPairRE = /\\([\v\u0020-\u00ff])/gu

/**
 * RegExp to match type in RFC 7231 sec 3.1.1.1
 *
 * media-type = type "/" subtype
 * type       = token
 * subtype    = token
 */
const mediaTypeRE = /^[!#$%&'*+.^\w|~-]+\/[!#$%&'*+.^\w|~-]+$/u

// default ContentType to prevent repeated object creation
const defaultContentType = { type: '', parameters: new NullObject() }
Object.freeze(defaultContentType.parameters)
Object.freeze(defaultContentType)

/**
 * Parse media type to object.
 *
 * @param {string|object} header
 * @return {Object}
 * @public
 */

function parse (header) {
  if (typeof header !== 'string') {
    throw new TypeError('argument header is required and must be a string')
  }

  let index = header.indexOf(';')
  const type = index !== -1
    ? header.slice(0, index).trim()
    : header.trim()

  if (mediaTypeRE.test(type) === false) {
    throw new TypeError('invalid media type')
  }

  const result = {
    type: type.toLowerCase(),
    parameters: new NullObject()
  }

  // parse parameters
  if (index === -1) {
    return result
  }

  let key
  let match
  let value

  paramRE.lastIndex = index

  while ((match = paramRE.exec(header))) {
    if (match.index !== index) {
      throw new TypeError('invalid parameter format')
    }

    index += match[0].length
    key = match[1].toLowerCase()
    value = match[2]

    if (value[0] === '"') {
      // remove quotes and escapes
      value = value
        .slice(1, value.length - 1)

      quotedPairRE.test(value) && (value = value.replace(quotedPairRE, '$1'))
    }

    result.parameters[key] = value
  }

  if (index !== header.length) {
    throw new TypeError('invalid parameter format')
  }

  return result
}

function safeParse (header) {
  if (typeof header !== 'string') {
    return defaultContentType
  }

  let index = header.indexOf(';')
  const type = index !== -1
    ? header.slice(0, index).trim()
    : header.trim()

  if (mediaTypeRE.test(type) === false) {
    return defaultContentType
  }

  const result = {
    type: type.toLowerCase(),
    parameters: new NullObject()
  }

  // parse parameters
  if (index === -1) {
    return result
  }

  let key
  let match
  let value

  paramRE.lastIndex = index

  while ((match = paramRE.exec(header))) {
    if (match.index !== index) {
      return defaultContentType
    }

    index += match[0].length
    key = match[1].toLowerCase()
    value = match[2]

    if (value[0] === '"') {
      // remove quotes and escapes
      value = value
        .slice(1, value.length - 1)

      quotedPairRE.test(value) && (value = value.replace(quotedPairRE, '$1'))
    }

    result.parameters[key] = value
  }

  if (index !== header.length) {
    return defaultContentType
  }

  return result
}

__webpack_unused_export__ = { parse, safeParse }
__webpack_unused_export__ = parse
module.exports.xL = safeParse
__webpack_unused_export__ = defaultContentType


/***/ }),

/***/ 2981:
/***/ ((__unused_webpack_module, exports, __nccwpck_require__) => {


Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.Glob = void 0;
const minimatch_1 = __nccwpck_require__(3790);
const node_url_1 = __nccwpck_require__(3136);
const path_scurry_1 = __nccwpck_require__(8958);
const pattern_js_1 = __nccwpck_require__(7813);
const walker_js_1 = __nccwpck_require__(1157);
// if no process global, just call it linux.
// so we default to case-sensitive, / separators
const defaultPlatform = (typeof process === 'object' &&
    process &&
    typeof process.platform === 'string') ?
    process.platform
    : 'linux';
/**
 * An object that can perform glob pattern traversals.
 */
class Glob {
    absolute;
    cwd;
    root;
    dot;
    dotRelative;
    follow;
    ignore;
    magicalBraces;
    mark;
    matchBase;
    maxDepth;
    nobrace;
    nocase;
    nodir;
    noext;
    noglobstar;
    pattern;
    platform;
    realpath;
    scurry;
    stat;
    signal;
    windowsPathsNoEscape;
    withFileTypes;
    includeChildMatches;
    /**
     * The options provided to the constructor.
     */
    opts;
    /**
     * An array of parsed immutable {@link Pattern} objects.
     */
    patterns;
    /**
     * All options are stored as properties on the `Glob` object.
     *
     * See {@link GlobOptions} for full options descriptions.
     *
     * Note that a previous `Glob` object can be passed as the
     * `GlobOptions` to another `Glob` instantiation to re-use settings
     * and caches with a new pattern.
     *
     * Traversal functions can be called multiple times to run the walk
     * again.
     */
    constructor(pattern, opts) {
        /* c8 ignore start */
        if (!opts)
            throw new TypeError('glob options required');
        /* c8 ignore stop */
        this.withFileTypes = !!opts.withFileTypes;
        this.signal = opts.signal;
        this.follow = !!opts.follow;
        this.dot = !!opts.dot;
        this.dotRelative = !!opts.dotRelative;
        this.nodir = !!opts.nodir;
        this.mark = !!opts.mark;
        if (!opts.cwd) {
            this.cwd = '';
        }
        else if (opts.cwd instanceof URL || opts.cwd.startsWith('file://')) {
            opts.cwd = (0, node_url_1.fileURLToPath)(opts.cwd);
        }
        this.cwd = opts.cwd || '';
        this.root = opts.root;
        this.magicalBraces = !!opts.magicalBraces;
        this.nobrace = !!opts.nobrace;
        this.noext = !!opts.noext;
        this.realpath = !!opts.realpath;
        this.absolute = opts.absolute;
        this.includeChildMatches = opts.includeChildMatches !== false;
        this.noglobstar = !!opts.noglobstar;
        this.matchBase = !!opts.matchBase;
        this.maxDepth =
            typeof opts.maxDepth === 'number' ? opts.maxDepth : Infinity;
        this.stat = !!opts.stat;
        this.ignore = opts.ignore;
        if (this.withFileTypes && this.absolute !== undefined) {
            throw new Error('cannot set absolute and withFileTypes:true');
        }
        if (typeof pattern === 'string') {
            pattern = [pattern];
        }
        this.windowsPathsNoEscape =
            !!opts.windowsPathsNoEscape ||
                opts.allowWindowsEscape ===
                    false;
        if (this.windowsPathsNoEscape) {
            pattern = pattern.map(p => p.replace(/\\/g, '/'));
        }
        if (this.matchBase) {
            if (opts.noglobstar) {
                throw new TypeError('base matching requires globstar');
            }
            pattern = pattern.map(p => (p.includes('/') ? p : `./**/${p}`));
        }
        this.pattern = pattern;
        this.platform = opts.platform || defaultPlatform;
        this.opts = { ...opts, platform: this.platform };
        if (opts.scurry) {
            this.scurry = opts.scurry;
            if (opts.nocase !== undefined &&
                opts.nocase !== opts.scurry.nocase) {
                throw new Error('nocase option contradicts provided scurry option');
            }
        }
        else {
            const Scurry = opts.platform === 'win32' ? path_scurry_1.PathScurryWin32
                : opts.platform === 'darwin' ? path_scurry_1.PathScurryDarwin
                    : opts.platform ? path_scurry_1.PathScurryPosix
                        : path_scurry_1.PathScurry;
            this.scurry = new Scurry(this.cwd, {
                nocase: opts.nocase,
                fs: opts.fs,
            });
        }
        this.nocase = this.scurry.nocase;
        // If you do nocase:true on a case-sensitive file system, then
        // we need to use regexps instead of strings for non-magic
        // path portions, because statting `aBc` won't return results
        // for the file `AbC` for example.
        const nocaseMagicOnly = this.platform === 'darwin' || this.platform === 'win32';
        const mmo = {
            // default nocase based on platform
            ...opts,
            dot: this.dot,
            matchBase: this.matchBase,
            nobrace: this.nobrace,
            nocase: this.nocase,
            nocaseMagicOnly,
            nocomment: true,
            noext: this.noext,
            nonegate: true,
            optimizationLevel: 2,
            platform: this.platform,
            windowsPathsNoEscape: this.windowsPathsNoEscape,
            debug: !!this.opts.debug,
        };
        const mms = this.pattern.map(p => new minimatch_1.Minimatch(p, mmo));
        const [matchSet, globParts] = mms.reduce((set, m) => {
            set[0].push(...m.set);
            set[1].push(...m.globParts);
            return set;
        }, [[], []]);
        this.patterns = matchSet.map((set, i) => {
            const g = globParts[i];
            /* c8 ignore start */
            if (!g)
                throw new Error('invalid pattern object');
            /* c8 ignore stop */
            return new pattern_js_1.Pattern(set, g, 0, this.platform);
        });
    }
    async walk() {
        // Walkers always return array of Path objects, so we just have to
        // coerce them into the right shape.  It will have already called
        // realpath() if the option was set to do so, so we know that's cached.
        // start out knowing the cwd, at least
        return [
            ...(await new walker_js_1.GlobWalker(this.patterns, this.scurry.cwd, {
                ...this.opts,
                maxDepth: this.maxDepth !== Infinity ?
                    this.maxDepth + this.scurry.cwd.depth()
                    : Infinity,
                platform: this.platform,
                nocase: this.nocase,
                includeChildMatches: this.includeChildMatches,
            }).walk()),
        ];
    }
    walkSync() {
        return [
            ...new walker_js_1.GlobWalker(this.patterns, this.scurry.cwd, {
                ...this.opts,
                maxDepth: this.maxDepth !== Infinity ?
                    this.maxDepth + this.scurry.cwd.depth()
                    : Infinity,
                platform: this.platform,
                nocase: this.nocase,
                includeChildMatches: this.includeChildMatches,
            }).walkSync(),
        ];
    }
    stream() {
        return new walker_js_1.GlobStream(this.patterns, this.scurry.cwd, {
            ...this.opts,
            maxDepth: this.maxDepth !== Infinity ?
                this.maxDepth + this.scurry.cwd.depth()
                : Infinity,
            platform: this.platform,
            nocase: this.nocase,
            includeChildMatches: this.includeChildMatches,
        }).stream();
    }
    streamSync() {
        return new walker_js_1.GlobStream(this.patterns, this.scurry.cwd, {
            ...this.opts,
            maxDepth: this.maxDepth !== Infinity ?
                this.maxDepth + this.scurry.cwd.depth()
                : Infinity,
            platform: this.platform,
            nocase: this.nocase,
            includeChildMatches: this.includeChildMatches,
        }).streamSync();
    }
    /**
     * Default sync iteration function. Returns a Generator that
     * iterates over the results.
     */
    iterateSync() {
        return this.streamSync()[Symbol.iterator]();
    }
    [Symbol.iterator]() {
        return this.iterateSync();
    }
    /**
     * Default async iteration function. Returns an AsyncGenerator that
     * iterates over the results.
     */
    iterate() {
        return this.stream()[Symbol.asyncIterator]();
    }
    [Symbol.asyncIterator]() {
        return this.iterate();
    }
}
exports.Glob = Glob;
//# sourceMappingURL=glob.js.map

/***/ }),

/***/ 5197:
/***/ ((__unused_webpack_module, exports, __nccwpck_require__) => {


Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.hasMagic = void 0;
const minimatch_1 = __nccwpck_require__(3790);
/**
 * Return true if the patterns provided contain any magic glob characters,
 * given the options provided.
 *
 * Brace expansion is not considered "magic" unless the `magicalBraces` option
 * is set, as brace expansion just turns one string into an array of strings.
 * So a pattern like `'x{a,b}y'` would return `false`, because `'xay'` and
 * `'xby'` both do not contain any magic glob characters, and it's treated the
 * same as if you had called it on `['xay', 'xby']`. When `magicalBraces:true`
 * is in the options, brace expansion _is_ treated as a pattern having magic.
 */
const hasMagic = (pattern, options = {}) => {
    if (!Array.isArray(pattern)) {
        pattern = [pattern];
    }
    for (const p of pattern) {
        if (new minimatch_1.Minimatch(p, options).hasMagic())
            return true;
    }
    return false;
};
exports.hasMagic = hasMagic;
//# sourceMappingURL=has-magic.js.map

/***/ }),

/***/ 5637:
/***/ ((__unused_webpack_module, exports, __nccwpck_require__) => {


// give it a pattern, and it'll be able to tell you if
// a given path should be ignored.
// Ignoring a path ignores its children if the pattern ends in /**
// Ignores are always parsed in dot:true mode
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.Ignore = void 0;
const minimatch_1 = __nccwpck_require__(3790);
const pattern_js_1 = __nccwpck_require__(7813);
const defaultPlatform = (typeof process === 'object' &&
    process &&
    typeof process.platform === 'string') ?
    process.platform
    : 'linux';
/**
 * Class used to process ignored patterns
 */
class Ignore {
    relative;
    relativeChildren;
    absolute;
    absoluteChildren;
    platform;
    mmopts;
    constructor(ignored, { nobrace, nocase, noext, noglobstar, platform = defaultPlatform, }) {
        this.relative = [];
        this.absolute = [];
        this.relativeChildren = [];
        this.absoluteChildren = [];
        this.platform = platform;
        this.mmopts = {
            dot: true,
            nobrace,
            nocase,
            noext,
            noglobstar,
            optimizationLevel: 2,
            platform,
            nocomment: true,
            nonegate: true,
        };
        for (const ign of ignored)
            this.add(ign);
    }
    add(ign) {
        // this is a little weird, but it gives us a clean set of optimized
        // minimatch matchers, without getting tripped up if one of them
        // ends in /** inside a brace section, and it's only inefficient at
        // the start of the walk, not along it.
        // It'd be nice if the Pattern class just had a .test() method, but
        // handling globstars is a bit of a pita, and that code already lives
        // in minimatch anyway.
        // Another way would be if maybe Minimatch could take its set/globParts
        // as an option, and then we could at least just use Pattern to test
        // for absolute-ness.
        // Yet another way, Minimatch could take an array of glob strings, and
        // a cwd option, and do the right thing.
        const mm = new minimatch_1.Minimatch(ign, this.mmopts);
        for (let i = 0; i < mm.set.length; i++) {
            const parsed = mm.set[i];
            const globParts = mm.globParts[i];
            /* c8 ignore start */
            if (!parsed || !globParts) {
                throw new Error('invalid pattern object');
            }
            // strip off leading ./ portions
            // https://github.com/isaacs/node-glob/issues/570
            while (parsed[0] === '.' && globParts[0] === '.') {
                parsed.shift();
                globParts.shift();
            }
            /* c8 ignore stop */
            const p = new pattern_js_1.Pattern(parsed, globParts, 0, this.platform);
            const m = new minimatch_1.Minimatch(p.globString(), this.mmopts);
            const children = globParts[globParts.length - 1] === '**';
            const absolute = p.isAbsolute();
            if (absolute)
                this.absolute.push(m);
            else
                this.relative.push(m);
            if (children) {
                if (absolute)
                    this.absoluteChildren.push(m);
                else
                    this.relativeChildren.push(m);
            }
        }
    }
    ignored(p) {
        const fullpath = p.fullpath();
        const fullpaths = `${fullpath}/`;
        const relative = p.relative() || '.';
        const relatives = `${relative}/`;
        for (const m of this.relative) {
            if (m.match(relative) || m.match(relatives))
                return true;
        }
        for (const m of this.absolute) {
            if (m.match(fullpath) || m.match(fullpaths))
                return true;
        }
        return false;
    }
    childrenIgnored(p) {
        const fullpath = p.fullpath() + '/';
        const relative = (p.relative() || '.') + '/';
        for (const m of this.relativeChildren) {
            if (m.match(relative))
                return true;
        }
        for (const m of this.absoluteChildren) {
            if (m.match(fullpath))
                return true;
        }
        return false;
    }
}
exports.Ignore = Ignore;
//# sourceMappingURL=ignore.js.map

/***/ }),

/***/ 1363:
/***/ ((__unused_webpack_module, exports, __nccwpck_require__) => {


Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.glob = exports.sync = exports.iterate = exports.iterateSync = exports.stream = exports.streamSync = exports.Ignore = exports.hasMagic = exports.Glob = exports.unescape = exports.escape = void 0;
exports.globStreamSync = globStreamSync;
exports.globStream = globStream;
exports.globSync = globSync;
exports.globIterateSync = globIterateSync;
exports.globIterate = globIterate;
const minimatch_1 = __nccwpck_require__(3790);
const glob_js_1 = __nccwpck_require__(2981);
const has_magic_js_1 = __nccwpck_require__(5197);
var minimatch_2 = __nccwpck_require__(3790);
Object.defineProperty(exports, "escape", ({ enumerable: true, get: function () { return minimatch_2.escape; } }));
Object.defineProperty(exports, "unescape", ({ enumerable: true, get: function () { return minimatch_2.unescape; } }));
var glob_js_2 = __nccwpck_require__(2981);
Object.defineProperty(exports, "Glob", ({ enumerable: true, get: function () { return glob_js_2.Glob; } }));
var has_magic_js_2 = __nccwpck_require__(5197);
Object.defineProperty(exports, "hasMagic", ({ enumerable: true, get: function () { return has_magic_js_2.hasMagic; } }));
var ignore_js_1 = __nccwpck_require__(5637);
Object.defineProperty(exports, "Ignore", ({ enumerable: true, get: function () { return ignore_js_1.Ignore; } }));
function globStreamSync(pattern, options = {}) {
    return new glob_js_1.Glob(pattern, options).streamSync();
}
function globStream(pattern, options = {}) {
    return new glob_js_1.Glob(pattern, options).stream();
}
function globSync(pattern, options = {}) {
    return new glob_js_1.Glob(pattern, options).walkSync();
}
async function glob_(pattern, options = {}) {
    return new glob_js_1.Glob(pattern, options).walk();
}
function globIterateSync(pattern, options = {}) {
    return new glob_js_1.Glob(pattern, options).iterateSync();
}
function globIterate(pattern, options = {}) {
    return new glob_js_1.Glob(pattern, options).iterate();
}
// aliases: glob.sync.stream() glob.stream.sync() glob.sync() etc
exports.streamSync = globStreamSync;
exports.stream = Object.assign(globStream, { sync: globStreamSync });
exports.iterateSync = globIterateSync;
exports.iterate = Object.assign(globIterate, {
    sync: globIterateSync,
});
exports.sync = Object.assign(globSync, {
    stream: globStreamSync,
    iterate: globIterateSync,
});
exports.glob = Object.assign(glob_, {
    glob: glob_,
    globSync,
    sync: exports.sync,
    globStream,
    stream: exports.stream,
    globStreamSync,
    streamSync: exports.streamSync,
    globIterate,
    iterate: exports.iterate,
    globIterateSync,
    iterateSync: exports.iterateSync,
    Glob: glob_js_1.Glob,
    hasMagic: has_magic_js_1.hasMagic,
    escape: minimatch_1.escape,
    unescape: minimatch_1.unescape,
});
exports.glob.glob = exports.glob;
//# sourceMappingURL=index.js.map

/***/ }),

/***/ 7813:
/***/ ((__unused_webpack_module, exports, __nccwpck_require__) => {


// this is just a very light wrapper around 2 arrays with an offset index
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.Pattern = void 0;
const minimatch_1 = __nccwpck_require__(3790);
const isPatternList = (pl) => pl.length >= 1;
const isGlobList = (gl) => gl.length >= 1;
/**
 * An immutable-ish view on an array of glob parts and their parsed
 * results
 */
class Pattern {
    #patternList;
    #globList;
    #index;
    length;
    #platform;
    #rest;
    #globString;
    #isDrive;
    #isUNC;
    #isAbsolute;
    #followGlobstar = true;
    constructor(patternList, globList, index, platform) {
        if (!isPatternList(patternList)) {
            throw new TypeError('empty pattern list');
        }
        if (!isGlobList(globList)) {
            throw new TypeError('empty glob list');
        }
        if (globList.length !== patternList.length) {
            throw new TypeError('mismatched pattern list and glob list lengths');
        }
        this.length = patternList.length;
        if (index < 0 || index >= this.length) {
            throw new TypeError('index out of range');
        }
        this.#patternList = patternList;
        this.#globList = globList;
        this.#index = index;
        this.#platform = platform;
        // normalize root entries of absolute patterns on initial creation.
        if (this.#index === 0) {
            // c: => ['c:/']
            // C:/ => ['C:/']
            // C:/x => ['C:/', 'x']
            // //host/share => ['//host/share/']
            // //host/share/ => ['//host/share/']
