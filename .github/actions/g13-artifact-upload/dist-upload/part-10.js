            // The Content-IDs are set to a valid index in the subrequests we sent. In the status code 202 path, we could expect it
            // to be 1-1 mapping from the [0, subRequests.size) to the Content-IDs returned. If not, we simply don't return that
            // unexpected subResponse in the parsed reponse and we can always look it up in the raw response for debugging purpose.
            if (contentId !== NOT_FOUND &&
                Number.isInteger(contentId) &&
                contentId >= 0 &&
                contentId < this.subRequests.size &&
                deserializedSubResponses[contentId] === undefined) {
                deserializedSubResponse._request = this.subRequests.get(contentId);
                deserializedSubResponses[contentId] = deserializedSubResponse;
            }
            else {
                storage_blob_dist_esm_log_logger.error(`subResponses[${index}] is dropped as the Content-ID is not found or invalid, Content-ID: ${contentId}`);
            }
            if (subRespFailed) {
                subResponsesFailedCount++;
            }
            else {
                subResponsesSucceededCount++;
            }
        }
        return {
            subResponses: deserializedSubResponses,
            subResponsesSucceededCount: subResponsesSucceededCount,
            subResponsesFailedCount: subResponsesFailedCount,
        };
    }
}
//# sourceMappingURL=BatchResponseParser.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/utils/Mutex.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
var MutexLockStatus;
(function (MutexLockStatus) {
    MutexLockStatus[MutexLockStatus["LOCKED"] = 0] = "LOCKED";
    MutexLockStatus[MutexLockStatus["UNLOCKED"] = 1] = "UNLOCKED";
})(MutexLockStatus || (MutexLockStatus = {}));
/**
 * An async mutex lock.
 */
class Mutex {
    /**
     * Lock for a specific key. If the lock has been acquired by another customer, then
     * will wait until getting the lock.
     *
     * @param key - lock key
     */
    static async lock(key) {
        return new Promise((resolve) => {
            if (this.keys[key] === undefined || this.keys[key] === MutexLockStatus.UNLOCKED) {
                this.keys[key] = MutexLockStatus.LOCKED;
                resolve();
            }
            else {
                this.onUnlockEvent(key, () => {
                    this.keys[key] = MutexLockStatus.LOCKED;
                    resolve();
                });
            }
        });
    }
    /**
     * Unlock a key.
     *
     * @param key -
     */
    static async unlock(key) {
        return new Promise((resolve) => {
            if (this.keys[key] === MutexLockStatus.LOCKED) {
                this.emitUnlockEvent(key);
            }
            delete this.keys[key];
            resolve();
        });
    }
    static keys = {};
    static listeners = {};
    static onUnlockEvent(key, handler) {
        if (this.listeners[key] === undefined) {
            this.listeners[key] = [handler];
        }
        else {
            this.listeners[key].push(handler);
        }
    }
    static emitUnlockEvent(key) {
        if (this.listeners[key] !== undefined && this.listeners[key].length > 0) {
            const handler = this.listeners[key].shift();
            setImmediate(() => {
                handler.call(this);
            });
        }
    }
}
//# sourceMappingURL=Mutex.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/BlobBatch.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.













/**
 * A BlobBatch represents an aggregated set of operations on blobs.
 * Currently, only `delete` and `setAccessTier` are supported.
 */
class BlobBatch {
    batchRequest;
    batch = "batch";
    batchType;
    constructor() {
        this.batchRequest = new InnerBatchRequest();
    }
    /**
     * Get the value of Content-Type for a batch request.
     * The value must be multipart/mixed with a batch boundary.
     * Example: multipart/mixed; boundary=batch_a81786c8-e301-4e42-a729-a32ca24ae252
     */
    getMultiPartContentType() {
        return this.batchRequest.getMultipartContentType();
    }
    /**
     * Get assembled HTTP request body for sub requests.
     */
    getHttpRequestBody() {
        return this.batchRequest.getHttpRequestBody();
    }
    /**
     * Get sub requests that are added into the batch request.
     */
    getSubRequests() {
        return this.batchRequest.getSubRequests();
    }
    async addSubRequestInternal(subRequest, assembleSubRequestFunc) {
        await Mutex.lock(this.batch);
        try {
            this.batchRequest.preAddSubRequest(subRequest);
            await assembleSubRequestFunc();
            this.batchRequest.postAddSubRequest(subRequest);
        }
        finally {
            await Mutex.unlock(this.batch);
        }
    }
    setBatchType(batchType) {
        if (!this.batchType) {
            this.batchType = batchType;
        }
        if (this.batchType !== batchType) {
            throw new RangeError(`BlobBatch only supports one operation type per batch and it already is being used for ${this.batchType} operations.`);
        }
    }
    async deleteBlob(urlOrBlobClient, credentialOrOptions, options) {
        let url;
        let credential;
        if (typeof urlOrBlobClient === "string" &&
            ((esm_isNodeLike && credentialOrOptions instanceof StorageSharedKeyCredential) ||
                credentialOrOptions instanceof AnonymousCredential ||
                isTokenCredential(credentialOrOptions))) {
            // First overload
            url = urlOrBlobClient;
            credential = credentialOrOptions;
        }
        else if (urlOrBlobClient instanceof BlobClient) {
            // Second overload
            url = urlOrBlobClient.url;
            credential = urlOrBlobClient.credential;
            options = credentialOrOptions;
        }
        else {
            throw new RangeError("Invalid arguments. Either url and credential, or BlobClient need be provided.");
        }
        if (!options) {
            options = {};
        }
        return tracingClient.withSpan("BatchDeleteRequest-addSubRequest", options, async (updatedOptions) => {
            this.setBatchType("delete");
            await this.addSubRequestInternal({
                url: url,
                credential: credential,
            }, async () => {
                await new BlobClient(url, this.batchRequest.createPipeline(credential)).delete(updatedOptions);
            });
        });
    }
    async setBlobAccessTier(urlOrBlobClient, credentialOrTier, tierOrOptions, options) {
        let url;
        let credential;
        let tier;
        if (typeof urlOrBlobClient === "string" &&
            ((esm_isNodeLike && credentialOrTier instanceof StorageSharedKeyCredential) ||
                credentialOrTier instanceof AnonymousCredential ||
                isTokenCredential(credentialOrTier))) {
            // First overload
            url = urlOrBlobClient;
            credential = credentialOrTier;
            tier = tierOrOptions;
        }
        else if (urlOrBlobClient instanceof BlobClient) {
            // Second overload
            url = urlOrBlobClient.url;
            credential = urlOrBlobClient.credential;
            tier = credentialOrTier;
            options = tierOrOptions;
        }
        else {
            throw new RangeError("Invalid arguments. Either url and credential, or BlobClient need be provided.");
        }
        if (!options) {
            options = {};
        }
        return tracingClient.withSpan("BatchSetTierRequest-addSubRequest", options, async (updatedOptions) => {
            this.setBatchType("setAccessTier");
            await this.addSubRequestInternal({
                url: url,
                credential: credential,
            }, async () => {
                await new BlobClient(url, this.batchRequest.createPipeline(credential)).setAccessTier(tier, updatedOptions);
            });
        });
    }
}
/**
 * Inner batch request class which is responsible for assembling and serializing sub requests.
 * See https://learn.microsoft.com/rest/api/storageservices/blob-batch#request-body for how requests are assembled.
 */
class InnerBatchRequest {
    operationCount;
    body;
    subRequests;
    boundary;
    subRequestPrefix;
    multipartContentType;
    batchRequestEnding;
    constructor() {
        this.operationCount = 0;
        this.body = "";
        const tempGuid = esm_randomUUID();
        // batch_{batchid}
        this.boundary = `batch_${tempGuid}`;
        // --batch_{batchid}
        // Content-Type: application/http
        // Content-Transfer-Encoding: binary
        this.subRequestPrefix = `--${this.boundary}${HTTP_LINE_ENDING}${utils_constants_HeaderConstants.CONTENT_TYPE}: application/http${HTTP_LINE_ENDING}${utils_constants_HeaderConstants.CONTENT_TRANSFER_ENCODING}: binary`;
        // multipart/mixed; boundary=batch_{batchid}
        this.multipartContentType = `multipart/mixed; boundary=${this.boundary}`;
        // --batch_{batchid}--
        this.batchRequestEnding = `--${this.boundary}--`;
        this.subRequests = new Map();
    }
    /**
     * Create pipeline to assemble sub requests. The idea here is to use existing
     * credential and serialization/deserialization components, with additional policies to
     * filter unnecessary headers, assemble sub requests into request's body
     * and intercept request from going to wire.
     * @param credential -  Such as AnonymousCredential, StorageSharedKeyCredential or any credential from the `@azure/identity` package to authenticate requests to the service. You can also provide an object that implements the TokenCredential interface. If not specified, AnonymousCredential is used.
     */
    createPipeline(credential) {
        const corePipeline = esm_pipeline_createEmptyPipeline();
        corePipeline.addPolicy(serializationPolicy({
            stringifyXML: stringifyXML,
            serializerOptions: {
                xml: {
                    xmlCharKey: "#",
                },
            },
        }), { phase: "Serialize" });
        // Use batch header filter policy to exclude unnecessary headers
        corePipeline.addPolicy(batchHeaderFilterPolicy());
        // Use batch assemble policy to assemble request and intercept request from going to wire
        corePipeline.addPolicy(batchRequestAssemblePolicy(this), { afterPhase: "Sign" });
        if (isTokenCredential(credential)) {
            corePipeline.addPolicy(bearerTokenAuthenticationPolicy({
                credential,
                scopes: StorageOAuthScopes,
                challengeCallbacks: { authorizeRequestOnChallenge: authorizeRequestOnTenantChallenge },
            }), { phase: "Sign" });
        }
        else if (credential instanceof StorageSharedKeyCredential) {
            corePipeline.addPolicy(storageSharedKeyCredentialPolicy({
                accountName: credential.accountName,
                accountKey: credential.accountKey,
            }), { phase: "Sign" });
        }
        const pipeline = new Pipeline([]);
        // attach the v2 pipeline to this one
        pipeline._credential = credential;
        pipeline._corePipeline = corePipeline;
        return pipeline;
    }
    appendSubRequestToBody(request) {
        // Start to assemble sub request
        this.body += [
            this.subRequestPrefix, // sub request constant prefix
            `${utils_constants_HeaderConstants.CONTENT_ID}: ${this.operationCount}`, // sub request's content ID
            "", // empty line after sub request's content ID
            `${request.method.toString()} ${utils_common_getURLPathAndQuery(request.url)} ${HTTP_VERSION_1_1}${HTTP_LINE_ENDING}`, // sub request start line with method
        ].join(HTTP_LINE_ENDING);
        for (const [name, value] of request.headers) {
            this.body += `${name}: ${value}${HTTP_LINE_ENDING}`;
        }
        this.body += HTTP_LINE_ENDING; // sub request's headers need be ending with an empty line
        // No body to assemble for current batch request support
        // End to assemble sub request
    }
    preAddSubRequest(subRequest) {
        if (this.operationCount >= BATCH_MAX_REQUEST) {
            throw new RangeError(`Cannot exceed ${BATCH_MAX_REQUEST} sub requests in a single batch`);
        }
        // Fast fail if url for sub request is invalid
        const path = utils_common_getURLPath(subRequest.url);
        if (!path || path === "") {
            throw new RangeError(`Invalid url for sub request: '${subRequest.url}'`);
        }
    }
    postAddSubRequest(subRequest) {
        this.subRequests.set(this.operationCount, subRequest);
        this.operationCount++;
    }
    // Return the http request body with assembling the ending line to the sub request body.
    getHttpRequestBody() {
        return `${this.body}${this.batchRequestEnding}${HTTP_LINE_ENDING}`;
    }
    getMultipartContentType() {
        return this.multipartContentType;
    }
    getSubRequests() {
        return this.subRequests;
    }
}
function batchRequestAssemblePolicy(batchRequest) {
    return {
        name: "batchRequestAssemblePolicy",
        async sendRequest(request) {
            batchRequest.appendSubRequestToBody(request);
            return {
                request,
                status: 200,
                headers: esm_httpHeaders_createHttpHeaders(),
            };
        },
    };
}
function batchHeaderFilterPolicy() {
    return {
        name: "batchHeaderFilterPolicy",
        async sendRequest(request, next) {
            let xMsHeaderName = "";
            for (const [name] of request.headers) {
                if (utils_common_iEqual(name, utils_constants_HeaderConstants.X_MS_VERSION)) {
                    xMsHeaderName = name;
                }
            }
            if (xMsHeaderName !== "") {
                request.headers.delete(xMsHeaderName); // The subrequests should not have the x-ms-version header.
            }
            return next(request);
        },
    };
}
//# sourceMappingURL=BlobBatch.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/BlobBatchClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.








/**
 * A BlobBatchClient allows you to make batched requests to the Azure Storage Blob service.
 *
 * @see https://learn.microsoft.com/rest/api/storageservices/blob-batch
 */
class BlobBatchClient {
    serviceOrContainerContext;
    constructor(url, credentialOrPipeline, 
    // Legacy, no fix for eslint error without breaking. Disable it for this interface.
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    options) {
        let pipeline;
        if (isPipelineLike(credentialOrPipeline)) {
            pipeline = credentialOrPipeline;
        }
        else if (!credentialOrPipeline) {
            // no credential provided
            pipeline = newPipeline(new AnonymousCredential(), options);
        }
        else {
            pipeline = newPipeline(credentialOrPipeline, options);
        }
        const storageClientContext = new StorageContextClient(url, getCoreClientOptions(pipeline));
        const path = utils_common_getURLPath(url);
        if (path && path !== "/") {
            // Container scoped.
            this.serviceOrContainerContext = storageClientContext.container;
        }
        else {
            this.serviceOrContainerContext = storageClientContext.service;
        }
    }
    /**
     * Creates a {@link BlobBatch}.
     * A BlobBatch represents an aggregated set of operations on blobs.
     */
    createBatch() {
        return new BlobBatch();
    }
    async deleteBlobs(urlsOrBlobClients, credentialOrOptions, 
    // Legacy, no fix for eslint error without breaking. Disable it for this interface.
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    options) {
        const batch = new BlobBatch();
        for (const urlOrBlobClient of urlsOrBlobClients) {
            if (typeof urlOrBlobClient === "string") {
                await batch.deleteBlob(urlOrBlobClient, credentialOrOptions, options);
            }
            else {
                await batch.deleteBlob(urlOrBlobClient, credentialOrOptions);
            }
        }
        return this.submitBatch(batch);
    }
    async setBlobsAccessTier(urlsOrBlobClients, credentialOrTier, tierOrOptions, 
    // Legacy, no fix for eslint error without breaking. Disable it for this interface.
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    options) {
        const batch = new BlobBatch();
        for (const urlOrBlobClient of urlsOrBlobClients) {
            if (typeof urlOrBlobClient === "string") {
                await batch.setBlobAccessTier(urlOrBlobClient, credentialOrTier, tierOrOptions, options);
            }
            else {
                await batch.setBlobAccessTier(urlOrBlobClient, credentialOrTier, tierOrOptions);
            }
        }
        return this.submitBatch(batch);
    }
    /**
     * Submit batch request which consists of multiple subrequests.
     *
     * Get `blobBatchClient` and other details before running the snippets.
     * `blobServiceClient.getBlobBatchClient()` gives the `blobBatchClient`
     *
     * Example usage:
     *
     * ```ts snippet:BlobBatchClientSubmitBatch
     * import { DefaultAzureCredential } from "@azure/identity";
     * import { BlobServiceClient, BlobBatch } from "@azure/storage-blob";
     *
     * const account = "<account>";
     * const credential = new DefaultAzureCredential();
     * const blobServiceClient = new BlobServiceClient(
     *   `https://${account}.blob.core.windows.net`,
     *   credential,
     * );
     *
     * const containerName = "<container name>";
     * const containerClient = blobServiceClient.getContainerClient(containerName);
     * const blobBatchClient = containerClient.getBlobBatchClient();
     *
     * const batchRequest = new BlobBatch();
     * await batchRequest.deleteBlob("<blob-url-1>", credential);
     * await batchRequest.deleteBlob("<blob-url-2>", credential, {
     *   deleteSnapshots: "include",
     * });
     * const batchResp = await blobBatchClient.submitBatch(batchRequest);
     * console.log(batchResp.subResponsesSucceededCount);
     * ```
     *
     * Example using a lease:
     *
     * ```ts snippet:BlobBatchClientSubmitBatchWithLease
     * import { DefaultAzureCredential } from "@azure/identity";
     * import { BlobServiceClient, BlobBatch } from "@azure/storage-blob";
     *
     * const account = "<account>";
     * const credential = new DefaultAzureCredential();
     * const blobServiceClient = new BlobServiceClient(
     *   `https://${account}.blob.core.windows.net`,
     *   credential,
     * );
     *
     * const containerName = "<container name>";
     * const containerClient = blobServiceClient.getContainerClient(containerName);
     * const blobBatchClient = containerClient.getBlobBatchClient();
     * const blobClient = containerClient.getBlobClient("<blob name>");
     *
     * const batchRequest = new BlobBatch();
     * await batchRequest.setBlobAccessTier(blobClient, "Cool");
     * await batchRequest.setBlobAccessTier(blobClient, "Cool", {
     *   conditions: { leaseId: "<lease-id>" },
     * });
     * const batchResp = await blobBatchClient.submitBatch(batchRequest);
     * console.log(batchResp.subResponsesSucceededCount);
     * ```
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/blob-batch
     *
     * @param batchRequest - A set of Delete or SetTier operations.
     * @param options -
     */
    async submitBatch(batchRequest, options = {}) {
        if (!batchRequest || batchRequest.getSubRequests().size === 0) {
            throw new RangeError("Batch request should contain one or more sub requests.");
        }
        return tracingClient.withSpan("BlobBatchClient-submitBatch", options, async (updatedOptions) => {
            const batchRequestBody = batchRequest.getHttpRequestBody();
            // ServiceSubmitBatchResponseModel and ContainerSubmitBatchResponse are compatible for now.
            const rawBatchResponse = utils_common_assertResponse((await this.serviceOrContainerContext.submitBatch(utf8ByteLength(batchRequestBody), batchRequest.getMultiPartContentType(), batchRequestBody, {
                ...updatedOptions,
            })));
            // Parse the sub responses result, if logic reaches here(i.e. the batch request succeeded with status code 202).
            const batchResponseParser = new BatchResponseParser(rawBatchResponse, batchRequest.getSubRequests());
            const responseSummary = await batchResponseParser.parseBatchResponse();
            const res = {
                _response: rawBatchResponse._response,
                contentType: rawBatchResponse.contentType,
                errorCode: rawBatchResponse.errorCode,
                requestId: rawBatchResponse.requestId,
                clientRequestId: rawBatchResponse.clientRequestId,
                version: rawBatchResponse.version,
                subResponses: responseSummary.subResponses,
                subResponsesSucceededCount: responseSummary.subResponsesSucceededCount,
                subResponsesFailedCount: responseSummary.subResponsesFailedCount,
            };
            return res;
        });
    }
}
//# sourceMappingURL=BlobBatchClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/ContainerClient.js












/**
 * A ContainerClient represents a URL to the Azure Storage container allowing you to manipulate its blobs.
 */
class ContainerClient extends StorageClient_StorageClient {
    /**
     * containerContext provided by protocol layer.
     */
    containerContext;
    _containerName;
    /**
     * The name of the container.
     */
    get containerName() {
        return this._containerName;
    }
    constructor(urlOrConnectionString, credentialOrPipelineOrContainerName, 
    // Legacy, no fix for eslint error without breaking. Disable it for this interface.
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    options) {
        let pipeline;
        let url;
        options = options || {};
        if (isPipelineLike(credentialOrPipelineOrContainerName)) {
            // (url: string, pipeline: Pipeline)
            url = urlOrConnectionString;
            pipeline = credentialOrPipelineOrContainerName;
        }
        else if ((esm_isNodeLike && credentialOrPipelineOrContainerName instanceof StorageSharedKeyCredential) ||
            credentialOrPipelineOrContainerName instanceof AnonymousCredential ||
            isTokenCredential(credentialOrPipelineOrContainerName)) {
            // (url: string, credential?: StorageSharedKeyCredential | AnonymousCredential | TokenCredential, options?: StoragePipelineOptions)
            url = urlOrConnectionString;
            pipeline = newPipeline(credentialOrPipelineOrContainerName, options);
        }
        else if (!credentialOrPipelineOrContainerName &&
            typeof credentialOrPipelineOrContainerName !== "string") {
            // (url: string, credential?: StorageSharedKeyCredential | AnonymousCredential | TokenCredential, options?: StoragePipelineOptions)
            // The second parameter is undefined. Use anonymous credential.
            url = urlOrConnectionString;
            pipeline = newPipeline(new AnonymousCredential(), options);
        }
        else if (credentialOrPipelineOrContainerName &&
            typeof credentialOrPipelineOrContainerName === "string") {
            // (connectionString: string, containerName: string, blobName: string, options?: StoragePipelineOptions)
            const containerName = credentialOrPipelineOrContainerName;
            const extractedCreds = utils_common_extractConnectionStringParts(urlOrConnectionString);
            if (extractedCreds.kind === "AccountConnString") {
                if (esm_isNodeLike) {
                    const sharedKeyCredential = new StorageSharedKeyCredential(extractedCreds.accountName, extractedCreds.accountKey);
                    url = utils_common_appendToURLPath(extractedCreds.url, encodeURIComponent(containerName));
                    if (!options.proxyOptions) {
                        options.proxyOptions = proxyPolicy_getDefaultProxySettings(extractedCreds.proxyUri);
                    }
                    pipeline = newPipeline(sharedKeyCredential, options);
                }
                else {
                    throw new Error("Account connection string is only supported in Node.js environment");
                }
            }
            else if (extractedCreds.kind === "SASConnString") {
                url =
                    utils_common_appendToURLPath(extractedCreds.url, encodeURIComponent(containerName)) +
                        "?" +
                        extractedCreds.accountSas;
                pipeline = newPipeline(new AnonymousCredential(), options);
            }
            else {
                throw new Error("Connection string must be either an Account connection string or a SAS connection string");
            }
        }
        else {
            throw new Error("Expecting non-empty strings for containerName parameter");
        }
        super(url, pipeline);
        this._containerName = this.getContainerNameFromUrl();
        this.containerContext = this.storageClientContext.container;
    }
    /**
     * Creates a new container under the specified account. If the container with
     * the same name already exists, the operation fails.
     * @see https://learn.microsoft.com/rest/api/storageservices/create-container
     * Naming rules: @see https://learn.microsoft.com/rest/api/storageservices/naming-and-referencing-containers--blobs--and-metadata
     *
     * @param options - Options to Container Create operation.
     *
     *
     * Example usage:
     *
     * ```ts snippet:ContainerClientCreate
     * import { BlobServiceClient } from "@azure/storage-blob";
     * import { DefaultAzureCredential } from "@azure/identity";
     *
     * const account = "<account>";
     * const blobServiceClient = new BlobServiceClient(
     *   `https://${account}.blob.core.windows.net`,
     *   new DefaultAzureCredential(),
     * );
     *
     * const containerName = "<container name>";
     * const containerClient = blobServiceClient.getContainerClient(containerName);
     * const createContainerResponse = await containerClient.create();
     * console.log("Container was created successfully", createContainerResponse.requestId);
     * ```
     */
    async create(options = {}) {
        return tracingClient.withSpan("ContainerClient-create", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.containerContext.create(updatedOptions));
        });
    }
    /**
     * Creates a new container under the specified account. If the container with
     * the same name already exists, it is not changed.
     * @see https://learn.microsoft.com/rest/api/storageservices/create-container
     * Naming rules: @see https://learn.microsoft.com/rest/api/storageservices/naming-and-referencing-containers--blobs--and-metadata
     *
     * @param options -
     */
    async createIfNotExists(options = {}) {
        return tracingClient.withSpan("ContainerClient-createIfNotExists", options, async (updatedOptions) => {
            try {
                const res = await this.create(updatedOptions);
                return {
                    succeeded: true,
                    ...res,
                    _response: res._response, // _response is made non-enumerable
                };
            }
            catch (e) {
                if (e.details?.errorCode === "ContainerAlreadyExists") {
                    return {
                        succeeded: false,
                        ...e.response?.parsedHeaders,
                        _response: e.response,
                    };
                }
                else {
                    throw e;
                }
            }
        });
    }
    /**
     * Returns true if the Azure container resource represented by this client exists; false otherwise.
     *
     * NOTE: use this function with care since an existing container might be deleted by other clients or
     * applications. Vice versa new containers with the same name might be added by other clients or
     * applications after this function completes.
     *
     * @param options -
     */
    async exists(options = {}) {
        return tracingClient.withSpan("ContainerClient-exists", options, async (updatedOptions) => {
            try {
                await this.getProperties({
                    abortSignal: options.abortSignal,
                    tracingOptions: updatedOptions.tracingOptions,
                });
                return true;
            }
            catch (e) {
                if (e.statusCode === 404) {
                    return false;
                }
                throw e;
            }
        });
    }
    /**
     * Creates a {@link BlobClient}
     *
     * @param blobName - A blob name
     * @returns A new BlobClient object for the given blob name.
     */
    getBlobClient(blobName) {
        return new BlobClient(utils_common_appendToURLPath(this.url, utils_common_EscapePath(blobName)), this.pipeline);
    }
    /**
     * Creates an {@link AppendBlobClient}
     *
     * @param blobName - An append blob name
     */
    getAppendBlobClient(blobName) {
        return new AppendBlobClient(utils_common_appendToURLPath(this.url, utils_common_EscapePath(blobName)), this.pipeline);
    }
    /**
     * Creates a {@link BlockBlobClient}
     *
     * @param blobName - A block blob name
     *
     *
     * Example usage:
     *
     * ```ts snippet:ClientsUpload
     * import { BlobServiceClient } from "@azure/storage-blob";
     * import { DefaultAzureCredential } from "@azure/identity";
     *
     * const account = "<account>";
     * const blobServiceClient = new BlobServiceClient(
     *   `https://${account}.blob.core.windows.net`,
     *   new DefaultAzureCredential(),
     * );
     *
     * const containerName = "<container name>";
     * const blobName = "<blob name>";
     * const containerClient = blobServiceClient.getContainerClient(containerName);
     * const blockBlobClient = containerClient.getBlockBlobClient(blobName);
     *
     * const content = "Hello world!";
     * const uploadBlobResponse = await blockBlobClient.upload(content, content.length);
     * ```
     */
    getBlockBlobClient(blobName) {
        return new BlockBlobClient(utils_common_appendToURLPath(this.url, utils_common_EscapePath(blobName)), this.pipeline);
    }
    /**
     * Creates a {@link PageBlobClient}
     *
     * @param blobName - A page blob name
     */
    getPageBlobClient(blobName) {
        return new PageBlobClient(utils_common_appendToURLPath(this.url, utils_common_EscapePath(blobName)), this.pipeline);
    }
    /**
     * Returns all user-defined metadata and system properties for the specified
     * container. The data returned does not include the container's list of blobs.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-container-properties
     *
     * WARNING: The `metadata` object returned in the response will have its keys in lowercase, even if
     * they originally contained uppercase characters. This differs from the metadata keys returned by
     * the `listContainers` method of {@link BlobServiceClient} using the `includeMetadata` option, which
     * will retain their original casing.
     *
     * @param options - Options to Container Get Properties operation.
     */
    async getProperties(options = {}) {
        if (!options.conditions) {
            options.conditions = {};
        }
        return tracingClient.withSpan("ContainerClient-getProperties", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.containerContext.getProperties({
                abortSignal: options.abortSignal,
                ...options.conditions,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Marks the specified container for deletion. The container and any blobs
     * contained within it are later deleted during garbage collection.
     * @see https://learn.microsoft.com/rest/api/storageservices/delete-container
     *
     * @param options - Options to Container Delete operation.
     */
    async delete(options = {}) {
        if (!options.conditions) {
            options.conditions = {};
        }
        return tracingClient.withSpan("ContainerClient-delete", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.containerContext.delete({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: options.conditions,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Marks the specified container for deletion if it exists. The container and any blobs
     * contained within it are later deleted during garbage collection.
     * @see https://learn.microsoft.com/rest/api/storageservices/delete-container
     *
     * @param options - Options to Container Delete operation.
     */
    async deleteIfExists(options = {}) {
        return tracingClient.withSpan("ContainerClient-deleteIfExists", options, async (updatedOptions) => {
            try {
                const res = await this.delete(updatedOptions);
                return {
                    succeeded: true,
                    ...res,
                    _response: res._response,
                };
            }
            catch (e) {
                if (e.details?.errorCode === "ContainerNotFound") {
                    return {
                        succeeded: false,
                        ...e.response?.parsedHeaders,
                        _response: e.response,
                    };
                }
                throw e;
            }
        });
    }
    /**
     * Sets one or more user-defined name-value pairs for the specified container.
     *
     * If no option provided, or no metadata defined in the parameter, the container
     * metadata will be removed.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/set-container-metadata
     *
     * @param metadata - Replace existing metadata with this value.
     *                            If no value provided the existing metadata will be removed.
     * @param options - Options to Container Set Metadata operation.
     */
    async setMetadata(metadata, options = {}) {
        if (!options.conditions) {
            options.conditions = {};
        }
        if (options.conditions.ifUnmodifiedSince) {
            throw new RangeError("the IfUnmodifiedSince must have their default values because they are ignored by the blob service");
        }
        return tracingClient.withSpan("ContainerClient-setMetadata", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.containerContext.setMetadata({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                metadata,
                modifiedAccessConditions: options.conditions,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Gets the permissions for the specified container. The permissions indicate
     * whether container data may be accessed publicly.
     *
     * WARNING: JavaScript Date will potentially lose precision when parsing startsOn and expiresOn strings.
     * For example, new Date("2018-12-31T03:44:23.8827891Z").toISOString() will get "2018-12-31T03:44:23.882Z".
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/get-container-acl
     *
     * @param options - Options to Container Get Access Policy operation.
     */
    async getAccessPolicy(options = {}) {
        if (!options.conditions) {
            options.conditions = {};
        }
        return tracingClient.withSpan("ContainerClient-getAccessPolicy", options, async (updatedOptions) => {
            const response = utils_common_assertResponse(await this.containerContext.getAccessPolicy({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                tracingOptions: updatedOptions.tracingOptions,
            }));
            const res = {
                _response: response._response,
                blobPublicAccess: response.blobPublicAccess,
                date: response.date,
                etag: response.etag,
                errorCode: response.errorCode,
                lastModified: response.lastModified,
                requestId: response.requestId,
                clientRequestId: response.clientRequestId,
                signedIdentifiers: [],
                version: response.version,
            };
            for (const identifier of response) {
                let accessPolicy = undefined;
                if (identifier.accessPolicy) {
                    accessPolicy = {
                        permissions: identifier.accessPolicy.permissions,
                    };
                    if (identifier.accessPolicy.expiresOn) {
                        accessPolicy.expiresOn = new Date(identifier.accessPolicy.expiresOn);
                    }
                    if (identifier.accessPolicy.startsOn) {
                        accessPolicy.startsOn = new Date(identifier.accessPolicy.startsOn);
                    }
                }
                res.signedIdentifiers.push({
                    accessPolicy,
                    id: identifier.id,
                });
            }
            return res;
        });
    }
    /**
     * Sets the permissions for the specified container. The permissions indicate
     * whether blobs in a container may be accessed publicly.
     *
     * When you set permissions for a container, the existing permissions are replaced.
     * If no access or containerAcl provided, the existing container ACL will be
     * removed.
     *
     * When you establish a stored access policy on a container, it may take up to 30 seconds to take effect.
     * During this interval, a shared access signature that is associated with the stored access policy will
     * fail with status code 403 (Forbidden), until the access policy becomes active.
     * @see https://learn.microsoft.com/rest/api/storageservices/set-container-acl
     *
     * @param access - The level of public access to data in the container.
     * @param containerAcl - Array of elements each having a unique Id and details of the access policy.
     * @param options - Options to Container Set Access Policy operation.
     */
    async setAccessPolicy(access, containerAcl, options = {}) {
        options.conditions = options.conditions || {};
        return tracingClient.withSpan("ContainerClient-setAccessPolicy", options, async (updatedOptions) => {
            const acl = [];
            for (const identifier of containerAcl || []) {
                acl.push({
                    accessPolicy: {
                        expiresOn: identifier.accessPolicy.expiresOn
                            ? utils_common_truncatedISO8061Date(identifier.accessPolicy.expiresOn)
                            : "",
                        permissions: identifier.accessPolicy.permissions,
                        startsOn: identifier.accessPolicy.startsOn
                            ? utils_common_truncatedISO8061Date(identifier.accessPolicy.startsOn)
                            : "",
                    },
                    id: identifier.id,
                });
            }
            return utils_common_assertResponse(await this.containerContext.setAccessPolicy({
                abortSignal: options.abortSignal,
                access,
                containerAcl: acl,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: options.conditions,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Get a {@link BlobLeaseClient} that manages leases on the container.
     *
     * @param proposeLeaseId - Initial proposed lease Id.
     * @returns A new BlobLeaseClient object for managing leases on the container.
     */
    getBlobLeaseClient(proposeLeaseId) {
        return new BlobLeaseClient(this, proposeLeaseId);
    }
    /**
     * Creates a new block blob, or updates the content of an existing block blob.
     *
     * Updating an existing block blob overwrites any existing metadata on the blob.
     * Partial updates are not supported; the content of the existing blob is
     * overwritten with the new content. To perform a partial update of a block blob's,
     * use {@link BlockBlobClient.stageBlock} and {@link BlockBlobClient.commitBlockList}.
     *
     * This is a non-parallel uploading method, please use {@link BlockBlobClient.uploadFile},
     * {@link BlockBlobClient.uploadStream} or {@link BlockBlobClient.uploadBrowserData} for better
     * performance with concurrency uploading.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/put-blob
     *
     * @param blobName - Name of the block blob to create or update.
     * @param body - Blob, string, ArrayBuffer, ArrayBufferView or a function
     *                               which returns a new Readable stream whose offset is from data source beginning.
     * @param contentLength - Length of body in bytes. Use Buffer.byteLength() to calculate body length for a
     *                               string including non non-Base64/Hex-encoded characters.
     * @param options - Options to configure the Block Blob Upload operation.
     * @returns Block Blob upload response data and the corresponding BlockBlobClient instance.
     */
    async uploadBlockBlob(blobName, body, contentLength, options = {}) {
        return tracingClient.withSpan("ContainerClient-uploadBlockBlob", options, async (updatedOptions) => {
            const blockBlobClient = this.getBlockBlobClient(blobName);
            const response = await blockBlobClient.upload(body, contentLength, updatedOptions);
            return {
                blockBlobClient,
                response,
            };
        });
    }
    /**
     * Marks the specified blob or snapshot for deletion. The blob is later deleted
     * during garbage collection. Note that in order to delete a blob, you must delete
     * all of its snapshots. You can delete both at the same time with the Delete
     * Blob operation.
     * @see https://learn.microsoft.com/rest/api/storageservices/delete-blob
     *
     * @param blobName -
     * @param options - Options to Blob Delete operation.
     * @returns Block blob deletion response data.
     */
    async deleteBlob(blobName, options = {}) {
        return tracingClient.withSpan("ContainerClient-deleteBlob", options, async (updatedOptions) => {
            let blobClient = this.getBlobClient(blobName);
            if (options.versionId) {
                blobClient = blobClient.withVersion(options.versionId);
            }
            return blobClient.delete(updatedOptions);
        });
    }
    /**
     * listBlobFlatSegment returns a single segment of blobs starting from the
     * specified Marker. Use an empty Marker to start enumeration from the beginning.
     * After getting a segment, process it, and then call listBlobsFlatSegment again
     * (passing the the previously-returned Marker) to get the next segment.
     * @see https://learn.microsoft.com/rest/api/storageservices/list-blobs
     *
     * @param marker - A string value that identifies the portion of the list to be returned with the next list operation.
     * @param options - Options to Container List Blob Flat Segment operation.
     */
    async listBlobFlatSegment(marker, options = {}) {
        return tracingClient.withSpan("ContainerClient-listBlobFlatSegment", options, async (updatedOptions) => {
            const response = utils_common_assertResponse(await this.containerContext.listBlobFlatSegment({
                marker,
                ...options,
                tracingOptions: updatedOptions.tracingOptions,
            }));
            const wrappedResponse = {
                ...response,
                _response: {
                    ...response._response,
                    parsedBody: ConvertInternalResponseOfListBlobFlat(response._response.parsedBody),
                }, // _response is made non-enumerable
                segment: {
                    ...response.segment,
                    blobItems: response.segment.blobItems.map((blobItemInternal) => {
                        const blobItem = {
                            ...blobItemInternal,
                            name: BlobNameToString(blobItemInternal.name),
                            tags: toTags(blobItemInternal.blobTags),
                            objectReplicationSourceProperties: parseObjectReplicationRecord(blobItemInternal.objectReplicationMetadata),
                        };
                        return blobItem;
                    }),
                },
            };
            return wrappedResponse;
        });
    }
    /**
     * listBlobHierarchySegment returns a single segment of blobs starting from
     * the specified Marker. Use an empty Marker to start enumeration from the
     * beginning. After getting a segment, process it, and then call listBlobsHierarchicalSegment
     * again (passing the the previously-returned Marker) to get the next segment.
     * @see https://learn.microsoft.com/rest/api/storageservices/list-blobs
     *
     * @param delimiter - The character or string used to define the virtual hierarchy
     * @param marker - A string value that identifies the portion of the list to be returned with the next list operation.
     * @param options - Options to Container List Blob Hierarchy Segment operation.
     */
    async listBlobHierarchySegment(delimiter, marker, options = {}) {
        return tracingClient.withSpan("ContainerClient-listBlobHierarchySegment", options, async (updatedOptions) => {
            const response = utils_common_assertResponse(await this.containerContext.listBlobHierarchySegment(delimiter, {
                marker,
                ...options,
                tracingOptions: updatedOptions.tracingOptions,
            }));
            const wrappedResponse = {
                ...response,
                _response: {
                    ...response._response,
                    parsedBody: ConvertInternalResponseOfListBlobHierarchy(response._response.parsedBody),
                }, // _response is made non-enumerable
                segment: {
                    ...response.segment,
                    blobItems: response.segment.blobItems.map((blobItemInternal) => {
                        const blobItem = {
                            ...blobItemInternal,
                            name: BlobNameToString(blobItemInternal.name),
                            tags: toTags(blobItemInternal.blobTags),
                            objectReplicationSourceProperties: parseObjectReplicationRecord(blobItemInternal.objectReplicationMetadata),
                        };
                        return blobItem;
                    }),
                    blobPrefixes: response.segment.blobPrefixes?.map((blobPrefixInternal) => {
                        const blobPrefix = {
                            ...blobPrefixInternal,
                            name: BlobNameToString(blobPrefixInternal.name),
                        };
                        return blobPrefix;
                    }),
                },
            };
            return wrappedResponse;
        });
    }
    /**
     * Returns an AsyncIterableIterator for ContainerListBlobFlatSegmentResponse
     *
     * @param marker - A string value that identifies the portion of
     *                          the list of blobs to be returned with the next listing operation. The
     *                          operation returns the ContinuationToken value within the response body if the
     *                          listing operation did not return all blobs remaining to be listed
     *                          with the current page. The ContinuationToken value can be used as the value for
     *                          the marker parameter in a subsequent call to request the next page of list
     *                          items. The marker value is opaque to the client.
     * @param options - Options to list blobs operation.
     */
    async *listSegments(marker, options = {}) {
        let listBlobsFlatSegmentResponse;
        if (!!marker || marker === undefined) {
            do {
                listBlobsFlatSegmentResponse = await this.listBlobFlatSegment(marker, options);
                marker = listBlobsFlatSegmentResponse.continuationToken;
                yield await listBlobsFlatSegmentResponse;
            } while (marker);
        }
    }
    /**
     * Returns an AsyncIterableIterator of {@link BlobItem} objects
     *
     * @param options - Options to list blobs operation.
     */
    async *listItems(options = {}) {
        let marker;
        for await (const listBlobsFlatSegmentResponse of this.listSegments(marker, options)) {
            yield* listBlobsFlatSegmentResponse.segment.blobItems;
        }
    }
    /**
     * Returns an async iterable iterator to list all the blobs
     * under the specified account.
     *
     * .byPage() returns an async iterable iterator to list the blobs in pages.
     *
     * ```ts snippet:ReadmeSampleListBlobs_Multiple
     * import { BlobServiceClient } from "@azure/storage-blob";
     * import { DefaultAzureCredential } from "@azure/identity";
     *
     * const account = "<account>";
     * const blobServiceClient = new BlobServiceClient(
     *   `https://${account}.blob.core.windows.net`,
     *   new DefaultAzureCredential(),
     * );
     *
     * const containerName = "<container name>";
     * const containerClient = blobServiceClient.getContainerClient(containerName);
     *
     * // Example using `for await` syntax
     * let i = 1;
     * const blobs = containerClient.listBlobsFlat();
     * for await (const blob of blobs) {
     *   console.log(`Blob ${i++}: ${blob.name}`);
     * }
     *
     * // Example using `iter.next()` syntax
     * i = 1;
     * const iter = containerClient.listBlobsFlat();
     * let { value, done } = await iter.next();
     * while (!done) {
     *   console.log(`Blob ${i++}: ${value.name}`);
     *   ({ value, done } = await iter.next());
     * }
     *
     * // Example using `byPage()` syntax
     * i = 1;
     * for await (const page of containerClient.listBlobsFlat().byPage({ maxPageSize: 20 })) {
     *   for (const blob of page.segment.blobItems) {
     *     console.log(`Blob ${i++}: ${blob.name}`);
     *   }
     * }
     *
     * // Example using paging with a marker
     * i = 1;
     * let iterator = containerClient.listBlobsFlat().byPage({ maxPageSize: 2 });
     * let response = (await iterator.next()).value;
     * // Prints 2 blob names
     * if (response.segment.blobItems) {
     *   for (const blob of response.segment.blobItems) {
     *     console.log(`Blob ${i++}: ${blob.name}`);
     *   }
     * }
     * // Gets next marker
     * let marker = response.continuationToken;
     * // Passing next marker as continuationToken
     * iterator = containerClient.listBlobsFlat().byPage({ continuationToken: marker, maxPageSize: 10 });
     * response = (await iterator.next()).value;
     * // Prints 10 blob names
     * if (response.segment.blobItems) {
     *   for (const blob of response.segment.blobItems) {
     *     console.log(`Blob ${i++}: ${blob.name}`);
     *   }
     * }
     * ```
     *
     * @param options - Options to list blobs.
     * @returns An asyncIterableIterator that supports paging.
     */
    listBlobsFlat(options = {}) {
        const include = [];
        if (options.includeCopy) {
            include.push("copy");
        }
        if (options.includeDeleted) {
            include.push("deleted");
        }
        if (options.includeMetadata) {
            include.push("metadata");
        }
        if (options.includeSnapshots) {
            include.push("snapshots");
        }
        if (options.includeVersions) {
            include.push("versions");
        }
        if (options.includeUncommitedBlobs) {
            include.push("uncommittedblobs");
        }
        if (options.includeTags) {
            include.push("tags");
        }
        if (options.includeDeletedWithVersions) {
            include.push("deletedwithversions");
        }
        if (options.includeImmutabilityPolicy) {
            include.push("immutabilitypolicy");
        }
        if (options.includeLegalHold) {
            include.push("legalhold");
        }
        if (options.prefix === "") {
            options.prefix = undefined;
        }
        const updatedOptions = {
            ...options,
            ...(include.length > 0 ? { include: include } : {}),
        };
        // AsyncIterableIterator to iterate over blobs
        const iter = this.listItems(updatedOptions);
        return {
            /**
             * The next method, part of the iteration protocol
             */
            next() {
                return iter.next();
            },
            /**
             * The connection to the async iterator, part of the iteration protocol
             */
            [Symbol.asyncIterator]() {
                return this;
            },
            /**
             * Return an AsyncIterableIterator that works a page at a time
             */
            byPage: (settings = {}) => {
                return this.listSegments(settings.continuationToken, {
                    maxPageSize: settings.maxPageSize,
                    ...updatedOptions,
                });
            },
        };
    }
    /**
     * Returns an AsyncIterableIterator for ContainerListBlobHierarchySegmentResponse
     *
     * @param delimiter - The character or string used to define the virtual hierarchy
     * @param marker - A string value that identifies the portion of
     *                          the list of blobs to be returned with the next listing operation. The
     *                          operation returns the ContinuationToken value within the response body if the
     *                          listing operation did not return all blobs remaining to be listed
     *                          with the current page. The ContinuationToken value can be used as the value for
     *                          the marker parameter in a subsequent call to request the next page of list
     *                          items. The marker value is opaque to the client.
     * @param options - Options to list blobs operation.
     */
    async *listHierarchySegments(delimiter, marker, options = {}) {
        let listBlobsHierarchySegmentResponse;
        if (!!marker || marker === undefined) {
            do {
                listBlobsHierarchySegmentResponse = await this.listBlobHierarchySegment(delimiter, marker, options);
                marker = listBlobsHierarchySegmentResponse.continuationToken;
                yield await listBlobsHierarchySegmentResponse;
            } while (marker);
        }
    }
    /**
     * Returns an AsyncIterableIterator for {@link BlobPrefix} and {@link BlobItem} objects.
     *
     * @param delimiter - The character or string used to define the virtual hierarchy
     * @param options - Options to list blobs operation.
     */
    async *listItemsByHierarchy(delimiter, options = {}) {
        let marker;
        for await (const listBlobsHierarchySegmentResponse of this.listHierarchySegments(delimiter, marker, options)) {
            const segment = listBlobsHierarchySegmentResponse.segment;
            if (segment.blobPrefixes) {
                for (const prefix of segment.blobPrefixes) {
                    yield {
                        kind: "prefix",
                        ...prefix,
                    };
                }
            }
            for (const blob of segment.blobItems) {
                yield { kind: "blob", ...blob };
            }
        }
    }
    /**
     * Returns an async iterable iterator to list all the blobs by hierarchy.
     * under the specified account.
     *
     * .byPage() returns an async iterable iterator to list the blobs by hierarchy in pages.
     *
     * ```ts snippet:ReadmeSampleListBlobsByHierarchy
     * import { BlobServiceClient } from "@azure/storage-blob";
     * import { DefaultAzureCredential } from "@azure/identity";
     *
     * const account = "<account>";
     * const blobServiceClient = new BlobServiceClient(
     *   `https://${account}.blob.core.windows.net`,
     *   new DefaultAzureCredential(),
     * );
     *
     * const containerName = "<container name>";
     * const containerClient = blobServiceClient.getContainerClient(containerName);
     *
     * // Example using `for await` syntax
     * let i = 1;
     * const blobs = containerClient.listBlobsByHierarchy("/");
     * for await (const blob of blobs) {
     *   if (blob.kind === "prefix") {
     *     console.log(`\tBlobPrefix: ${blob.name}`);
     *   } else {
     *     console.log(`\tBlobItem: name - ${blob.name}`);
     *   }
     * }
     *
     * // Example using `iter.next()` syntax
     * i = 1;
     * const iter = containerClient.listBlobsByHierarchy("/");
     * let { value, done } = await iter.next();
     * while (!done) {
     *   if (value.kind === "prefix") {
     *     console.log(`\tBlobPrefix: ${value.name}`);
     *   } else {
     *     console.log(`\tBlobItem: name - ${value.name}`);
     *   }
     *   ({ value, done } = await iter.next());
     * }
     *
     * // Example using `byPage()` syntax
     * i = 1;
     * for await (const page of containerClient.listBlobsByHierarchy("/").byPage({ maxPageSize: 20 })) {
     *   const segment = page.segment;
     *   if (segment.blobPrefixes) {
     *     for (const prefix of segment.blobPrefixes) {
     *       console.log(`\tBlobPrefix: ${prefix.name}`);
     *     }
     *   }
     *   for (const blob of page.segment.blobItems) {
     *     console.log(`\tBlobItem: name - ${blob.name}`);
     *   }
     * }
     *
     * // Example using paging with a marker
     * i = 1;
     * let iterator = containerClient.listBlobsByHierarchy("/").byPage({ maxPageSize: 2 });
     * let response = (await iterator.next()).value;
     * // Prints 2 blob names
     * if (response.blobPrefixes) {
     *   for (const prefix of response.blobPrefixes) {
     *     console.log(`\tBlobPrefix: ${prefix.name}`);
     *   }
     * }
     * if (response.segment.blobItems) {
     *   for (const blob of response.segment.blobItems) {
     *     console.log(`\tBlobItem: name - ${blob.name}`);
     *   }
     * }
     * // Gets next marker
     * let marker = response.continuationToken;
     * // Passing next marker as continuationToken
     * iterator = containerClient
     *   .listBlobsByHierarchy("/")
     *   .byPage({ continuationToken: marker, maxPageSize: 10 });
     * response = (await iterator.next()).value;
     * // Prints 10 blob names
     * if (response.blobPrefixes) {
     *   for (const prefix of response.blobPrefixes) {
     *     console.log(`\tBlobPrefix: ${prefix.name}`);
     *   }
     * }
     * if (response.segment.blobItems) {
     *   for (const blob of response.segment.blobItems) {
     *     console.log(`Blob ${i++}: ${blob.name}`);
     *   }
     * }
     * ```
     *
     * @param delimiter - The character or string used to define the virtual hierarchy
     * @param options - Options to list blobs operation.
     */
    listBlobsByHierarchy(delimiter, options = {}) {
        if (delimiter === "") {
            throw new RangeError("delimiter should contain one or more characters");
        }
        const include = [];
        if (options.includeCopy) {
            include.push("copy");
        }
        if (options.includeDeleted) {
            include.push("deleted");
        }
        if (options.includeMetadata) {
            include.push("metadata");
        }
        if (options.includeSnapshots) {
            include.push("snapshots");
        }
        if (options.includeVersions) {
            include.push("versions");
        }
        if (options.includeUncommitedBlobs) {
            include.push("uncommittedblobs");
        }
        if (options.includeTags) {
            include.push("tags");
        }
        if (options.includeDeletedWithVersions) {
            include.push("deletedwithversions");
        }
        if (options.includeImmutabilityPolicy) {
            include.push("immutabilitypolicy");
        }
        if (options.includeLegalHold) {
            include.push("legalhold");
        }
        if (options.prefix === "") {
            options.prefix = undefined;
        }
        const updatedOptions = {
            ...options,
            ...(include.length > 0 ? { include: include } : {}),
        };
        // AsyncIterableIterator to iterate over blob prefixes and blobs
        const iter = this.listItemsByHierarchy(delimiter, updatedOptions);
        return {
            /**
             * The next method, part of the iteration protocol
             */
            async next() {
                return iter.next();
            },
            /**
             * The connection to the async iterator, part of the iteration protocol
             */
            [Symbol.asyncIterator]() {
                return this;
            },
            /**
             * Return an AsyncIterableIterator that works a page at a time
             */
            byPage: (settings = {}) => {
                return this.listHierarchySegments(delimiter, settings.continuationToken, {
                    maxPageSize: settings.maxPageSize,
                    ...updatedOptions,
                });
            },
        };
    }
    /**
     * The Filter Blobs operation enables callers to list blobs in the container whose tags
     * match a given search expression.
     *
     * @param tagFilterSqlExpression - The where parameter enables the caller to query blobs whose tags match a given expression.
     *                                        The given expression must evaluate to true for a blob to be returned in the results.
     *                                        The[OData - ABNF] filter syntax rule defines the formal grammar for the value of the where query parameter;
     *                                        however, only a subset of the OData filter syntax is supported in the Blob service.
     * @param marker - A string value that identifies the portion of
     *                          the list of blobs to be returned with the next listing operation. The
     *                          operation returns the continuationToken value within the response body if the
     *                          listing operation did not return all blobs remaining to be listed
     *                          with the current page. The continuationToken value can be used as the value for
     *                          the marker parameter in a subsequent call to request the next page of list
     *                          items. The marker value is opaque to the client.
     * @param options - Options to find blobs by tags.
     */
    async findBlobsByTagsSegment(tagFilterSqlExpression, marker, options = {}) {
        return tracingClient.withSpan("ContainerClient-findBlobsByTagsSegment", options, async (updatedOptions) => {
            const response = utils_common_assertResponse(await this.containerContext.filterBlobs({
                abortSignal: options.abortSignal,
                where: tagFilterSqlExpression,
                marker,
                maxPageSize: options.maxPageSize,
                tracingOptions: updatedOptions.tracingOptions,
            }));
            const wrappedResponse = {
                ...response,
                _response: response._response, // _response is made non-enumerable
                blobs: response.blobs.map((blob) => {
                    let tagValue = "";
                    if (blob.tags?.blobTagSet.length === 1) {
                        tagValue = blob.tags.blobTagSet[0].value;
                    }
                    return { ...blob, tags: toTags(blob.tags), tagValue };
                }),
            };
            return wrappedResponse;
        });
    }
    /**
     * Returns an AsyncIterableIterator for ContainerFindBlobsByTagsSegmentResponse.
     *
     * @param tagFilterSqlExpression -  The where parameter enables the caller to query blobs whose tags match a given expression.
     *                                         The given expression must evaluate to true for a blob to be returned in the results.
     *                                         The[OData - ABNF] filter syntax rule defines the formal grammar for the value of the where query parameter;
     *                                         however, only a subset of the OData filter syntax is supported in the Blob service.
     * @param marker - A string value that identifies the portion of
     *                          the list of blobs to be returned with the next listing operation. The
     *                          operation returns the continuationToken value within the response body if the
     *                          listing operation did not return all blobs remaining to be listed
     *                          with the current page. The continuationToken value can be used as the value for
     *                          the marker parameter in a subsequent call to request the next page of list
     *                          items. The marker value is opaque to the client.
     * @param options - Options to find blobs by tags.
     */
    async *findBlobsByTagsSegments(tagFilterSqlExpression, marker, options = {}) {
        let response;
        if (!!marker || marker === undefined) {
            do {
                response = await this.findBlobsByTagsSegment(tagFilterSqlExpression, marker, options);
                response.blobs = response.blobs || [];
                marker = response.continuationToken;
                yield response;
            } while (marker);
        }
    }
    /**
     * Returns an AsyncIterableIterator for blobs.
     *
     * @param tagFilterSqlExpression -  The where parameter enables the caller to query blobs whose tags match a given expression.
     *                                         The given expression must evaluate to true for a blob to be returned in the results.
     *                                         The[OData - ABNF] filter syntax rule defines the formal grammar for the value of the where query parameter;
     *                                         however, only a subset of the OData filter syntax is supported in the Blob service.
     * @param options - Options to findBlobsByTagsItems.
     */
    async *findBlobsByTagsItems(tagFilterSqlExpression, options = {}) {
        let marker;
        for await (const segment of this.findBlobsByTagsSegments(tagFilterSqlExpression, marker, options)) {
            yield* segment.blobs;
        }
    }
    /**
     * Returns an async iterable iterator to find all blobs with specified tag
     * under the specified container.
     *
     * .byPage() returns an async iterable iterator to list the blobs in pages.
     *
     * Example using `for await` syntax:
     *
     * ```ts snippet:ReadmeSampleFindBlobsByTags
     * import { BlobServiceClient } from "@azure/storage-blob";
     * import { DefaultAzureCredential } from "@azure/identity";
     *
     * const account = "<account>";
     * const blobServiceClient = new BlobServiceClient(
     *   `https://${account}.blob.core.windows.net`,
     *   new DefaultAzureCredential(),
     * );
     *
     * const containerName = "<container name>";
     * const containerClient = blobServiceClient.getContainerClient(containerName);
     *
     * // Example using `for await` syntax
     * let i = 1;
     * for await (const blob of containerClient.findBlobsByTags("tagkey='tagvalue'")) {
     *   console.log(`Blob ${i++}: ${blob.name}`);
     * }
     *
     * // Example using `iter.next()` syntax
     * i = 1;
     * const iter = containerClient.findBlobsByTags("tagkey='tagvalue'");
     * let { value, done } = await iter.next();
     * while (!done) {
     *   console.log(`Blob ${i++}: ${value.name}`);
     *   ({ value, done } = await iter.next());
     * }
     *
     * // Example using `byPage()` syntax
     * i = 1;
     * for await (const page of containerClient
     *   .findBlobsByTags("tagkey='tagvalue'")
     *   .byPage({ maxPageSize: 20 })) {
     *   for (const blob of page.blobs) {
     *     console.log(`Blob ${i++}: ${blob.name}`);
     *   }
     * }
     *
     * // Example using paging with a marker
     * i = 1;
     * let iterator = containerClient.findBlobsByTags("tagkey='tagvalue'").byPage({ maxPageSize: 2 });
     * let response = (await iterator.next()).value;
     * // Prints 2 blob names
     * if (response.blobs) {
     *   for (const blob of response.blobs) {
     *     console.log(`Blob ${i++}: ${blob.name}`);
     *   }
     * }
     * // Gets next marker
     * let marker = response.continuationToken;
     * // Passing next marker as continuationToken
     * iterator = containerClient
     *   .findBlobsByTags("tagkey='tagvalue'")
     *   .byPage({ continuationToken: marker, maxPageSize: 10 });
     * response = (await iterator.next()).value;
     * // Prints 10 blob names
     * if (response.blobs) {
     *   for (const blob of response.blobs) {
     *     console.log(`Blob ${i++}: ${blob.name}`);
     *   }
     * }
     * ```
     *
     * @param tagFilterSqlExpression -  The where parameter enables the caller to query blobs whose tags match a given expression.
     *                                         The given expression must evaluate to true for a blob to be returned in the results.
     *                                         The[OData - ABNF] filter syntax rule defines the formal grammar for the value of the where query parameter;
     *                                         however, only a subset of the OData filter syntax is supported in the Blob service.
     * @param options - Options to find blobs by tags.
     */
    findBlobsByTags(tagFilterSqlExpression, options = {}) {
        // AsyncIterableIterator to iterate over blobs
        const listSegmentOptions = {
            ...options,
        };
        const iter = this.findBlobsByTagsItems(tagFilterSqlExpression, listSegmentOptions);
        return {
            /**
             * The next method, part of the iteration protocol
             */
            next() {
                return iter.next();
            },
            /**
             * The connection to the async iterator, part of the iteration protocol
             */
            [Symbol.asyncIterator]() {
                return this;
            },
            /**
             * Return an AsyncIterableIterator that works a page at a time
             */
            byPage: (settings = {}) => {
                return this.findBlobsByTagsSegments(tagFilterSqlExpression, settings.continuationToken, {
                    maxPageSize: settings.maxPageSize,
                    ...listSegmentOptions,
                });
            },
        };
    }
    /**
     * The Get Account Information operation returns the sku name and account kind
     * for the specified account.
     * The Get Account Information operation is available on service versions beginning
     * with version 2018-03-28.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-account-information
     *
     * @param options - Options to the Service Get Account Info operation.
     * @returns Response data for the Service Get Account Info operation.
     */
    async getAccountInfo(options = {}) {
        return tracingClient.withSpan("ContainerClient-getAccountInfo", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.containerContext.getAccountInfo({
                abortSignal: options.abortSignal,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    getContainerNameFromUrl() {
        let containerName;
        try {
            //  URL may look like the following
            // "https://myaccount.blob.core.windows.net/mycontainer?sasString";
            // "https://myaccount.blob.core.windows.net/mycontainer";
            // IPv4/IPv6 address hosts, Endpoints - `http://127.0.0.1:10000/devstoreaccount1/containername`
            // http://localhost:10001/devstoreaccount1/containername
            const parsedUrl = new URL(this.url);
            if (parsedUrl.hostname.split(".")[1] === "blob") {
                // "https://myaccount.blob.core.windows.net/containername".
                // "https://customdomain.com/containername".
                // .getPath() -> /containername
                containerName = parsedUrl.pathname.split("/")[1];
            }
            else if (utils_common_isIpEndpointStyle(parsedUrl)) {
                // IPv4/IPv6 address hosts... Example - http://192.0.0.10:10001/devstoreaccount1/containername
                // Single word domain without a [dot] in the endpoint... Example - http://localhost:10001/devstoreaccount1/containername
                // .getPath() -> /devstoreaccount1/containername
                containerName = parsedUrl.pathname.split("/")[2];
            }
            else {
                // "https://customdomain.com/containername".
                // .getPath() -> /containername
                containerName = parsedUrl.pathname.split("/")[1];
            }
            // decode the encoded containerName - to get all the special characters that might be present in it
            containerName = decodeURIComponent(containerName);
            if (!containerName) {
                throw new Error("Provided containerName is invalid.");
            }
            return containerName;
        }
        catch (error) {
            throw new Error("Unable to extract containerName with provided information.");
        }
    }
    /**
     * Only available for ContainerClient constructed with a shared key credential.
     *
     * Generates a Blob Container Service Shared Access Signature (SAS) URI based on the client properties
     * and parameters passed in. The SAS is signed by the shared key credential of the client.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/constructing-a-service-sas
     *
     * @param options - Optional parameters.
     * @returns The SAS URI consisting of the URI to the resource represented by this client, followed by the generated SAS token.
     */
    generateSasUrl(options) {
        return new Promise((resolve) => {
            if (!(this.credential instanceof StorageSharedKeyCredential)) {
                throw new RangeError("Can only generate the SAS when the client is initialized with a shared key credential");
            }
            const sas = generateBlobSASQueryParameters({
                containerName: this._containerName,
                ...options,
            }, this.credential).toString();
            resolve(utils_common_appendToURLQuery(this.url, sas));
        });
    }
    /**
     * Only available for ContainerClient constructed with a shared key credential.
     *
     * Generates string to sign for a Blob Container Service Shared Access Signature (SAS) URI
     * based on the client properties and parameters passed in. The SAS is signed by the shared key credential of the client.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/constructing-a-service-sas
     *
     * @param options - Optional parameters.
     * @returns The SAS URI consisting of the URI to the resource represented by this client, followed by the generated SAS token.
     */
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    generateSasStringToSign(options) {
        if (!(this.credential instanceof StorageSharedKeyCredential)) {
            throw new RangeError("Can only generate the SAS when the client is initialized with a shared key credential");
        }
        return generateBlobSASQueryParametersInternal({
            containerName: this._containerName,
            ...options,
        }, this.credential).stringToSign;
    }
    /**
     * Generates a Blob Container Service Shared Access Signature (SAS) URI based on the client properties
     * and parameters passed in. The SAS is signed by the input user delegation key.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/constructing-a-service-sas
     *
     * @param options - Optional parameters.
     * @param userDelegationKey -  Return value of `blobServiceClient.getUserDelegationKey()`
     * @returns The SAS URI consisting of the URI to the resource represented by this client, followed by the generated SAS token.
     */
    generateUserDelegationSasUrl(options, userDelegationKey) {
        return new Promise((resolve) => {
            const sas = generateBlobSASQueryParameters({
                containerName: this._containerName,
                ...options,
            }, userDelegationKey, this.accountName).toString();
            resolve(utils_common_appendToURLQuery(this.url, sas));
        });
    }
    /**
     * Generates string to sign for a Blob Container Service Shared Access Signature (SAS) URI
     * based on the client properties and parameters passed in. The SAS is signed by the input user delegation key.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/constructing-a-service-sas
     *
     * @param options - Optional parameters.
     * @param userDelegationKey -  Return value of `blobServiceClient.getUserDelegationKey()`
     * @returns The SAS URI consisting of the URI to the resource represented by this client, followed by the generated SAS token.
     */
    generateUserDelegationSasStringToSign(options, userDelegationKey) {
        return generateBlobSASQueryParametersInternal({
            containerName: this._containerName,
            ...options,
        }, userDelegationKey, this.accountName).stringToSign;
    }
    /**
     * Creates a BlobBatchClient object to conduct batch operations.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/blob-batch
     *
     * @returns A new BlobBatchClient object for this container.
     */
    getBlobBatchClient() {
        return new BlobBatchClient(this.url, this.pipeline);
    }
}
//# sourceMappingURL=ContainerClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/sas/AccountSASPermissions.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * This is a helper class to construct a string representing the permissions granted by an AccountSAS. Setting a value
 * to true means that any SAS which uses these permissions will grant permissions for that operation. Once all the
 * values are set, this should be serialized with toString and set as the permissions field on an
 * {@link AccountSASSignatureValues} object. It is possible to construct the permissions string without this class, but
 * the order of the permissions is particular and this class guarantees correctness.
 */
class AccountSASPermissions {
    /**
     * Parse initializes the AccountSASPermissions fields from a string.
     *
     * @param permissions -
     */
    static parse(permissions) {
        const accountSASPermissions = new AccountSASPermissions();
        for (const c of permissions) {
            switch (c) {
                case "r":
                    accountSASPermissions.read = true;
                    break;
                case "w":
                    accountSASPermissions.write = true;
                    break;
                case "d":
                    accountSASPermissions.delete = true;
                    break;
                case "x":
                    accountSASPermissions.deleteVersion = true;
                    break;
                case "l":
                    accountSASPermissions.list = true;
                    break;
                case "a":
                    accountSASPermissions.add = true;
                    break;
                case "c":
                    accountSASPermissions.create = true;
                    break;
                case "u":
                    accountSASPermissions.update = true;
                    break;
                case "p":
                    accountSASPermissions.process = true;
                    break;
                case "t":
                    accountSASPermissions.tag = true;
                    break;
                case "f":
                    accountSASPermissions.filter = true;
                    break;
                case "i":
                    accountSASPermissions.setImmutabilityPolicy = true;
                    break;
                case "y":
                    accountSASPermissions.permanentDelete = true;
                    break;
                default:
                    throw new RangeError(`Invalid permission character: ${c}`);
            }
        }
        return accountSASPermissions;
    }
    /**
     * Creates a {@link AccountSASPermissions} from a raw object which contains same keys as it
     * and boolean values for them.
     *
     * @param permissionLike -
     */
    static from(permissionLike) {
        const accountSASPermissions = new AccountSASPermissions();
        if (permissionLike.read) {
            accountSASPermissions.read = true;
        }
        if (permissionLike.write) {
            accountSASPermissions.write = true;
        }
        if (permissionLike.delete) {
            accountSASPermissions.delete = true;
        }
        if (permissionLike.deleteVersion) {
            accountSASPermissions.deleteVersion = true;
        }
        if (permissionLike.filter) {
            accountSASPermissions.filter = true;
        }
        if (permissionLike.tag) {
            accountSASPermissions.tag = true;
        }
        if (permissionLike.list) {
            accountSASPermissions.list = true;
        }
        if (permissionLike.add) {
            accountSASPermissions.add = true;
        }
        if (permissionLike.create) {
            accountSASPermissions.create = true;
        }
        if (permissionLike.update) {
            accountSASPermissions.update = true;
        }
        if (permissionLike.process) {
            accountSASPermissions.process = true;
        }
        if (permissionLike.setImmutabilityPolicy) {
            accountSASPermissions.setImmutabilityPolicy = true;
        }
        if (permissionLike.permanentDelete) {
            accountSASPermissions.permanentDelete = true;
        }
        return accountSASPermissions;
    }
    /**
     * Permission to read resources and list queues and tables granted.
     */
    read = false;
    /**
     * Permission to write resources granted.
     */
    write = false;
    /**
     * Permission to delete blobs and files granted.
     */
    delete = false;
    /**
     * Permission to delete versions granted.
     */
    deleteVersion = false;
    /**
     * Permission to list blob containers, blobs, shares, directories, and files granted.
     */
    list = false;
    /**
     * Permission to add messages, table entities, and append to blobs granted.
     */
    add = false;
    /**
     * Permission to create blobs and files granted.
     */
    create = false;
    /**
     * Permissions to update messages and table entities granted.
     */
    update = false;
    /**
     * Permission to get and delete messages granted.
     */
    process = false;
    /**
     * Specfies Tag access granted.
     */
    tag = false;
    /**
     * Permission to filter blobs.
     */
    filter = false;
    /**
     * Permission to set immutability policy.
     */
    setImmutabilityPolicy = false;
    /**
     * Specifies that Permanent Delete is permitted.
     */
    permanentDelete = false;
    /**
     * Produces the SAS permissions string for an Azure Storage account.
     * Call this method to set AccountSASSignatureValues Permissions field.
     *
     * Using this method will guarantee the resource types are in
     * an order accepted by the service.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/constructing-an-account-sas
     *
     */
    toString() {
        // The order of the characters should be as specified here to ensure correctness:
        // https://learn.microsoft.com/rest/api/storageservices/constructing-an-account-sas
        // Use a string array instead of string concatenating += operator for performance
        const permissions = [];
        if (this.read) {
            permissions.push("r");
        }
        if (this.write) {
            permissions.push("w");
        }
        if (this.delete) {
            permissions.push("d");
        }
        if (this.deleteVersion) {
            permissions.push("x");
        }
        if (this.filter) {
            permissions.push("f");
        }
        if (this.tag) {
            permissions.push("t");
        }
        if (this.list) {
            permissions.push("l");
        }
        if (this.add) {
            permissions.push("a");
        }
        if (this.create) {
            permissions.push("c");
        }
        if (this.update) {
            permissions.push("u");
        }
        if (this.process) {
            permissions.push("p");
        }
        if (this.setImmutabilityPolicy) {
            permissions.push("i");
        }
        if (this.permanentDelete) {
            permissions.push("y");
        }
        return permissions.join("");
    }
}
//# sourceMappingURL=AccountSASPermissions.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/sas/AccountSASResourceTypes.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * This is a helper class to construct a string representing the resources accessible by an AccountSAS. Setting a value
 * to true means that any SAS which uses these permissions will grant access to that resource type. Once all the
 * values are set, this should be serialized with toString and set as the resources field on an
 * {@link AccountSASSignatureValues} object. It is possible to construct the resources string without this class, but
 * the order of the resources is particular and this class guarantees correctness.
 */
class AccountSASResourceTypes {
    /**
     * Creates an {@link AccountSASResourceTypes} from the specified resource types string. This method will throw an
     * Error if it encounters a character that does not correspond to a valid resource type.
     *
     * @param resourceTypes -
     */
    static parse(resourceTypes) {
        const accountSASResourceTypes = new AccountSASResourceTypes();
        for (const c of resourceTypes) {
            switch (c) {
                case "s":
                    accountSASResourceTypes.service = true;
                    break;
                case "c":
                    accountSASResourceTypes.container = true;
                    break;
                case "o":
                    accountSASResourceTypes.object = true;
                    break;
                default:
                    throw new RangeError(`Invalid resource type: ${c}`);
            }
        }
        return accountSASResourceTypes;
    }
    /**
     * Permission to access service level APIs granted.
     */
    service = false;
    /**
     * Permission to access container level APIs (Blob Containers, Tables, Queues, File Shares) granted.
     */
    container = false;
    /**
     * Permission to access object level APIs (Blobs, Table Entities, Queue Messages, Files) granted.
     */
    object = false;
    /**
     * Converts the given resource types to a string.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/constructing-an-account-sas
     *
     */
    toString() {
        const resourceTypes = [];
        if (this.service) {
            resourceTypes.push("s");
        }
        if (this.container) {
            resourceTypes.push("c");
        }
        if (this.object) {
            resourceTypes.push("o");
        }
        return resourceTypes.join("");
    }
}
//# sourceMappingURL=AccountSASResourceTypes.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/sas/AccountSASServices.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * This is a helper class to construct a string representing the services accessible by an AccountSAS. Setting a value
 * to true means that any SAS which uses these permissions will grant access to that service. Once all the
 * values are set, this should be serialized with toString and set as the services field on an
 * {@link AccountSASSignatureValues} object. It is possible to construct the services string without this class, but
 * the order of the services is particular and this class guarantees correctness.
 */
class AccountSASServices {
    /**
     * Creates an {@link AccountSASServices} from the specified services string. This method will throw an
     * Error if it encounters a character that does not correspond to a valid service.
     *
     * @param services -
     */
    static parse(services) {
        const accountSASServices = new AccountSASServices();
        for (const c of services) {
            switch (c) {
                case "b":
                    accountSASServices.blob = true;
                    break;
                case "f":
                    accountSASServices.file = true;
                    break;
                case "q":
                    accountSASServices.queue = true;
                    break;
                case "t":
                    accountSASServices.table = true;
                    break;
                default:
                    throw new RangeError(`Invalid service character: ${c}`);
            }
        }
        return accountSASServices;
    }
    /**
     * Permission to access blob resources granted.
     */
    blob = false;
    /**
     * Permission to access file resources granted.
     */
    file = false;
    /**
     * Permission to access queue resources granted.
     */
    queue = false;
    /**
     * Permission to access table resources granted.
     */
    table = false;
    /**
     * Converts the given services to a string.
     *
     */
    toString() {
        const services = [];
        if (this.blob) {
            services.push("b");
        }
        if (this.table) {
            services.push("t");
        }
        if (this.queue) {
            services.push("q");
        }
        if (this.file) {
            services.push("f");
        }
        return services.join("");
    }
}
//# sourceMappingURL=AccountSASServices.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/sas/AccountSASSignatureValues.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.







/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * Generates a {@link SASQueryParameters} object which contains all SAS query parameters needed to make an actual
 * REST request.
 *
 * @see https://learn.microsoft.com/rest/api/storageservices/constructing-an-account-sas
 *
 * @param accountSASSignatureValues -
 * @param sharedKeyCredential -
 */
function generateAccountSASQueryParameters(accountSASSignatureValues, sharedKeyCredential) {
    return generateAccountSASQueryParametersInternal(accountSASSignatureValues, sharedKeyCredential)
        .sasQueryParameters;
}
function generateAccountSASQueryParametersInternal(accountSASSignatureValues, sharedKeyCredential) {
    const version = accountSASSignatureValues.version
        ? accountSASSignatureValues.version
        : SERVICE_VERSION;
    if (accountSASSignatureValues.permissions &&
        accountSASSignatureValues.permissions.setImmutabilityPolicy &&
        version < "2020-08-04") {
        throw RangeError("'version' must be >= '2020-08-04' when provided 'i' permission.");
    }
    if (accountSASSignatureValues.permissions &&
        accountSASSignatureValues.permissions.deleteVersion &&
        version < "2019-10-10") {
        throw RangeError("'version' must be >= '2019-10-10' when provided 'x' permission.");
    }
    if (accountSASSignatureValues.permissions &&
        accountSASSignatureValues.permissions.permanentDelete &&
        version < "2019-10-10") {
        throw RangeError("'version' must be >= '2019-10-10' when provided 'y' permission.");
    }
    if (accountSASSignatureValues.permissions &&
        accountSASSignatureValues.permissions.tag &&
        version < "2019-12-12") {
        throw RangeError("'version' must be >= '2019-12-12' when provided 't' permission.");
    }
    if (accountSASSignatureValues.permissions &&
        accountSASSignatureValues.permissions.filter &&
        version < "2019-12-12") {
        throw RangeError("'version' must be >= '2019-12-12' when provided 'f' permission.");
    }
    if (accountSASSignatureValues.encryptionScope && version < "2020-12-06") {
        throw RangeError("'version' must be >= '2020-12-06' when provided 'encryptionScope' in SAS.");
    }
    const parsedPermissions = AccountSASPermissions.parse(accountSASSignatureValues.permissions.toString());
    const parsedServices = AccountSASServices.parse(accountSASSignatureValues.services).toString();
    const parsedResourceTypes = AccountSASResourceTypes.parse(accountSASSignatureValues.resourceTypes).toString();
    let stringToSign;
    if (version >= "2020-12-06") {
        stringToSign = [
            sharedKeyCredential.accountName,
            parsedPermissions,
            parsedServices,
            parsedResourceTypes,
            accountSASSignatureValues.startsOn
                ? utils_common_truncatedISO8061Date(accountSASSignatureValues.startsOn, false)
                : "",
            utils_common_truncatedISO8061Date(accountSASSignatureValues.expiresOn, false),
            accountSASSignatureValues.ipRange ? ipRangeToString(accountSASSignatureValues.ipRange) : "",
            accountSASSignatureValues.protocol ? accountSASSignatureValues.protocol : "",
            version,
            accountSASSignatureValues.encryptionScope ? accountSASSignatureValues.encryptionScope : "",
            "", // Account SAS requires an additional newline character
        ].join("\n");
    }
    else {
        stringToSign = [
            sharedKeyCredential.accountName,
            parsedPermissions,
            parsedServices,
            parsedResourceTypes,
            accountSASSignatureValues.startsOn
                ? utils_common_truncatedISO8061Date(accountSASSignatureValues.startsOn, false)
                : "",
            utils_common_truncatedISO8061Date(accountSASSignatureValues.expiresOn, false),
            accountSASSignatureValues.ipRange ? ipRangeToString(accountSASSignatureValues.ipRange) : "",
            accountSASSignatureValues.protocol ? accountSASSignatureValues.protocol : "",
            version,
            "", // Account SAS requires an additional newline character
        ].join("\n");
    }
    const signature = sharedKeyCredential.computeHMACSHA256(stringToSign);
    return {
        sasQueryParameters: new SASQueryParameters(version, signature, parsedPermissions.toString(), parsedServices, parsedResourceTypes, accountSASSignatureValues.protocol, accountSASSignatureValues.startsOn, accountSASSignatureValues.expiresOn, accountSASSignatureValues.ipRange, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, accountSASSignatureValues.encryptionScope),
        stringToSign: stringToSign,
    };
}
//# sourceMappingURL=AccountSASSignatureValues.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/BlobServiceClient.js














/**
 * A BlobServiceClient represents a Client to the Azure Storage Blob service allowing you
 * to manipulate blob containers.
 */
class BlobServiceClient extends StorageClient_StorageClient {
    /**
     * serviceContext provided by protocol layer.
     */
    serviceContext;
    /**
     *
     * Creates an instance of BlobServiceClient from connection string.
     *
     * @param connectionString - Account connection string or a SAS connection string of an Azure storage account.
     *                                  [ Note - Account connection string can only be used in NODE.JS runtime. ]
     *                                  Account connection string example -
     *                                  `DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=accountKey;EndpointSuffix=core.windows.net`
     *                                  SAS connection string example -
     *                                  `BlobEndpoint=https://myaccount.blob.core.windows.net/;QueueEndpoint=https://myaccount.queue.core.windows.net/;FileEndpoint=https://myaccount.file.core.windows.net/;TableEndpoint=https://myaccount.table.core.windows.net/;SharedAccessSignature=sasString`
     * @param options - Optional. Options to configure the HTTP pipeline.
     */
    static fromConnectionString(connectionString, 
    // Legacy, no fix for eslint error without breaking. Disable it for this interface.
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    options) {
        options = options || {};
        const extractedCreds = utils_common_extractConnectionStringParts(connectionString);
        if (extractedCreds.kind === "AccountConnString") {
            if (esm_isNodeLike) {
                const sharedKeyCredential = new StorageSharedKeyCredential(extractedCreds.accountName, extractedCreds.accountKey);
                if (!options.proxyOptions) {
                    options.proxyOptions = proxyPolicy_getDefaultProxySettings(extractedCreds.proxyUri);
                }
                const pipeline = newPipeline(sharedKeyCredential, options);
                return new BlobServiceClient(extractedCreds.url, pipeline);
            }
            else {
                throw new Error("Account connection string is only supported in Node.js environment");
            }
        }
        else if (extractedCreds.kind === "SASConnString") {
            const pipeline = newPipeline(new AnonymousCredential(), options);
            return new BlobServiceClient(extractedCreds.url + "?" + extractedCreds.accountSas, pipeline);
        }
        else {
            throw new Error("Connection string must be either an Account connection string or a SAS connection string");
        }
    }
    constructor(url, credentialOrPipeline, 
    // Legacy, no fix for eslint error without breaking. Disable it for this interface.
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    options) {
        let pipeline;
        if (isPipelineLike(credentialOrPipeline)) {
            pipeline = credentialOrPipeline;
        }
        else if ((esm_isNodeLike && credentialOrPipeline instanceof StorageSharedKeyCredential) ||
            credentialOrPipeline instanceof AnonymousCredential ||
            isTokenCredential(credentialOrPipeline)) {
            pipeline = newPipeline(credentialOrPipeline, options);
        }
        else {
            // The second parameter is undefined. Use anonymous credential
            pipeline = newPipeline(new AnonymousCredential(), options);
        }
        super(url, pipeline);
        this.serviceContext = this.storageClientContext.service;
    }
    /**
     * Creates a {@link ContainerClient} object
     *
     * @param containerName - A container name
     * @returns A new ContainerClient object for the given container name.
     *
     * Example usage:
     *
     * ```ts snippet:BlobServiceClientGetContainerClient
     * import { BlobServiceClient } from "@azure/storage-blob";
     * import { DefaultAzureCredential } from "@azure/identity";
     *
     * const account = "<account>";
     * const blobServiceClient = new BlobServiceClient(
     *   `https://${account}.blob.core.windows.net`,
     *   new DefaultAzureCredential(),
     * );
     *
     * const containerClient = blobServiceClient.getContainerClient("<container name>");
     * ```
     */
    getContainerClient(containerName) {
        return new ContainerClient(utils_common_appendToURLPath(this.url, encodeURIComponent(containerName)), this.pipeline);
    }
    /**
     * Create a Blob container. @see https://learn.microsoft.com/rest/api/storageservices/create-container
     *
     * @param containerName - Name of the container to create.
     * @param options - Options to configure Container Create operation.
     * @returns Container creation response and the corresponding container client.
     */
    async createContainer(containerName, options = {}) {
        return tracingClient.withSpan("BlobServiceClient-createContainer", options, async (updatedOptions) => {
            const containerClient = this.getContainerClient(containerName);
            const containerCreateResponse = await containerClient.create(updatedOptions);
            return {
                containerClient,
                containerCreateResponse,
            };
        });
    }
    /**
     * Deletes a Blob container.
     *
     * @param containerName - Name of the container to delete.
     * @param options - Options to configure Container Delete operation.
     * @returns Container deletion response.
     */
    async deleteContainer(containerName, options = {}) {
        return tracingClient.withSpan("BlobServiceClient-deleteContainer", options, async (updatedOptions) => {
            const containerClient = this.getContainerClient(containerName);
            return containerClient.delete(updatedOptions);
        });
    }
    /**
     * Restore a previously deleted Blob container.
     * This API is only functional if Container Soft Delete is enabled for the storage account associated with the container.
     *
     * @param deletedContainerName - Name of the previously deleted container.
     * @param deletedContainerVersion - Version of the previously deleted container, used to uniquely identify the deleted container.
     * @param options - Options to configure Container Restore operation.
     * @returns Container deletion response.
     */
    async undeleteContainer(deletedContainerName, deletedContainerVersion, options = {}) {
        return tracingClient.withSpan("BlobServiceClient-undeleteContainer", options, async (updatedOptions) => {
            const containerClient = this.getContainerClient(options.destinationContainerName || deletedContainerName);
            // Hack to access a protected member.
            const containerContext = containerClient["storageClientContext"].container;
            const containerUndeleteResponse = utils_common_assertResponse(await containerContext.restore({
                deletedContainerName,
                deletedContainerVersion,
                tracingOptions: updatedOptions.tracingOptions,
            }));
            return { containerClient, containerUndeleteResponse };
        });
    }
    /**
     * Gets the properties of a storage account’s Blob service, including properties
     * for Storage Analytics and CORS (Cross-Origin Resource Sharing) rules.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-blob-service-properties
     *
     * @param options - Options to the Service Get Properties operation.
     * @returns Response data for the Service Get Properties operation.
     */
    async getProperties(options = {}) {
        return tracingClient.withSpan("BlobServiceClient-getProperties", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.serviceContext.getProperties({
                abortSignal: options.abortSignal,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Sets properties for a storage account’s Blob service endpoint, including properties
     * for Storage Analytics, CORS (Cross-Origin Resource Sharing) rules and soft delete settings.
     * @see https://learn.microsoft.com/rest/api/storageservices/set-blob-service-properties
     *
     * @param properties -
     * @param options - Options to the Service Set Properties operation.
     * @returns Response data for the Service Set Properties operation.
     */
    async setProperties(properties, options = {}) {
        return tracingClient.withSpan("BlobServiceClient-setProperties", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.serviceContext.setProperties(properties, {
                abortSignal: options.abortSignal,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Retrieves statistics related to replication for the Blob service. It is only
     * available on the secondary location endpoint when read-access geo-redundant
     * replication is enabled for the storage account.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-blob-service-stats
     *
     * @param options - Options to the Service Get Statistics operation.
     * @returns Response data for the Service Get Statistics operation.
     */
    async getStatistics(options = {}) {
        return tracingClient.withSpan("BlobServiceClient-getStatistics", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.serviceContext.getStatistics({
                abortSignal: options.abortSignal,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * The Get Account Information operation returns the sku name and account kind
     * for the specified account.
     * The Get Account Information operation is available on service versions beginning
     * with version 2018-03-28.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-account-information
     *
     * @param options - Options to the Service Get Account Info operation.
     * @returns Response data for the Service Get Account Info operation.
     */
    async getAccountInfo(options = {}) {
        return tracingClient.withSpan("BlobServiceClient-getAccountInfo", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.serviceContext.getAccountInfo({
                abortSignal: options.abortSignal,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Returns a list of the containers under the specified account.
     * @see https://learn.microsoft.com/rest/api/storageservices/list-containers2
     *
     * @param marker - A string value that identifies the portion of
     *                        the list of containers to be returned with the next listing operation. The
     *                        operation returns the continuationToken value within the response body if the
     *                        listing operation did not return all containers remaining to be listed
     *                        with the current page. The continuationToken value can be used as the value for
     *                        the marker parameter in a subsequent call to request the next page of list
     *                        items. The marker value is opaque to the client.
     * @param options - Options to the Service List Container Segment operation.
     * @returns Response data for the Service List Container Segment operation.
     */
    async listContainersSegment(marker, options = {}) {
        return tracingClient.withSpan("BlobServiceClient-listContainersSegment", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.serviceContext.listContainersSegment({
                abortSignal: options.abortSignal,
                marker,
                ...options,
                include: typeof options.include === "string" ? [options.include] : options.include,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * The Filter Blobs operation enables callers to list blobs across all containers whose tags
     * match a given search expression. Filter blobs searches across all containers within a
     * storage account but can be scoped within the expression to a single container.
     *
     * @param tagFilterSqlExpression - The where parameter enables the caller to query blobs whose tags match a given expression.
     *                                        The given expression must evaluate to true for a blob to be returned in the results.
     *                                        The[OData - ABNF] filter syntax rule defines the formal grammar for the value of the where query parameter;
     *                                        however, only a subset of the OData filter syntax is supported in the Blob service.
     * @param marker - A string value that identifies the portion of
     *                          the list of blobs to be returned with the next listing operation. The
     *                          operation returns the continuationToken value within the response body if the
     *                          listing operation did not return all blobs remaining to be listed
     *                          with the current page. The continuationToken value can be used as the value for
     *                          the marker parameter in a subsequent call to request the next page of list
     *                          items. The marker value is opaque to the client.
     * @param options - Options to find blobs by tags.
     */
    async findBlobsByTagsSegment(tagFilterSqlExpression, marker, options = {}) {
        return tracingClient.withSpan("BlobServiceClient-findBlobsByTagsSegment", options, async (updatedOptions) => {
            const response = utils_common_assertResponse(await this.serviceContext.filterBlobs({
                abortSignal: options.abortSignal,
                where: tagFilterSqlExpression,
                marker,
                maxPageSize: options.maxPageSize,
                tracingOptions: updatedOptions.tracingOptions,
            }));
            const wrappedResponse = {
                ...response,
                _response: response._response, // _response is made non-enumerable
                blobs: response.blobs.map((blob) => {
                    let tagValue = "";
                    if (blob.tags?.blobTagSet.length === 1) {
                        tagValue = blob.tags.blobTagSet[0].value;
                    }
                    return { ...blob, tags: toTags(blob.tags), tagValue };
                }),
            };
            return wrappedResponse;
        });
    }
    /**
     * Returns an AsyncIterableIterator for ServiceFindBlobsByTagsSegmentResponse.
     *
     * @param tagFilterSqlExpression -  The where parameter enables the caller to query blobs whose tags match a given expression.
     *                                         The given expression must evaluate to true for a blob to be returned in the results.
     *                                         The[OData - ABNF] filter syntax rule defines the formal grammar for the value of the where query parameter;
     *                                         however, only a subset of the OData filter syntax is supported in the Blob service.
     * @param marker - A string value that identifies the portion of
     *                          the list of blobs to be returned with the next listing operation. The
     *                          operation returns the continuationToken value within the response body if the
     *                          listing operation did not return all blobs remaining to be listed
     *                          with the current page. The continuationToken value can be used as the value for
     *                          the marker parameter in a subsequent call to request the next page of list
     *                          items. The marker value is opaque to the client.
     * @param options - Options to find blobs by tags.
     */
    async *findBlobsByTagsSegments(tagFilterSqlExpression, marker, options = {}) {
        let response;
        if (!!marker || marker === undefined) {
            do {
                response = await this.findBlobsByTagsSegment(tagFilterSqlExpression, marker, options);
                response.blobs = response.blobs || [];
                marker = response.continuationToken;
                yield response;
            } while (marker);
        }
    }
    /**
     * Returns an AsyncIterableIterator for blobs.
     *
     * @param tagFilterSqlExpression -  The where parameter enables the caller to query blobs whose tags match a given expression.
     *                                         The given expression must evaluate to true for a blob to be returned in the results.
     *                                         The[OData - ABNF] filter syntax rule defines the formal grammar for the value of the where query parameter;
     *                                         however, only a subset of the OData filter syntax is supported in the Blob service.
     * @param options - Options to findBlobsByTagsItems.
     */
    async *findBlobsByTagsItems(tagFilterSqlExpression, options = {}) {
        let marker;
        for await (const segment of this.findBlobsByTagsSegments(tagFilterSqlExpression, marker, options)) {
            yield* segment.blobs;
        }
    }
    /**
     * Returns an async iterable iterator to find all blobs with specified tag
     * under the specified account.
     *
     * .byPage() returns an async iterable iterator to list the blobs in pages.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/get-blob-service-properties
     *
     * ```ts snippet:BlobServiceClientFindBlobsByTags
     * import { BlobServiceClient } from "@azure/storage-blob";
     * import { DefaultAzureCredential } from "@azure/identity";
     *
     * const account = "<account>";
     * const blobServiceClient = new BlobServiceClient(
     *   `https://${account}.blob.core.windows.net`,
     *   new DefaultAzureCredential(),
     * );
     *
     * // Use for await to iterate the blobs
     * let i = 1;
     * for await (const blob of blobServiceClient.findBlobsByTags("tagkey='tagvalue'")) {
     *   console.log(`Blob ${i++}: ${blob.name}`);
     * }
     *
     * // Use iter.next() to iterate the blobs
     * i = 1;
     * const iter = blobServiceClient.findBlobsByTags("tagkey='tagvalue'");
     * let { value, done } = await iter.next();
     * while (!done) {
     *   console.log(`Blob ${i++}: ${value.name}`);
     *   ({ value, done } = await iter.next());
     * }
     *
     * // Use byPage() to iterate the blobs
     * i = 1;
     * for await (const page of blobServiceClient
     *   .findBlobsByTags("tagkey='tagvalue'")
     *   .byPage({ maxPageSize: 20 })) {
     *   for (const blob of page.blobs) {
     *     console.log(`Blob ${i++}: ${blob.name}`);
     *   }
     * }
     *
     * // Use paging with a marker
     * i = 1;
     * let iterator = blobServiceClient.findBlobsByTags("tagkey='tagvalue'").byPage({ maxPageSize: 2 });
     * let response = (await iterator.next()).value;
     * // Prints 2 blob names
     * if (response.blobs) {
     *   for (const blob of response.blobs) {
     *     console.log(`Blob ${i++}: ${blob.name}`);
     *   }
     * }
     * // Gets next marker
     * let marker = response.continuationToken;
     * // Passing next marker as continuationToken
     * iterator = blobServiceClient
     *   .findBlobsByTags("tagkey='tagvalue'")
     *   .byPage({ continuationToken: marker, maxPageSize: 10 });
     * response = (await iterator.next()).value;
     *
     * // Prints blob names
     * if (response.blobs) {
     *   for (const blob of response.blobs) {
     *     console.log(`Blob ${i++}: ${blob.name}`);
     *   }
     * }
     * ```
     *
     * @param tagFilterSqlExpression -  The where parameter enables the caller to query blobs whose tags match a given expression.
     *                                         The given expression must evaluate to true for a blob to be returned in the results.
     *                                         The[OData - ABNF] filter syntax rule defines the formal grammar for the value of the where query parameter;
     *                                         however, only a subset of the OData filter syntax is supported in the Blob service.
     * @param options - Options to find blobs by tags.
     */
    findBlobsByTags(tagFilterSqlExpression, options = {}) {
        // AsyncIterableIterator to iterate over blobs
        const listSegmentOptions = {
            ...options,
        };
        const iter = this.findBlobsByTagsItems(tagFilterSqlExpression, listSegmentOptions);
        return {
            /**
             * The next method, part of the iteration protocol
             */
            next() {
                return iter.next();
            },
            /**
             * The connection to the async iterator, part of the iteration protocol
             */
            [Symbol.asyncIterator]() {
                return this;
            },
            /**
             * Return an AsyncIterableIterator that works a page at a time
             */
            byPage: (settings = {}) => {
                return this.findBlobsByTagsSegments(tagFilterSqlExpression, settings.continuationToken, {
                    maxPageSize: settings.maxPageSize,
                    ...listSegmentOptions,
                });
            },
        };
    }
    /**
     * Returns an AsyncIterableIterator for ServiceListContainersSegmentResponses
     *
     * @param marker - A string value that identifies the portion of
     *                        the list of containers to be returned with the next listing operation. The
     *                        operation returns the continuationToken value within the response body if the
     *                        listing operation did not return all containers remaining to be listed
     *                        with the current page. The continuationToken value can be used as the value for
     *                        the marker parameter in a subsequent call to request the next page of list
     *                        items. The marker value is opaque to the client.
     * @param options - Options to list containers operation.
     */
    async *listSegments(marker, options = {}) {
        let listContainersSegmentResponse;
        if (!!marker || marker === undefined) {
            do {
                listContainersSegmentResponse = await this.listContainersSegment(marker, options);
                listContainersSegmentResponse.containerItems =
                    listContainersSegmentResponse.containerItems || [];
                marker = listContainersSegmentResponse.continuationToken;
                yield await listContainersSegmentResponse;
            } while (marker);
        }
    }
    /**
     * Returns an AsyncIterableIterator for Container Items
     *
     * @param options - Options to list containers operation.
     */
    async *listItems(options = {}) {
        let marker;
        for await (const segment of this.listSegments(marker, options)) {
            yield* segment.containerItems;
        }
    }
    /**
     * Returns an async iterable iterator to list all the containers
     * under the specified account.
     *
     * .byPage() returns an async iterable iterator to list the containers in pages.
     *
     * ```ts snippet:BlobServiceClientListContainers
     * import { BlobServiceClient } from "@azure/storage-blob";
     * import { DefaultAzureCredential } from "@azure/identity";
     *
     * const account = "<account>";
     * const blobServiceClient = new BlobServiceClient(
     *   `https://${account}.blob.core.windows.net`,
     *   new DefaultAzureCredential(),
     * );
     *
     * // Use for await to iterate the containers
     * let i = 1;
     * for await (const container of blobServiceClient.listContainers()) {
     *   console.log(`Container ${i++}: ${container.name}`);
     * }
     *
     * // Use iter.next() to iterate the containers
     * i = 1;
     * const iter = blobServiceClient.listContainers();
     * let { value, done } = await iter.next();
     * while (!done) {
     *   console.log(`Container ${i++}: ${value.name}`);
     *   ({ value, done } = await iter.next());
     * }
     *
     * // Use byPage() to iterate the containers
     * i = 1;
     * for await (const page of blobServiceClient.listContainers().byPage({ maxPageSize: 20 })) {
     *   for (const container of page.containerItems) {
     *     console.log(`Container ${i++}: ${container.name}`);
     *   }
     * }
     *
     * // Use paging with a marker
     * i = 1;
     * let iterator = blobServiceClient.listContainers().byPage({ maxPageSize: 2 });
     * let response = (await iterator.next()).value;
     *
     * // Prints 2 container names
     * if (response.containerItems) {
     *   for (const container of response.containerItems) {
     *     console.log(`Container ${i++}: ${container.name}`);
     *   }
     * }
     *
     * // Gets next marker
     * let marker = response.continuationToken;
     * // Passing next marker as continuationToken
     * iterator = blobServiceClient
     *   .listContainers()
     *   .byPage({ continuationToken: marker, maxPageSize: 10 });
     * response = (await iterator.next()).value;
     *
     * // Prints 10 container names
     * if (response.containerItems) {
     *   for (const container of response.containerItems) {
     *     console.log(`Container ${i++}: ${container.name}`);
     *   }
     * }
     * ```
     *
     * @param options - Options to list containers.
     * @returns An asyncIterableIterator that supports paging.
     */
    listContainers(options = {}) {
        if (options.prefix === "") {
            options.prefix = undefined;
        }
        const include = [];
        if (options.includeDeleted) {
            include.push("deleted");
        }
        if (options.includeMetadata) {
            include.push("metadata");
        }
        if (options.includeSystem) {
            include.push("system");
        }
        // AsyncIterableIterator to iterate over containers
        const listSegmentOptions = {
            ...options,
            ...(include.length > 0 ? { include } : {}),
        };
        const iter = this.listItems(listSegmentOptions);
        return {
            /**
             * The next method, part of the iteration protocol
             */
            next() {
                return iter.next();
            },
            /**
             * The connection to the async iterator, part of the iteration protocol
             */
            [Symbol.asyncIterator]() {
                return this;
            },
            /**
             * Return an AsyncIterableIterator that works a page at a time
             */
            byPage: (settings = {}) => {
                return this.listSegments(settings.continuationToken, {
                    maxPageSize: settings.maxPageSize,
                    ...listSegmentOptions,
                });
            },
        };
    }
    /**
     * ONLY AVAILABLE WHEN USING BEARER TOKEN AUTHENTICATION (TokenCredential).
     *
     * Retrieves a user delegation key for the Blob service. This is only a valid operation when using
     * bearer token authentication.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/get-user-delegation-key
     *
     * @param startsOn -      The start time for the user delegation SAS. Must be within 7 days of the current time
     * @param expiresOn -     The end time for the user delegation SAS. Must be within 7 days of the current time
     */
    async getUserDelegationKey(startsOn, expiresOn, options = {}) {
        return tracingClient.withSpan("BlobServiceClient-getUserDelegationKey", options, async (updatedOptions) => {
            const response = utils_common_assertResponse(await this.serviceContext.getUserDelegationKey({
                startsOn: utils_common_truncatedISO8061Date(startsOn, false),
                expiresOn: utils_common_truncatedISO8061Date(expiresOn, false),
            }, {
                abortSignal: options.abortSignal,
                tracingOptions: updatedOptions.tracingOptions,
            }));
            const userDelegationKey = {
                signedObjectId: response.signedObjectId,
                signedTenantId: response.signedTenantId,
                signedStartsOn: new Date(response.signedStartsOn),
                signedExpiresOn: new Date(response.signedExpiresOn),
                signedService: response.signedService,
                signedVersion: response.signedVersion,
                value: response.value,
            };
            const res = {
                _response: response._response,
                requestId: response.requestId,
                clientRequestId: response.clientRequestId,
                version: response.version,
                date: response.date,
                errorCode: response.errorCode,
                ...userDelegationKey,
            };
            return res;
        });
    }
    /**
     * Creates a BlobBatchClient object to conduct batch operations.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/blob-batch
     *
     * @returns A new BlobBatchClient object for this service.
     */
    getBlobBatchClient() {
        return new BlobBatchClient(this.url, this.pipeline);
    }
    /**
     * Only available for BlobServiceClient constructed with a shared key credential.
     *
     * Generates a Blob account Shared Access Signature (SAS) URI based on the client properties
     * and parameters passed in. The SAS is signed by the shared key credential of the client.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/create-account-sas
     *
     * @param expiresOn - Optional. The time at which the shared access signature becomes invalid. Default to an hour later if not provided.
     * @param permissions - Specifies the list of permissions to be associated with the SAS.
     * @param resourceTypes - Specifies the resource types associated with the shared access signature.
     * @param options - Optional parameters.
     * @returns An account SAS URI consisting of the URI to the resource represented by this client, followed by the generated SAS token.
     */
    generateAccountSasUrl(expiresOn, permissions = AccountSASPermissions.parse("r"), resourceTypes = "sco", options = {}) {
        if (!(this.credential instanceof StorageSharedKeyCredential)) {
            throw RangeError("Can only generate the account SAS when the client is initialized with a shared key credential");
        }
        if (expiresOn === undefined) {
            const now = new Date();
            expiresOn = new Date(now.getTime() + 3600 * 1000);
        }
        const sas = generateAccountSASQueryParameters({
            permissions,
            expiresOn,
            resourceTypes,
            services: AccountSASServices.parse("b").toString(),
            ...options,
        }, this.credential).toString();
        return utils_common_appendToURLQuery(this.url, sas);
    }
    /**
     * Only available for BlobServiceClient constructed with a shared key credential.
     *
     * Generates string to sign for a Blob account Shared Access Signature (SAS) URI based on
     * the client properties and parameters passed in. The SAS is signed by the shared key credential of the client.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/create-account-sas
     *
     * @param expiresOn - Optional. The time at which the shared access signature becomes invalid. Default to an hour later if not provided.
     * @param permissions - Specifies the list of permissions to be associated with the SAS.
     * @param resourceTypes - Specifies the resource types associated with the shared access signature.
     * @param options - Optional parameters.
     * @returns An account SAS URI consisting of the URI to the resource represented by this client, followed by the generated SAS token.
     */
    generateSasStringToSign(expiresOn, permissions = AccountSASPermissions.parse("r"), resourceTypes = "sco", options = {}) {
        if (!(this.credential instanceof StorageSharedKeyCredential)) {
            throw RangeError("Can only generate the account SAS when the client is initialized with a shared key credential");
        }
        if (expiresOn === undefined) {
            const now = new Date();
            expiresOn = new Date(now.getTime() + 3600 * 1000);
        }
        return generateAccountSASQueryParametersInternal({
            permissions,
            expiresOn,
            resourceTypes,
            services: AccountSASServices.parse("b").toString(),
            ...options,
        }, this.credential).stringToSign;
    }
}
//# sourceMappingURL=BlobServiceClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generatedModels.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/** Known values of {@link EncryptionAlgorithmType} that the service accepts. */
var generatedModels_KnownEncryptionAlgorithmType;
(function (KnownEncryptionAlgorithmType) {
    KnownEncryptionAlgorithmType["AES256"] = "AES256";
})(generatedModels_KnownEncryptionAlgorithmType || (generatedModels_KnownEncryptionAlgorithmType = {}));
//# sourceMappingURL=generatedModels.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.






















//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/upload/blob-upload.js
var blob_upload_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};






function uploadToBlobStorage(authenticatedUploadURL, uploadStream, contentType) {
    return blob_upload_awaiter(this, void 0, void 0, function* () {
        let uploadByteCount = 0;
        let lastProgressTime = Date.now();
        const abortController = new AbortController();
        const chunkTimer = (interval) => blob_upload_awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve, reject) => {
                const timer = setInterval(() => {
                    if (Date.now() - lastProgressTime > interval) {
                        reject(new Error('Upload progress stalled.'));
                    }
                }, interval);
                abortController.signal.addEventListener('abort', () => {
                    clearInterval(timer);
                    resolve();
                });
            });
        });
        const maxConcurrency = getConcurrency();
        const bufferSize = getUploadChunkSize();
        const blobClient = new BlobClient(authenticatedUploadURL);
        const blockBlobClient = blobClient.getBlockBlobClient();
        core_debug(`Uploading artifact to blob storage with maxConcurrency: ${maxConcurrency}, bufferSize: ${bufferSize}, contentType: ${contentType}`);
        const uploadCallback = (progress) => {
            info(`Uploaded bytes ${progress.loadedBytes}`);
            uploadByteCount = progress.loadedBytes;
            lastProgressTime = Date.now();
        };
        const options = {
            blobHTTPHeaders: { blobContentType: contentType },
            onProgress: uploadCallback,
            abortSignal: abortController.signal
        };
        let sha256Hash = undefined;
        const blobUploadStream = new external_stream_.PassThrough();
        const hashStream = external_crypto_namespaceObject.createHash('sha256');
        uploadStream.pipe(blobUploadStream); // This stream is used for the upload
        uploadStream.pipe(hashStream).setEncoding('hex'); // This stream is used to compute a hash of the content for integrity check
        info('Beginning upload of artifact content to blob storage');
        try {
            yield Promise.race([
                blockBlobClient.uploadStream(blobUploadStream, bufferSize, maxConcurrency, options),
                chunkTimer(getUploadChunkTimeout())
            ]);
        }
        catch (error) {
            if (NetworkError.isNetworkErrorCode(error === null || error === void 0 ? void 0 : error.code)) {
                throw new NetworkError(error === null || error === void 0 ? void 0 : error.code);
            }
            throw error;
        }
        finally {
            abortController.abort();
        }
        info('Finished uploading artifact content to blob storage!');
        hashStream.end();
        sha256Hash = hashStream.read();
        info(`SHA256 digest of uploaded artifact is ${sha256Hash}`);
        if (uploadByteCount === 0) {
            warning(`No data was uploaded to blob storage. Reported upload byte count is 0.`);
        }
        return {
            uploadSize: uploadByteCount,
            sha256Hash
        };
    });
}
//# sourceMappingURL=blob-upload.js.map
;// CONCATENATED MODULE: external "fs/promises"
const promises_namespaceObject = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("fs/promises");
// EXTERNAL MODULE: ./node_modules/archiver/index.js
var archiver = __nccwpck_require__(9392);
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/upload/stream.js
var stream_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};





// Custom stream transformer so we can set the highWaterMark property
// See https://github.com/nodejs/node/issues/8855
class WaterMarkedUploadStream extends external_stream_.Transform {
    constructor(bufferSize) {
        super({
            highWaterMark: bufferSize
        });
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    _transform(chunk, enc, cb) {
        cb(null, chunk);
    }
}
function createRawFileUploadStream(filePath) {
    return stream_awaiter(this, void 0, void 0, function* () {
        core_debug(`Creating raw file upload stream for: ${filePath}`);
        const bufferSize = getUploadChunkSize();
        const uploadStream = new WaterMarkedUploadStream(bufferSize);
        // Check if symlink and resolve the source path
        let sourcePath = filePath;
        const stats = yield external_fs_.promises.lstat(filePath);
        if (stats.isSymbolicLink()) {
            sourcePath = yield (0,promises_namespaceObject.realpath)(filePath);
        }
        // Create a read stream from the file and pipe it to the upload stream
        const fileStream = external_fs_.createReadStream(sourcePath, {
            highWaterMark: bufferSize
        });
        fileStream.on('error', error => {
            core_error('An error has occurred while reading the file for upload');
            core_error(String(error));
            uploadStream.destroy(new Error('An error has occurred during file read for the artifact'));
        });
        fileStream.pipe(uploadStream);
        return uploadStream;
    });
}
//# sourceMappingURL=stream.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/upload/zip.js
var zip_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};





const DEFAULT_COMPRESSION_LEVEL = 6;
function createZipUploadStream(uploadSpecification_1) {
    return zip_awaiter(this, arguments, void 0, function* (uploadSpecification, compressionLevel = DEFAULT_COMPRESSION_LEVEL) {
        core_debug(`Creating Artifact archive with compressionLevel: ${compressionLevel}`);
        const zip = archiver.create('zip', {
            highWaterMark: getUploadChunkSize(),
            zlib: { level: compressionLevel }
        });
        // register callbacks for various events during the zip lifecycle
        zip.on('error', zipErrorCallback);
        zip.on('warning', zipWarningCallback);
        zip.on('finish', zipFinishCallback);
        zip.on('end', zipEndCallback);
        for (const file of uploadSpecification) {
            if (file.sourcePath !== null) {
                // Check if symlink and resolve the source path
                let sourcePath = file.sourcePath;
                if (file.stats.isSymbolicLink()) {
                    sourcePath = yield (0,promises_namespaceObject.realpath)(file.sourcePath);
                }
                // Add the file to the zip
                zip.file(sourcePath, {
                    name: file.destinationPath
                });
            }
            else {
                // Add a directory to the zip
                zip.append('', { name: file.destinationPath });
            }
        }
        const bufferSize = getUploadChunkSize();
        const zipUploadStream = new WaterMarkedUploadStream(bufferSize);
        core_debug(`Zip write high watermark value ${zipUploadStream.writableHighWaterMark}`);
        core_debug(`Zip read high watermark value ${zipUploadStream.readableHighWaterMark}`);
        zip.pipe(zipUploadStream);
        zip.finalize();
        return zipUploadStream;
    });
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const zipErrorCallback = (error) => {
    core_error('An error has occurred while creating the zip file for upload');
    info(error);
    throw new Error('An error has occurred during zip creation for the artifact');
};
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const zipWarningCallback = (error) => {
    if (error.code === 'ENOENT') {
        warning('ENOENT warning during artifact zip creation. No such file or directory');
        info(error);
    }
    else {
        warning(`A non-blocking warning has occurred during artifact zip creation: ${error.code}`);
        info(error);
    }
};
const zipFinishCallback = () => {
    core_debug('Zip stream for upload has finished.');
};
const zipEndCallback = () => {
    core_debug('Zip stream for upload has ended.');
};
//# sourceMappingURL=zip.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/upload/types.js

/**
 * Maps file extensions to MIME types
 */
const types_mimeTypes = {
    // Text
    '.txt': 'text/plain',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
    '.csv': 'text/csv',
    '.xml': 'text/xml',
    '.md': 'text/markdown',
    // JavaScript/JSON
    '.js': 'application/javascript',
    '.mjs': 'application/javascript',
    '.json': 'application/json',
    // Images
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
    '.ico': 'image/x-icon',
    '.bmp': 'image/bmp',
    '.tiff': 'image/tiff',
    '.tif': 'image/tiff',
    // Audio
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.ogg': 'audio/ogg',
    '.flac': 'audio/flac',
    // Video
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
    '.avi': 'video/x-msvideo',
    '.mov': 'video/quicktime',
    // Documents
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    // Archives
    '.zip': 'application/zip',
    '.tar': 'application/x-tar',
    '.gz': 'application/gzip',
    '.rar': 'application/vnd.rar',
    '.7z': 'application/x-7z-compressed',
    // Code/Data
    '.wasm': 'application/wasm',
    '.yaml': 'application/x-yaml',
    '.yml': 'application/x-yaml',
    // Fonts
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.otf': 'font/otf',
    '.eot': 'application/vnd.ms-fontobject'
};
/**
 * Gets the MIME type for a file based on its extension
 */
function getMimeType(filePath) {
    const ext = external_path_.extname(filePath).toLowerCase();
    return types_mimeTypes[ext] || 'application/octet-stream';
}
//# sourceMappingURL=types.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/upload/upload-artifact.js
var upload_artifact_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};














function uploadArtifact(name, files, rootDirectory, options) {
    return upload_artifact_awaiter(this, void 0, void 0, function* () {
        let artifactFileName = `${name}.zip`;
        if (options === null || options === void 0 ? void 0 : options.skipArchive) {
            if (files.length === 0) {
                throw new FilesNotFoundError([]);
            }
            if (files.length > 1) {
                throw new Error('skipArchive option is only supported when uploading a single file');
            }
            if (!external_fs_.existsSync(files[0])) {
                throw new FilesNotFoundError(files);
            }
            artifactFileName = external_path_.basename(files[0]);
            name = artifactFileName;
        }
        validateArtifactName(name);
        validateRootDirectory(rootDirectory);
        let zipSpecification = [];
        if (!(options === null || options === void 0 ? void 0 : options.skipArchive)) {
            zipSpecification = getUploadZipSpecification(files, rootDirectory);
            if (zipSpecification.length === 0) {
                throw new FilesNotFoundError(zipSpecification.flatMap(s => (s.sourcePath ? [s.sourcePath] : [])));
            }
        }
        const contentType = getMimeType(artifactFileName);
        // get the IDs needed for the artifact creation
        const backendIds = getBackendIdsFromToken();
        // create the artifact client
        const artifactClient = internalArtifactTwirpClient();
        // create the artifact
        const createArtifactReq = {
            workflowRunBackendId: backendIds.workflowRunBackendId,
            workflowJobRunBackendId: backendIds.workflowJobRunBackendId,
            name,
            mimeType: StringValue.create({ value: contentType }),
            version: 7
        };
        // if there is a retention period, add it to the request
        const expiresAt = getExpiration(options === null || options === void 0 ? void 0 : options.retentionDays);
        if (expiresAt) {
            createArtifactReq.expiresAt = expiresAt;
        }
        const createArtifactResp = yield artifactClient.CreateArtifact(createArtifactReq);
        if (!createArtifactResp.ok) {
            throw new InvalidResponseError('CreateArtifact: response from backend was not ok');
        }
        let stream;
        if (options === null || options === void 0 ? void 0 : options.skipArchive) {
            // Upload raw file without archiving
            stream = yield createRawFileUploadStream(files[0]);
        }
        else {
            // Create and upload zip archive
            stream = yield createZipUploadStream(zipSpecification, options === null || options === void 0 ? void 0 : options.compressionLevel);
        }
        info(`Uploading artifact: ${artifactFileName}`);
        const uploadResult = yield uploadToBlobStorage(createArtifactResp.signedUploadUrl, stream, contentType);
        // finalize the artifact
        const finalizeArtifactReq = {
            workflowRunBackendId: backendIds.workflowRunBackendId,
            workflowJobRunBackendId: backendIds.workflowJobRunBackendId,
            name,
            size: uploadResult.uploadSize ? uploadResult.uploadSize.toString() : '0'
        };
        if (uploadResult.sha256Hash) {
            finalizeArtifactReq.hash = StringValue.create({
                value: `sha256:${uploadResult.sha256Hash}`
            });
        }
        info(`Finalizing artifact upload`);
        const finalizeArtifactResp = yield artifactClient.FinalizeArtifact(finalizeArtifactReq);
        if (!finalizeArtifactResp.ok) {
            throw new InvalidResponseError('FinalizeArtifact: response from backend was not ok');
        }
        const artifactId = BigInt(finalizeArtifactResp.artifactId);
        info(`Artifact ${name} successfully finalized. Artifact ID ${artifactId}`);
        return {
            size: uploadResult.uploadSize,
            digest: uploadResult.sha256Hash,
            id: Number(artifactId)
        };
    });
}
//# sourceMappingURL=upload-artifact.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/github/lib/context.js


class Context {
    /**
     * Hydrate the context from the environment
     */
    constructor() {
        var _a, _b, _c;
        this.payload = {};
        if (process.env.GITHUB_EVENT_PATH) {
            if ((0,external_fs_.existsSync)(process.env.GITHUB_EVENT_PATH)) {
                this.payload = JSON.parse((0,external_fs_.readFileSync)(process.env.GITHUB_EVENT_PATH, { encoding: 'utf8' }));
            }
            else {
                const path = process.env.GITHUB_EVENT_PATH;
                process.stdout.write(`GITHUB_EVENT_PATH ${path} does not exist${external_os_.EOL}`);
            }
        }
        this.eventName = process.env.GITHUB_EVENT_NAME;
        this.sha = process.env.GITHUB_SHA;
        this.ref = process.env.GITHUB_REF;
        this.workflow = process.env.GITHUB_WORKFLOW;
        this.action = process.env.GITHUB_ACTION;
        this.actor = process.env.GITHUB_ACTOR;
        this.job = process.env.GITHUB_JOB;
        this.runAttempt = parseInt(process.env.GITHUB_RUN_ATTEMPT, 10);
        this.runNumber = parseInt(process.env.GITHUB_RUN_NUMBER, 10);
        this.runId = parseInt(process.env.GITHUB_RUN_ID, 10);
        this.apiUrl = (_a = process.env.GITHUB_API_URL) !== null && _a !== void 0 ? _a : `https://api.github.com`;
        this.serverUrl = (_b = process.env.GITHUB_SERVER_URL) !== null && _b !== void 0 ? _b : `https://github.com`;
        this.graphqlUrl =
            (_c = process.env.GITHUB_GRAPHQL_URL) !== null && _c !== void 0 ? _c : `https://api.github.com/graphql`;
    }
    get issue() {
        const payload = this.payload;
        return Object.assign(Object.assign({}, this.repo), { number: (payload.issue || payload.pull_request || payload).number });
    }
    get repo() {
        if (process.env.GITHUB_REPOSITORY) {
            const [owner, repo] = process.env.GITHUB_REPOSITORY.split('/');
            return { owner, repo };
        }
        if (this.payload.repository) {
            return {
                owner: this.payload.repository.owner.login,
                repo: this.payload.repository.name
            };
        }
        throw new Error("context.repo requires a GITHUB_REPOSITORY environment variable like 'owner/repo'");
    }
}
//# sourceMappingURL=context.js.map
// EXTERNAL MODULE: ./node_modules/@actions/github/node_modules/@actions/http-client/lib/index.js
var lib = __nccwpck_require__(9659);
;// CONCATENATED MODULE: ./node_modules/@actions/github/lib/internal/utils.js
var utils_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};


function getAuthString(token, options) {
    if (!token && !options.auth) {
        throw new Error('Parameter token or opts.auth is required');
    }
    else if (token && options.auth) {
        throw new Error('Parameters token and opts.auth may not both be specified');
    }
    return typeof options.auth === 'string' ? options.auth : `token ${token}`;
}
function getProxyAgent(destinationUrl) {
    const hc = new lib.HttpClient();
    return hc.getAgent(destinationUrl);
}
function getProxyAgentDispatcher(destinationUrl) {
    const hc = new lib.HttpClient();
    return hc.getAgentDispatcher(destinationUrl);
}
function getProxyFetch(destinationUrl) {
    const httpDispatcher = getProxyAgentDispatcher(destinationUrl);
    const proxyFetch = (url, opts) => utils_awaiter(this, void 0, void 0, function* () {
        return (0,undici.fetch)(url, Object.assign(Object.assign({}, opts), { dispatcher: httpDispatcher }));
    });
    return proxyFetch;
}
function getApiBaseUrl() {
    return process.env['GITHUB_API_URL'] || 'https://api.github.com';
}
//# sourceMappingURL=utils.js.map
;// CONCATENATED MODULE: ./node_modules/universal-user-agent/index.js
function getUserAgent() {
  if (typeof navigator === "object" && "userAgent" in navigator) {
    return navigator.userAgent;
  }

  if (typeof process === "object" && process.version !== undefined) {
    return `Node.js/${process.version.substr(1)} (${process.platform}; ${
      process.arch
    })`;
  }

  return "<environment undetectable>";
}

;// CONCATENATED MODULE: ./node_modules/before-after-hook/lib/register.js
// @ts-check

function register(state, name, method, options) {
  if (typeof method !== "function") {
    throw new Error("method for before hook must be a function");
  }

  if (!options) {
    options = {};
  }

  if (Array.isArray(name)) {
    return name.reverse().reduce((callback, name) => {
      return register.bind(null, state, name, callback, options);
    }, method)();
  }

  return Promise.resolve().then(() => {
    if (!state.registry[name]) {
      return method(options);
    }

    return state.registry[name].reduce((method, registered) => {
      return registered.hook.bind(null, method, options);
    }, method)();
  });
}

;// CONCATENATED MODULE: ./node_modules/before-after-hook/lib/add.js
// @ts-check

function addHook(state, kind, name, hook) {
  const orig = hook;
  if (!state.registry[name]) {
    state.registry[name] = [];
  }

  if (kind === "before") {
    hook = (method, options) => {
      return Promise.resolve()
        .then(orig.bind(null, options))
        .then(method.bind(null, options));
    };
  }

  if (kind === "after") {
    hook = (method, options) => {
      let result;
      return Promise.resolve()
        .then(method.bind(null, options))
        .then((result_) => {
          result = result_;
          return orig(result, options);
        })
        .then(() => {
          return result;
        });
    };
  }

  if (kind === "error") {
    hook = (method, options) => {
      return Promise.resolve()
        .then(method.bind(null, options))
        .catch((error) => {
          return orig(error, options);
        });
    };
  }

  state.registry[name].push({
    hook: hook,
    orig: orig,
  });
}

;// CONCATENATED MODULE: ./node_modules/before-after-hook/lib/remove.js
// @ts-check

function removeHook(state, name, method) {
  if (!state.registry[name]) {
    return;
  }

  const index = state.registry[name]
    .map((registered) => {
      return registered.orig;
    })
    .indexOf(method);

  if (index === -1) {
    return;
  }

  state.registry[name].splice(index, 1);
}

;// CONCATENATED MODULE: ./node_modules/before-after-hook/index.js
// @ts-check





// bind with array of arguments: https://stackoverflow.com/a/21792913
const bind = Function.bind;
const bindable = bind.bind(bind);

function bindApi(hook, state, name) {
  const removeHookRef = bindable(removeHook, null).apply(
    null,
    name ? [state, name] : [state]
  );
  hook.api = { remove: removeHookRef };
  hook.remove = removeHookRef;
  ["before", "error", "after", "wrap"].forEach((kind) => {
    const args = name ? [state, kind, name] : [state, kind];
    hook[kind] = hook.api[kind] = bindable(addHook, null).apply(null, args);
  });
}

function Singular() {
  const singularHookName = Symbol("Singular");
  const singularHookState = {
    registry: {},
  };
  const singularHook = register.bind(null, singularHookState, singularHookName);
  bindApi(singularHook, singularHookState, singularHookName);
  return singularHook;
}

function Collection() {
  const state = {
    registry: {},
  };

  const hook = register.bind(null, state);
  bindApi(hook, state);

  return hook;
}

/* harmony default export */ const before_after_hook = ({ Singular, Collection });

;// CONCATENATED MODULE: ./node_modules/@octokit/endpoint/dist-bundle/index.js
// pkg/dist-src/defaults.js


// pkg/dist-src/version.js
var VERSION = "0.0.0-development";

// pkg/dist-src/defaults.js
var userAgent = `octokit-endpoint.js/${VERSION} ${getUserAgent()}`;
var DEFAULTS = {
  method: "GET",
  baseUrl: "https://api.github.com",
  headers: {
    accept: "application/vnd.github.v3+json",
    "user-agent": userAgent
  },
  mediaType: {
    format: ""
  }
};

// pkg/dist-src/util/lowercase-keys.js
function dist_bundle_lowercaseKeys(object) {
  if (!object) {
    return {};
  }
  return Object.keys(object).reduce((newObj, key) => {
    newObj[key.toLowerCase()] = object[key];
    return newObj;
  }, {});
}

// pkg/dist-src/util/is-plain-object.js
function isPlainObject(value) {
  if (typeof value !== "object" || value === null) return false;
  if (Object.prototype.toString.call(value) !== "[object Object]") return false;
  const proto = Object.getPrototypeOf(value);
  if (proto === null) return true;
  const Ctor = Object.prototype.hasOwnProperty.call(proto, "constructor") && proto.constructor;
  return typeof Ctor === "function" && Ctor instanceof Ctor && Function.prototype.call(Ctor) === Function.prototype.call(value);
}

// pkg/dist-src/util/merge-deep.js
function mergeDeep(defaults, options) {
  const result = Object.assign({}, defaults);
  Object.keys(options).forEach((key) => {
    if (isPlainObject(options[key])) {
      if (!(key in defaults)) Object.assign(result, { [key]: options[key] });
      else result[key] = mergeDeep(defaults[key], options[key]);
    } else {
      Object.assign(result, { [key]: options[key] });
    }
  });
  return result;
}

// pkg/dist-src/util/remove-undefined-properties.js
function removeUndefinedProperties(obj) {
  for (const key in obj) {
    if (obj[key] === void 0) {
      delete obj[key];
    }
  }
  return obj;
}

// pkg/dist-src/merge.js
function merge(defaults, route, options) {
  if (typeof route === "string") {
    let [method, url] = route.split(" ");
    options = Object.assign(url ? { method, url } : { url: method }, options);
  } else {
    options = Object.assign({}, route);
  }
  options.headers = dist_bundle_lowercaseKeys(options.headers);
  removeUndefinedProperties(options);
  removeUndefinedProperties(options.headers);
  const mergedOptions = mergeDeep(defaults || {}, options);
  if (options.url === "/graphql") {
    if (defaults && defaults.mediaType.previews?.length) {
      mergedOptions.mediaType.previews = defaults.mediaType.previews.filter(
        (preview) => !mergedOptions.mediaType.previews.includes(preview)
      ).concat(mergedOptions.mediaType.previews);
    }
    mergedOptions.mediaType.previews = (mergedOptions.mediaType.previews || []).map((preview) => preview.replace(/-preview/, ""));
  }
  return mergedOptions;
}

// pkg/dist-src/util/add-query-parameters.js
function addQueryParameters(url, parameters) {
  const separator = /\?/.test(url) ? "&" : "?";
  const names = Object.keys(parameters);
  if (names.length === 0) {
    return url;
  }
  return url + separator + names.map((name) => {
    if (name === "q") {
      return "q=" + parameters.q.split("+").map(encodeURIComponent).join("+");
    }
    return `${name}=${encodeURIComponent(parameters[name])}`;
  }).join("&");
}

// pkg/dist-src/util/extract-url-variable-names.js
var urlVariableRegex = /\{[^{}}]+\}/g;
function removeNonChars(variableName) {
  return variableName.replace(/(?:^\W+)|(?:(?<!\W)\W+$)/g, "").split(/,/);
}
function extractUrlVariableNames(url) {
  const matches = url.match(urlVariableRegex);
  if (!matches) {
    return [];
  }
  return matches.map(removeNonChars).reduce((a, b) => a.concat(b), []);
}

// pkg/dist-src/util/omit.js
function omit(object, keysToOmit) {
  const result = { __proto__: null };
  for (const key of Object.keys(object)) {
    if (keysToOmit.indexOf(key) === -1) {
      result[key] = object[key];
    }
  }
  return result;
}

// pkg/dist-src/util/url-template.js
function encodeReserved(str) {
  return str.split(/(%[0-9A-Fa-f]{2})/g).map(function(part) {
    if (!/%[0-9A-Fa-f]/.test(part)) {
      part = encodeURI(part).replace(/%5B/g, "[").replace(/%5D/g, "]");
    }
    return part;
  }).join("");
}
function encodeUnreserved(str) {
  return encodeURIComponent(str).replace(/[!'()*]/g, function(c) {
    return "%" + c.charCodeAt(0).toString(16).toUpperCase();
  });
}
function encodeValue(operator, value, key) {
  value = operator === "+" || operator === "#" ? encodeReserved(value) : encodeUnreserved(value);
  if (key) {
    return encodeUnreserved(key) + "=" + value;
  } else {
    return value;
  }
}
function isDefined(value) {
  return value !== void 0 && value !== null;
}
function isKeyOperator(operator) {
  return operator === ";" || operator === "&" || operator === "?";
}
function getValues(context, operator, key, modifier) {
  var value = context[key], result = [];
  if (isDefined(value) && value !== "") {
    if (typeof value === "string" || typeof value === "number" || typeof value === "bigint" || typeof value === "boolean") {
      value = value.toString();
      if (modifier && modifier !== "*") {
        value = value.substring(0, parseInt(modifier, 10));
      }
      result.push(
        encodeValue(operator, value, isKeyOperator(operator) ? key : "")
      );
    } else {
      if (modifier === "*") {
        if (Array.isArray(value)) {
          value.filter(isDefined).forEach(function(value2) {
            result.push(
              encodeValue(operator, value2, isKeyOperator(operator) ? key : "")
            );
          });
        } else {
          Object.keys(value).forEach(function(k) {
            if (isDefined(value[k])) {
              result.push(encodeValue(operator, value[k], k));
            }
          });
        }
      } else {
        const tmp = [];
        if (Array.isArray(value)) {
          value.filter(isDefined).forEach(function(value2) {
            tmp.push(encodeValue(operator, value2));
          });
        } else {
          Object.keys(value).forEach(function(k) {
            if (isDefined(value[k])) {
              tmp.push(encodeUnreserved(k));
              tmp.push(encodeValue(operator, value[k].toString()));
            }
          });
        }
        if (isKeyOperator(operator)) {
          result.push(encodeUnreserved(key) + "=" + tmp.join(","));
        } else if (tmp.length !== 0) {
          result.push(tmp.join(","));
        }
      }
    }
  } else {
    if (operator === ";") {
      if (isDefined(value)) {
        result.push(encodeUnreserved(key));
      }
    } else if (value === "" && (operator === "&" || operator === "?")) {
      result.push(encodeUnreserved(key) + "=");
    } else if (value === "") {
      result.push("");
    }
  }
  return result;
}
function parseUrl(template) {
  return {
    expand: expand.bind(null, template)
  };
}
function expand(template, context) {
  var operators = ["+", "#", ".", "/", ";", "?", "&"];
  template = template.replace(
    /\{([^\{\}]+)\}|([^\{\}]+)/g,
    function(_, expression, literal) {
      if (expression) {
        let operator = "";
        const values = [];
        if (operators.indexOf(expression.charAt(0)) !== -1) {
          operator = expression.charAt(0);
          expression = expression.substr(1);
        }
        expression.split(/,/g).forEach(function(variable) {
          var tmp = /([^:\*]*)(?::(\d+)|(\*))?/.exec(variable);
          values.push(getValues(context, operator, tmp[1], tmp[2] || tmp[3]));
        });
        if (operator && operator !== "+") {
          var separator = ",";
          if (operator === "?") {
            separator = "&";
          } else if (operator !== "#") {
            separator = operator;
          }
          return (values.length !== 0 ? operator : "") + values.join(separator);
        } else {
          return values.join(",");
        }
      } else {
        return encodeReserved(literal);
      }
    }
  );
  if (template === "/") {
    return template;
  } else {
    return template.replace(/\/$/, "");
  }
}

// pkg/dist-src/parse.js
function dist_bundle_parse(options) {
  let method = options.method.toUpperCase();
  let url = (options.url || "/").replace(/:([a-z]\w+)/g, "{$1}");
  let headers = Object.assign({}, options.headers);
  let body;
  let parameters = omit(options, [
    "method",
    "baseUrl",
    "url",
    "headers",
    "request",
    "mediaType"
  ]);
  const urlVariableNames = extractUrlVariableNames(url);
  url = parseUrl(url).expand(parameters);
  if (!/^http/.test(url)) {
    url = options.baseUrl + url;
  }
  const omittedParameters = Object.keys(options).filter((option) => urlVariableNames.includes(option)).concat("baseUrl");
  const remainingParameters = omit(parameters, omittedParameters);
  const isBinaryRequest = /application\/octet-stream/i.test(headers.accept);
  if (!isBinaryRequest) {
    if (options.mediaType.format) {
      headers.accept = headers.accept.split(/,/).map(
        (format) => format.replace(
          /application\/vnd(\.\w+)(\.v3)?(\.\w+)?(\+json)?$/,
          `application/vnd$1$2.${options.mediaType.format}`
        )
      ).join(",");
    }
    if (url.endsWith("/graphql")) {
      if (options.mediaType.previews?.length) {
        const previewsFromAcceptHeader = headers.accept.match(/(?<![\w-])[\w-]+(?=-preview)/g) || [];
        headers.accept = previewsFromAcceptHeader.concat(options.mediaType.previews).map((preview) => {
          const format = options.mediaType.format ? `.${options.mediaType.format}` : "+json";
          return `application/vnd.github.${preview}-preview${format}`;
        }).join(",");
      }
    }
  }
  if (["GET", "HEAD"].includes(method)) {
    url = addQueryParameters(url, remainingParameters);
  } else {
    if ("data" in remainingParameters) {
      body = remainingParameters.data;
    } else {
      if (Object.keys(remainingParameters).length) {
        body = remainingParameters;
      }
    }
  }
  if (!headers["content-type"] && typeof body !== "undefined") {
    headers["content-type"] = "application/json; charset=utf-8";
  }
  if (["PATCH", "PUT"].includes(method) && typeof body === "undefined") {
    body = "";
  }
  return Object.assign(
    { method, url, headers },
    typeof body !== "undefined" ? { body } : null,
    options.request ? { request: options.request } : null
  );
}

// pkg/dist-src/endpoint-with-defaults.js
function endpointWithDefaults(defaults, route, options) {
  return dist_bundle_parse(merge(defaults, route, options));
}

// pkg/dist-src/with-defaults.js
function withDefaults(oldDefaults, newDefaults) {
  const DEFAULTS2 = merge(oldDefaults, newDefaults);
  const endpoint2 = endpointWithDefaults.bind(null, DEFAULTS2);
  return Object.assign(endpoint2, {
    DEFAULTS: DEFAULTS2,
    defaults: withDefaults.bind(null, DEFAULTS2),
    merge: merge.bind(null, DEFAULTS2),
    parse: dist_bundle_parse
  });
}

// pkg/dist-src/index.js
var endpoint = withDefaults(null, DEFAULTS);


// EXTERNAL MODULE: ./node_modules/fast-content-type-parse/index.js
var fast_content_type_parse = __nccwpck_require__(1120);
;// CONCATENATED MODULE: ./node_modules/json-with-bigint/json-with-bigint.js
const noiseValue = /^-?\d+n+$/; // Noise - strings that match the custom format before being converted to it
const originalStringify = JSON.stringify;
const originalParse = JSON.parse;

/*
  Function to serialize value to a JSON string.
  Converts BigInt values to a custom format (strings with digits and "n" at the end) and then converts them to proper big integers in a JSON string.
*/
const JSONStringify = (value, replacer, space) => {
  if ("rawJSON" in JSON) {
    return originalStringify(
      value,
      (key, value) => {
        if (typeof value === "bigint") return JSON.rawJSON(value.toString());

        if (typeof replacer === "function") return replacer(key, value);

        if (Array.isArray(replacer) && replacer.includes(key)) return value;

        return value;
      },
      space
    );
  }

  if (!value) return originalStringify(value, replacer, space);

  const bigInts = /([\[:])?"(-?\d+)n"($|([\\n]|\s)*(\s|[\\n])*[,\}\]])/g;
  const noise = /([\[:])?("-?\d+n+)n("$|"([\\n]|\s)*(\s|[\\n])*[,\}\]])/g;
  const convertedToCustomJSON = originalStringify(
    value,
    (key, value) => {
      const isNoise =
        typeof value === "string" && Boolean(value.match(noiseValue));

      if (isNoise) return value.toString() + "n"; // Mark noise values with additional "n" to offset the deletion of one "n" during the processing

      if (typeof value === "bigint") return value.toString() + "n";

      if (typeof replacer === "function") return replacer(key, value);

      if (Array.isArray(replacer) && replacer.includes(key)) return value;

      return value;
    },
    space
  );
  const processedJSON = convertedToCustomJSON.replace(bigInts, "$1$2$3"); // Delete one "n" off the end of every BigInt value
  const denoisedJSON = processedJSON.replace(noise, "$1$2$3"); // Remove one "n" off the end of every noisy string

  return denoisedJSON;
};

/*
  Function to check if the JSON.parse's context.source feature is supported.
*/
const isContextSourceSupported = () =>
  JSON.parse("1", (_, __, context) => !!context && context.source === "1");

/*
  Faster (2x) and simpler function to parse JSON.
  Based on JSON.parse's context.source feature, which is not universally available now.
  Does not support the legacy custom format, used in the first version of this library.
*/
const JSONParseV2 = (text, reviver) => {
  const intRegex = /^-?\d+$/;

  return JSON.parse(text, (key, value, context) => {
    const isBigNumber =
      typeof value === "number" &&
      (value > Number.MAX_SAFE_INTEGER || value < Number.MIN_SAFE_INTEGER);
    const isInt = intRegex.test(context.source);
    const isBigInt = isBigNumber && isInt;

    if (isBigInt) return BigInt(context.source);

    if (typeof reviver !== "function") return value;

    return reviver(key, value, context);
  });
};

/*
  Function to parse JSON.
  If JSON has number values greater than Number.MAX_SAFE_INTEGER, we convert those values to a custom format, then parse them to BigInt values.
  Other types of values are not affected and parsed as native JSON.parse() would parse them.
*/
const JSONParse = (text, reviver) => {
  if (!text) return originalParse(text, reviver);

  if (isContextSourceSupported()) return JSONParseV2(text, reviver); // Shortcut to a faster (2x) and simpler version

  const MAX_INT = Number.MAX_SAFE_INTEGER.toString();
  const MAX_DIGITS = MAX_INT.length;
  const stringsOrLargeNumbers =
    /"(?:\\.|[^"])*"|-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?/g;
  const noiseValueWithQuotes = /^"-?\d+n+"$/; // Noise - strings that match the custom format before being converted to it
  const customFormat = /^-?\d+n$/;

  // Find and mark big numbers with "n"
  const serializedData = text.replace(
    stringsOrLargeNumbers,
    (text, digits, fractional, exponential) => {
      const isString = text[0] === '"';
      const isNoise = isString && Boolean(text.match(noiseValueWithQuotes));

      if (isNoise) return text.substring(0, text.length - 1) + 'n"'; // Mark noise values with additional "n" to offset the deletion of one "n" during the processing

      const isFractionalOrExponential = fractional || exponential;
      const isLessThanMaxSafeInt =
        digits &&
        (digits.length < MAX_DIGITS ||
          (digits.length === MAX_DIGITS && digits <= MAX_INT)); // With a fixed number of digits, we can correctly use lexicographical comparison to do a numeric comparison

      if (isString || isFractionalOrExponential || isLessThanMaxSafeInt)
        return text;

      return '"' + text + 'n"';
    }
  );

  // Convert marked big numbers to BigInt
  return originalParse(serializedData, (key, value, context) => {
    const isCustomFormatBigInt =
      typeof value === "string" && Boolean(value.match(customFormat));

    if (isCustomFormatBigInt)
      return BigInt(value.substring(0, value.length - 1));

    const isNoiseValue =
      typeof value === "string" && Boolean(value.match(noiseValue));

    if (isNoiseValue) return value.substring(0, value.length - 1); // Remove one "n" off the end of the noisy string

    if (typeof reviver !== "function") return value;

    return reviver(key, value, context);
  });
};

;// CONCATENATED MODULE: ./node_modules/@octokit/request-error/dist-src/index.js
class RequestError extends Error {
  name;
  /**
   * http status code
   */
  status;
  /**
   * Request options that lead to the error.
   */
  request;
  /**
   * Response object if a response was received
   */
  response;
  constructor(message, statusCode, options) {
    super(message, { cause: options.cause });
    this.name = "HttpError";
    this.status = Number.parseInt(statusCode);
    if (Number.isNaN(this.status)) {
      this.status = 0;
    }
    /* v8 ignore else -- @preserve -- Bug with vitest coverage where it sees an else branch that doesn't exist */
    if ("response" in options) {
      this.response = options.response;
    }
    const requestCopy = Object.assign({}, options.request);
    if (options.request.headers.authorization) {
      requestCopy.headers = Object.assign({}, options.request.headers, {
        authorization: options.request.headers.authorization.replace(
          /(?<! ) .*$/,
          " [REDACTED]"
        )
      });
    }
    requestCopy.url = requestCopy.url.replace(/\bclient_secret=\w+/g, "client_secret=[REDACTED]").replace(/\baccess_token=\w+/g, "access_token=[REDACTED]");
    this.request = requestCopy;
  }
}


;// CONCATENATED MODULE: ./node_modules/@octokit/request/dist-bundle/index.js
// pkg/dist-src/index.js


// pkg/dist-src/defaults.js


// pkg/dist-src/version.js
var dist_bundle_VERSION = "10.0.8";

// pkg/dist-src/defaults.js
var defaults_default = {
  headers: {
    "user-agent": `octokit-request.js/${dist_bundle_VERSION} ${getUserAgent()}`
  }
};

// pkg/dist-src/fetch-wrapper.js



// pkg/dist-src/is-plain-object.js
function dist_bundle_isPlainObject(value) {
  if (typeof value !== "object" || value === null) return false;
  if (Object.prototype.toString.call(value) !== "[object Object]") return false;
  const proto = Object.getPrototypeOf(value);
  if (proto === null) return true;
  const Ctor = Object.prototype.hasOwnProperty.call(proto, "constructor") && proto.constructor;
  return typeof Ctor === "function" && Ctor instanceof Ctor && Function.prototype.call(Ctor) === Function.prototype.call(value);
}

// pkg/dist-src/fetch-wrapper.js

var noop = () => "";
async function fetchWrapper(requestOptions) {
  const fetch = requestOptions.request?.fetch || globalThis.fetch;
  if (!fetch) {
    throw new Error(
      "fetch is not set. Please pass a fetch implementation as new Octokit({ request: { fetch }}). Learn more at https://github.com/octokit/octokit.js/#fetch-missing"
    );
  }
  const log = requestOptions.request?.log || console;
  const parseSuccessResponseBody = requestOptions.request?.parseSuccessResponseBody !== false;
  const body = dist_bundle_isPlainObject(requestOptions.body) || Array.isArray(requestOptions.body) ? JSONStringify(requestOptions.body) : requestOptions.body;
  const requestHeaders = Object.fromEntries(
    Object.entries(requestOptions.headers).map(([name, value]) => [
      name,
      String(value)
    ])
  );
  let fetchResponse;
  try {
    fetchResponse = await fetch(requestOptions.url, {
      method: requestOptions.method,
      body,
      redirect: requestOptions.request?.redirect,
      headers: requestHeaders,
      signal: requestOptions.request?.signal,
      // duplex must be set if request.body is ReadableStream or Async Iterables.
      // See https://fetch.spec.whatwg.org/#dom-requestinit-duplex.
      ...requestOptions.body && { duplex: "half" }
    });
  } catch (error) {
    let message = "Unknown Error";
    if (error instanceof Error) {
      if (error.name === "AbortError") {
        error.status = 500;
        throw error;
      }
      message = error.message;
      if (error.name === "TypeError" && "cause" in error) {
        if (error.cause instanceof Error) {
          message = error.cause.message;
        } else if (typeof error.cause === "string") {
          message = error.cause;
        }
      }
    }
    const requestError = new RequestError(message, 500, {
      request: requestOptions
    });
    requestError.cause = error;
    throw requestError;
  }
  const status = fetchResponse.status;
  const url = fetchResponse.url;
  const responseHeaders = {};
  for (const [key, value] of fetchResponse.headers) {
    responseHeaders[key] = value;
  }
  const octokitResponse = {
    url,
    status,
    headers: responseHeaders,
    data: ""
  };
  if ("deprecation" in responseHeaders) {
    const matches = responseHeaders.link && responseHeaders.link.match(/<([^<>]+)>; rel="deprecation"/);
    const deprecationLink = matches && matches.pop();
    log.warn(
      `[@octokit/request] "${requestOptions.method} ${requestOptions.url}" is deprecated. It is scheduled to be removed on ${responseHeaders.sunset}${deprecationLink ? `. See ${deprecationLink}` : ""}`
    );
  }
  if (status === 204 || status === 205) {
    return octokitResponse;
  }
  if (requestOptions.method === "HEAD") {
    if (status < 400) {
      return octokitResponse;
    }
    throw new RequestError(fetchResponse.statusText, status, {
      response: octokitResponse,
      request: requestOptions
    });
  }
  if (status === 304) {
    octokitResponse.data = await getResponseData(fetchResponse);
    throw new RequestError("Not modified", status, {
      response: octokitResponse,
      request: requestOptions
    });
  }
  if (status >= 400) {
    octokitResponse.data = await getResponseData(fetchResponse);
    throw new RequestError(toErrorMessage(octokitResponse.data), status, {
      response: octokitResponse,
      request: requestOptions
    });
  }
  octokitResponse.data = parseSuccessResponseBody ? await getResponseData(fetchResponse) : fetchResponse.body;
  return octokitResponse;
}
async function getResponseData(response) {
  const contentType = response.headers.get("content-type");
  if (!contentType) {
    return response.text().catch(noop);
  }
  const mimetype = (0,fast_content_type_parse/* safeParse */.xL)(contentType);
  if (isJSONResponse(mimetype)) {
    let text = "";
    try {
      text = await response.text();
      return JSONParse(text);
    } catch (err) {
      return text;
    }
  } else if (mimetype.type.startsWith("text/") || mimetype.parameters.charset?.toLowerCase() === "utf-8") {
    return response.text().catch(noop);
  } else {
    return response.arrayBuffer().catch(
      /* v8 ignore next -- @preserve */
      () => new ArrayBuffer(0)
    );
  }
}
function isJSONResponse(mimetype) {
  return mimetype.type === "application/json" || mimetype.type === "application/scim+json";
}
function toErrorMessage(data) {
  if (typeof data === "string") {
    return data;
  }
  if (data instanceof ArrayBuffer) {
    return "Unknown error";
  }
  if ("message" in data) {
    const suffix = "documentation_url" in data ? ` - ${data.documentation_url}` : "";
    return Array.isArray(data.errors) ? `${data.message}: ${data.errors.map((v) => JSON.stringify(v)).join(", ")}${suffix}` : `${data.message}${suffix}`;
  }
  return `Unknown error: ${JSON.stringify(data)}`;
}

// pkg/dist-src/with-defaults.js
function dist_bundle_withDefaults(oldEndpoint, newDefaults) {
  const endpoint2 = oldEndpoint.defaults(newDefaults);
  const newApi = function(route, parameters) {
    const endpointOptions = endpoint2.merge(route, parameters);
    if (!endpointOptions.request || !endpointOptions.request.hook) {
      return fetchWrapper(endpoint2.parse(endpointOptions));
    }
    const request2 = (route2, parameters2) => {
      return fetchWrapper(
        endpoint2.parse(endpoint2.merge(route2, parameters2))
      );
    };
    Object.assign(request2, {
      endpoint: endpoint2,
      defaults: dist_bundle_withDefaults.bind(null, endpoint2)
    });
    return endpointOptions.request.hook(request2, endpointOptions);
  };
  return Object.assign(newApi, {
    endpoint: endpoint2,
    defaults: dist_bundle_withDefaults.bind(null, endpoint2)
  });
}

// pkg/dist-src/index.js
var request = dist_bundle_withDefaults(endpoint, defaults_default);

/* v8 ignore next -- @preserve */
/* v8 ignore else -- @preserve */

;// CONCATENATED MODULE: ./node_modules/@octokit/graphql/dist-bundle/index.js
// pkg/dist-src/index.js



// pkg/dist-src/version.js
var graphql_dist_bundle_VERSION = "0.0.0-development";

// pkg/dist-src/with-defaults.js


// pkg/dist-src/graphql.js


// pkg/dist-src/error.js
function _buildMessageForResponseErrors(data) {
  return `Request failed due to following response errors:
` + data.errors.map((e) => ` - ${e.message}`).join("\n");
}
var GraphqlResponseError = class extends Error {
  constructor(request2, headers, response) {
    super(_buildMessageForResponseErrors(response));
    this.request = request2;
    this.headers = headers;
    this.response = response;
    this.errors = response.errors;
    this.data = response.data;
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
  name = "GraphqlResponseError";
  errors;
  data;
};

// pkg/dist-src/graphql.js
var NON_VARIABLE_OPTIONS = [
  "method",
  "baseUrl",
  "url",
  "headers",
  "request",
  "query",
  "mediaType",
  "operationName"
];
var FORBIDDEN_VARIABLE_OPTIONS = ["query", "method", "url"];
var GHES_V3_SUFFIX_REGEX = /\/api\/v3\/?$/;
function graphql(request2, query, options) {
  if (options) {
    if (typeof query === "string" && "query" in options) {
      return Promise.reject(
        new Error(`[@octokit/graphql] "query" cannot be used as variable name`)
      );
    }
    for (const key in options) {
      if (!FORBIDDEN_VARIABLE_OPTIONS.includes(key)) continue;
      return Promise.reject(
        new Error(
          `[@octokit/graphql] "${key}" cannot be used as variable name`
        )
      );
    }
  }
  const parsedOptions = typeof query === "string" ? Object.assign({ query }, options) : query;
  const requestOptions = Object.keys(
    parsedOptions
  ).reduce((result, key) => {
    if (NON_VARIABLE_OPTIONS.includes(key)) {
      result[key] = parsedOptions[key];
      return result;
    }
    if (!result.variables) {
      result.variables = {};
    }
    result.variables[key] = parsedOptions[key];
    return result;
  }, {});
  const baseUrl = parsedOptions.baseUrl || request2.endpoint.DEFAULTS.baseUrl;
  if (GHES_V3_SUFFIX_REGEX.test(baseUrl)) {
    requestOptions.url = baseUrl.replace(GHES_V3_SUFFIX_REGEX, "/api/graphql");
  }
  return request2(requestOptions).then((response) => {
    if (response.data.errors) {
      const headers = {};
      for (const key of Object.keys(response.headers)) {
        headers[key] = response.headers[key];
      }
      throw new GraphqlResponseError(
        requestOptions,
        headers,
        response.data
      );
    }
    return response.data.data;
  });
}

// pkg/dist-src/with-defaults.js
function graphql_dist_bundle_withDefaults(request2, newDefaults) {
  const newRequest = request2.defaults(newDefaults);
  const newApi = (query, options) => {
    return graphql(newRequest, query, options);
  };
  return Object.assign(newApi, {
    defaults: graphql_dist_bundle_withDefaults.bind(null, newRequest),
    endpoint: newRequest.endpoint
  });
}

// pkg/dist-src/index.js
var graphql2 = graphql_dist_bundle_withDefaults(request, {
  headers: {
    "user-agent": `octokit-graphql.js/${graphql_dist_bundle_VERSION} ${getUserAgent()}`
  },
  method: "POST",
  url: "/graphql"
});
function withCustomRequest(customRequest) {
  return graphql_dist_bundle_withDefaults(customRequest, {
    method: "POST",
    url: "/graphql"
  });
}


;// CONCATENATED MODULE: ./node_modules/@octokit/auth-token/dist-bundle/index.js
// pkg/dist-src/is-jwt.js
var b64url = "(?:[a-zA-Z0-9_-]+)";
var sep = "\\.";
var jwtRE = new RegExp(`^${b64url}${sep}${b64url}${sep}${b64url}$`);
var isJWT = jwtRE.test.bind(jwtRE);

// pkg/dist-src/auth.js
async function auth(token) {
  const isApp = isJWT(token);
  const isInstallation = token.startsWith("v1.") || token.startsWith("ghs_");
  const isUserToServer = token.startsWith("ghu_");
  const tokenType = isApp ? "app" : isInstallation ? "installation" : isUserToServer ? "user-to-server" : "oauth";
  return {
    type: "token",
    token,
    tokenType
  };
}

// pkg/dist-src/with-authorization-prefix.js
function withAuthorizationPrefix(token) {
  if (token.split(/\./).length === 3) {
    return `bearer ${token}`;
  }
  return `token ${token}`;
}

// pkg/dist-src/hook.js
async function hook(token, request, route, parameters) {
  const endpoint = request.endpoint.merge(
    route,
    parameters
  );
  endpoint.headers.authorization = withAuthorizationPrefix(token);
  return request(endpoint);
}

// pkg/dist-src/index.js
var createTokenAuth = function createTokenAuth2(token) {
  if (!token) {
    throw new Error("[@octokit/auth-token] No token passed to createTokenAuth");
  }
  if (typeof token !== "string") {
    throw new Error(
      "[@octokit/auth-token] Token passed to createTokenAuth is not a string"
    );
  }
  token = token.replace(/^(token|bearer) +/i, "");
  return Object.assign(auth.bind(null, token), {
    hook: hook.bind(null, token)
  });
};


;// CONCATENATED MODULE: ./node_modules/@octokit/core/dist-src/version.js
const version_VERSION = "7.0.6";


;// CONCATENATED MODULE: ./node_modules/@octokit/core/dist-src/index.js






const dist_src_noop = () => {
};
const consoleWarn = console.warn.bind(console);
const consoleError = console.error.bind(console);
function createLogger(logger = {}) {
  if (typeof logger.debug !== "function") {
    logger.debug = dist_src_noop;
  }
  if (typeof logger.info !== "function") {
    logger.info = dist_src_noop;
  }
  if (typeof logger.warn !== "function") {
    logger.warn = consoleWarn;
  }
  if (typeof logger.error !== "function") {
    logger.error = consoleError;
  }
  return logger;
}
const userAgentTrail = `octokit-core.js/${version_VERSION} ${getUserAgent()}`;
class Octokit {
  static VERSION = version_VERSION;
  static defaults(defaults) {
    const OctokitWithDefaults = class extends this {
      constructor(...args) {
        const options = args[0] || {};
        if (typeof defaults === "function") {
          super(defaults(options));
          return;
        }
        super(
          Object.assign(
            {},
            defaults,
            options,
            options.userAgent && defaults.userAgent ? {
              userAgent: `${options.userAgent} ${defaults.userAgent}`
            } : null
          )
        );
      }
    };
    return OctokitWithDefaults;
  }
  static plugins = [];
  /**
   * Attach a plugin (or many) to your Octokit instance.
   *
   * @example
   * const API = Octokit.plugin(plugin1, plugin2, plugin3, ...)
   */
  static plugin(...newPlugins) {
    const currentPlugins = this.plugins;
    const NewOctokit = class extends this {
      static plugins = currentPlugins.concat(
        newPlugins.filter((plugin) => !currentPlugins.includes(plugin))
      );
    };
    return NewOctokit;
  }
  constructor(options = {}) {
    const hook = new before_after_hook.Collection();
    const requestDefaults = {
      baseUrl: request.endpoint.DEFAULTS.baseUrl,
      headers: {},
      request: Object.assign({}, options.request, {
        // @ts-ignore internal usage only, no need to type
        hook: hook.bind(null, "request")
      }),
      mediaType: {
        previews: [],
        format: ""
      }
    };
    requestDefaults.headers["user-agent"] = options.userAgent ? `${options.userAgent} ${userAgentTrail}` : userAgentTrail;
    if (options.baseUrl) {
      requestDefaults.baseUrl = options.baseUrl;
    }
    if (options.previews) {
      requestDefaults.mediaType.previews = options.previews;
    }
    if (options.timeZone) {
      requestDefaults.headers["time-zone"] = options.timeZone;
    }
    this.request = request.defaults(requestDefaults);
    this.graphql = withCustomRequest(this.request).defaults(requestDefaults);
    this.log = createLogger(options.log);
    this.hook = hook;
    if (!options.authStrategy) {
      if (!options.auth) {
        this.auth = async () => ({
          type: "unauthenticated"
        });
      } else {
        const auth = createTokenAuth(options.auth);
        hook.wrap("request", auth.hook);
        this.auth = auth;
      }
    } else {
      const { authStrategy, ...otherOptions } = options;
      const auth = authStrategy(
        Object.assign(
          {
            request: this.request,
            log: this.log,
            // we pass the current octokit instance as well as its constructor options
            // to allow for authentication strategies that return a new octokit instance
            // that shares the same internal state as the current one. The original
            // requirement for this was the "event-octokit" authentication strategy
            // of https://github.com/probot/octokit-auth-probot.
            octokit: this,
            octokitOptions: otherOptions
          },
          options.auth
        )
      );
      hook.wrap("request", auth.hook);
      this.auth = auth;
    }
    const classConstructor = this.constructor;
    for (let i = 0; i < classConstructor.plugins.length; ++i) {
      Object.assign(this, classConstructor.plugins[i](this, options));
    }
  }
  // assigned during constructor
  request;
  graphql;
  log;
  hook;
  // TODO: type `octokit.auth` based on passed options.authStrategy
  auth;
}


;// CONCATENATED MODULE: ./node_modules/@octokit/plugin-rest-endpoint-methods/dist-src/version.js
const dist_src_version_VERSION = "17.0.0";

//# sourceMappingURL=version.js.map

;// CONCATENATED MODULE: ./node_modules/@octokit/plugin-rest-endpoint-methods/dist-src/generated/endpoints.js
const Endpoints = {
  actions: {
    addCustomLabelsToSelfHostedRunnerForOrg: [
      "POST /orgs/{org}/actions/runners/{runner_id}/labels"
    ],
    addCustomLabelsToSelfHostedRunnerForRepo: [
      "POST /repos/{owner}/{repo}/actions/runners/{runner_id}/labels"
    ],
    addRepoAccessToSelfHostedRunnerGroupInOrg: [
      "PUT /orgs/{org}/actions/runner-groups/{runner_group_id}/repositories/{repository_id}"
    ],
    addSelectedRepoToOrgSecret: [
      "PUT /orgs/{org}/actions/secrets/{secret_name}/repositories/{repository_id}"
    ],
    addSelectedRepoToOrgVariable: [
      "PUT /orgs/{org}/actions/variables/{name}/repositories/{repository_id}"
    ],
    approveWorkflowRun: [
      "POST /repos/{owner}/{repo}/actions/runs/{run_id}/approve"
    ],
    cancelWorkflowRun: [
      "POST /repos/{owner}/{repo}/actions/runs/{run_id}/cancel"
    ],
    createEnvironmentVariable: [
      "POST /repos/{owner}/{repo}/environments/{environment_name}/variables"
    ],
    createHostedRunnerForOrg: ["POST /orgs/{org}/actions/hosted-runners"],
    createOrUpdateEnvironmentSecret: [
      "PUT /repos/{owner}/{repo}/environments/{environment_name}/secrets/{secret_name}"
    ],
    createOrUpdateOrgSecret: ["PUT /orgs/{org}/actions/secrets/{secret_name}"],
    createOrUpdateRepoSecret: [
      "PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}"
    ],
    createOrgVariable: ["POST /orgs/{org}/actions/variables"],
    createRegistrationTokenForOrg: [
      "POST /orgs/{org}/actions/runners/registration-token"
    ],
    createRegistrationTokenForRepo: [
      "POST /repos/{owner}/{repo}/actions/runners/registration-token"
    ],
    createRemoveTokenForOrg: ["POST /orgs/{org}/actions/runners/remove-token"],
    createRemoveTokenForRepo: [
      "POST /repos/{owner}/{repo}/actions/runners/remove-token"
    ],
    createRepoVariable: ["POST /repos/{owner}/{repo}/actions/variables"],
    createWorkflowDispatch: [
      "POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
    ],
    deleteActionsCacheById: [
      "DELETE /repos/{owner}/{repo}/actions/caches/{cache_id}"
    ],
    deleteActionsCacheByKey: [
      "DELETE /repos/{owner}/{repo}/actions/caches{?key,ref}"
    ],
    deleteArtifact: [
      "DELETE /repos/{owner}/{repo}/actions/artifacts/{artifact_id}"
    ],
    deleteCustomImageFromOrg: [
      "DELETE /orgs/{org}/actions/hosted-runners/images/custom/{image_definition_id}"
    ],
    deleteCustomImageVersionFromOrg: [
      "DELETE /orgs/{org}/actions/hosted-runners/images/custom/{image_definition_id}/versions/{version}"
    ],
    deleteEnvironmentSecret: [
      "DELETE /repos/{owner}/{repo}/environments/{environment_name}/secrets/{secret_name}"
    ],
    deleteEnvironmentVariable: [
      "DELETE /repos/{owner}/{repo}/environments/{environment_name}/variables/{name}"
    ],
    deleteHostedRunnerForOrg: [
      "DELETE /orgs/{org}/actions/hosted-runners/{hosted_runner_id}"
    ],
    deleteOrgSecret: ["DELETE /orgs/{org}/actions/secrets/{secret_name}"],
    deleteOrgVariable: ["DELETE /orgs/{org}/actions/variables/{name}"],
    deleteRepoSecret: [
      "DELETE /repos/{owner}/{repo}/actions/secrets/{secret_name}"
    ],
    deleteRepoVariable: [
      "DELETE /repos/{owner}/{repo}/actions/variables/{name}"
    ],
    deleteSelfHostedRunnerFromOrg: [
      "DELETE /orgs/{org}/actions/runners/{runner_id}"
    ],
    deleteSelfHostedRunnerFromRepo: [
      "DELETE /repos/{owner}/{repo}/actions/runners/{runner_id}"
    ],
    deleteWorkflowRun: ["DELETE /repos/{owner}/{repo}/actions/runs/{run_id}"],
    deleteWorkflowRunLogs: [
      "DELETE /repos/{owner}/{repo}/actions/runs/{run_id}/logs"
    ],
    disableSelectedRepositoryGithubActionsOrganization: [
      "DELETE /orgs/{org}/actions/permissions/repositories/{repository_id}"
    ],
    disableWorkflow: [
      "PUT /repos/{owner}/{repo}/actions/workflows/{workflow_id}/disable"
    ],
    downloadArtifact: [
      "GET /repos/{owner}/{repo}/actions/artifacts/{artifact_id}/{archive_format}"
    ],
    downloadJobLogsForWorkflowRun: [
      "GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
    ],
    downloadWorkflowRunAttemptLogs: [
      "GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}/logs"
    ],
    downloadWorkflowRunLogs: [
      "GET /repos/{owner}/{repo}/actions/runs/{run_id}/logs"
    ],
    enableSelectedRepositoryGithubActionsOrganization: [
      "PUT /orgs/{org}/actions/permissions/repositories/{repository_id}"
    ],
    enableWorkflow: [
      "PUT /repos/{owner}/{repo}/actions/workflows/{workflow_id}/enable"
    ],
    forceCancelWorkflowRun: [
      "POST /repos/{owner}/{repo}/actions/runs/{run_id}/force-cancel"
    ],
    generateRunnerJitconfigForOrg: [
      "POST /orgs/{org}/actions/runners/generate-jitconfig"
    ],
    generateRunnerJitconfigForRepo: [
      "POST /repos/{owner}/{repo}/actions/runners/generate-jitconfig"
    ],
    getActionsCacheList: ["GET /repos/{owner}/{repo}/actions/caches"],
    getActionsCacheUsage: ["GET /repos/{owner}/{repo}/actions/cache/usage"],
    getActionsCacheUsageByRepoForOrg: [
      "GET /orgs/{org}/actions/cache/usage-by-repository"
    ],
    getActionsCacheUsageForOrg: ["GET /orgs/{org}/actions/cache/usage"],
    getAllowedActionsOrganization: [
      "GET /orgs/{org}/actions/permissions/selected-actions"
    ],
    getAllowedActionsRepository: [
      "GET /repos/{owner}/{repo}/actions/permissions/selected-actions"
    ],
    getArtifact: ["GET /repos/{owner}/{repo}/actions/artifacts/{artifact_id}"],
    getCustomImageForOrg: [
      "GET /orgs/{org}/actions/hosted-runners/images/custom/{image_definition_id}"
    ],
    getCustomImageVersionForOrg: [
      "GET /orgs/{org}/actions/hosted-runners/images/custom/{image_definition_id}/versions/{version}"
    ],
    getCustomOidcSubClaimForRepo: [
      "GET /repos/{owner}/{repo}/actions/oidc/customization/sub"
    ],
    getEnvironmentPublicKey: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}/secrets/public-key"
    ],
    getEnvironmentSecret: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}/secrets/{secret_name}"
    ],
    getEnvironmentVariable: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}/variables/{name}"
    ],
    getGithubActionsDefaultWorkflowPermissionsOrganization: [
      "GET /orgs/{org}/actions/permissions/workflow"
    ],
    getGithubActionsDefaultWorkflowPermissionsRepository: [
      "GET /repos/{owner}/{repo}/actions/permissions/workflow"
    ],
    getGithubActionsPermissionsOrganization: [
      "GET /orgs/{org}/actions/permissions"
    ],
    getGithubActionsPermissionsRepository: [
      "GET /repos/{owner}/{repo}/actions/permissions"
    ],
    getHostedRunnerForOrg: [
      "GET /orgs/{org}/actions/hosted-runners/{hosted_runner_id}"
    ],
    getHostedRunnersGithubOwnedImagesForOrg: [
      "GET /orgs/{org}/actions/hosted-runners/images/github-owned"
    ],
    getHostedRunnersLimitsForOrg: [
      "GET /orgs/{org}/actions/hosted-runners/limits"
    ],
    getHostedRunnersMachineSpecsForOrg: [
      "GET /orgs/{org}/actions/hosted-runners/machine-sizes"
    ],
    getHostedRunnersPartnerImagesForOrg: [
      "GET /orgs/{org}/actions/hosted-runners/images/partner"
    ],
    getHostedRunnersPlatformsForOrg: [
      "GET /orgs/{org}/actions/hosted-runners/platforms"
    ],
    getJobForWorkflowRun: ["GET /repos/{owner}/{repo}/actions/jobs/{job_id}"],
    getOrgPublicKey: ["GET /orgs/{org}/actions/secrets/public-key"],
    getOrgSecret: ["GET /orgs/{org}/actions/secrets/{secret_name}"],
    getOrgVariable: ["GET /orgs/{org}/actions/variables/{name}"],
    getPendingDeploymentsForRun: [
      "GET /repos/{owner}/{repo}/actions/runs/{run_id}/pending_deployments"
    ],
    getRepoPermissions: [
      "GET /repos/{owner}/{repo}/actions/permissions",
      {},
      { renamed: ["actions", "getGithubActionsPermissionsRepository"] }
    ],
    getRepoPublicKey: ["GET /repos/{owner}/{repo}/actions/secrets/public-key"],
    getRepoSecret: ["GET /repos/{owner}/{repo}/actions/secrets/{secret_name}"],
    getRepoVariable: ["GET /repos/{owner}/{repo}/actions/variables/{name}"],
    getReviewsForRun: [
      "GET /repos/{owner}/{repo}/actions/runs/{run_id}/approvals"
    ],
    getSelfHostedRunnerForOrg: ["GET /orgs/{org}/actions/runners/{runner_id}"],
    getSelfHostedRunnerForRepo: [
      "GET /repos/{owner}/{repo}/actions/runners/{runner_id}"
    ],
    getWorkflow: ["GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}"],
    getWorkflowAccessToRepository: [
      "GET /repos/{owner}/{repo}/actions/permissions/access"
    ],
    getWorkflowRun: ["GET /repos/{owner}/{repo}/actions/runs/{run_id}"],
    getWorkflowRunAttempt: [
      "GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}"
    ],
    getWorkflowRunUsage: [
      "GET /repos/{owner}/{repo}/actions/runs/{run_id}/timing"
    ],
    getWorkflowUsage: [
      "GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}/timing"
    ],
    listArtifactsForRepo: ["GET /repos/{owner}/{repo}/actions/artifacts"],
    listCustomImageVersionsForOrg: [
      "GET /orgs/{org}/actions/hosted-runners/images/custom/{image_definition_id}/versions"
    ],
    listCustomImagesForOrg: [
      "GET /orgs/{org}/actions/hosted-runners/images/custom"
    ],
    listEnvironmentSecrets: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}/secrets"
    ],
    listEnvironmentVariables: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}/variables"
    ],
    listGithubHostedRunnersInGroupForOrg: [
      "GET /orgs/{org}/actions/runner-groups/{runner_group_id}/hosted-runners"
    ],
    listHostedRunnersForOrg: ["GET /orgs/{org}/actions/hosted-runners"],
    listJobsForWorkflowRun: [
      "GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    ],
    listJobsForWorkflowRunAttempt: [
      "GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}/jobs"
    ],
    listLabelsForSelfHostedRunnerForOrg: [
      "GET /orgs/{org}/actions/runners/{runner_id}/labels"
    ],
    listLabelsForSelfHostedRunnerForRepo: [
      "GET /repos/{owner}/{repo}/actions/runners/{runner_id}/labels"
    ],
    listOrgSecrets: ["GET /orgs/{org}/actions/secrets"],
    listOrgVariables: ["GET /orgs/{org}/actions/variables"],
    listRepoOrganizationSecrets: [
      "GET /repos/{owner}/{repo}/actions/organization-secrets"
    ],
    listRepoOrganizationVariables: [
      "GET /repos/{owner}/{repo}/actions/organization-variables"
    ],
    listRepoSecrets: ["GET /repos/{owner}/{repo}/actions/secrets"],
    listRepoVariables: ["GET /repos/{owner}/{repo}/actions/variables"],
    listRepoWorkflows: ["GET /repos/{owner}/{repo}/actions/workflows"],
    listRunnerApplicationsForOrg: ["GET /orgs/{org}/actions/runners/downloads"],
    listRunnerApplicationsForRepo: [
      "GET /repos/{owner}/{repo}/actions/runners/downloads"
    ],
    listSelectedReposForOrgSecret: [
      "GET /orgs/{org}/actions/secrets/{secret_name}/repositories"
    ],
    listSelectedReposForOrgVariable: [
      "GET /orgs/{org}/actions/variables/{name}/repositories"
    ],
    listSelectedRepositoriesEnabledGithubActionsOrganization: [
      "GET /orgs/{org}/actions/permissions/repositories"
    ],
    listSelfHostedRunnersForOrg: ["GET /orgs/{org}/actions/runners"],
    listSelfHostedRunnersForRepo: ["GET /repos/{owner}/{repo}/actions/runners"],
    listWorkflowRunArtifacts: [
      "GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
    ],
    listWorkflowRuns: [
      "GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
    ],
    listWorkflowRunsForRepo: ["GET /repos/{owner}/{repo}/actions/runs"],
    reRunJobForWorkflowRun: [
      "POST /repos/{owner}/{repo}/actions/jobs/{job_id}/rerun"
    ],
    reRunWorkflow: ["POST /repos/{owner}/{repo}/actions/runs/{run_id}/rerun"],
    reRunWorkflowFailedJobs: [
      "POST /repos/{owner}/{repo}/actions/runs/{run_id}/rerun-failed-jobs"
    ],
    removeAllCustomLabelsFromSelfHostedRunnerForOrg: [
      "DELETE /orgs/{org}/actions/runners/{runner_id}/labels"
    ],
    removeAllCustomLabelsFromSelfHostedRunnerForRepo: [
      "DELETE /repos/{owner}/{repo}/actions/runners/{runner_id}/labels"
    ],
    removeCustomLabelFromSelfHostedRunnerForOrg: [
      "DELETE /orgs/{org}/actions/runners/{runner_id}/labels/{name}"
    ],
    removeCustomLabelFromSelfHostedRunnerForRepo: [
      "DELETE /repos/{owner}/{repo}/actions/runners/{runner_id}/labels/{name}"
    ],
    removeSelectedRepoFromOrgSecret: [
      "DELETE /orgs/{org}/actions/secrets/{secret_name}/repositories/{repository_id}"
    ],
    removeSelectedRepoFromOrgVariable: [
      "DELETE /orgs/{org}/actions/variables/{name}/repositories/{repository_id}"
    ],
    reviewCustomGatesForRun: [
      "POST /repos/{owner}/{repo}/actions/runs/{run_id}/deployment_protection_rule"
    ],
    reviewPendingDeploymentsForRun: [
      "POST /repos/{owner}/{repo}/actions/runs/{run_id}/pending_deployments"
    ],
    setAllowedActionsOrganization: [
      "PUT /orgs/{org}/actions/permissions/selected-actions"
    ],
    setAllowedActionsRepository: [
      "PUT /repos/{owner}/{repo}/actions/permissions/selected-actions"
    ],
    setCustomLabelsForSelfHostedRunnerForOrg: [
      "PUT /orgs/{org}/actions/runners/{runner_id}/labels"
    ],
    setCustomLabelsForSelfHostedRunnerForRepo: [
      "PUT /repos/{owner}/{repo}/actions/runners/{runner_id}/labels"
    ],
    setCustomOidcSubClaimForRepo: [
      "PUT /repos/{owner}/{repo}/actions/oidc/customization/sub"
    ],
    setGithubActionsDefaultWorkflowPermissionsOrganization: [
      "PUT /orgs/{org}/actions/permissions/workflow"
    ],
    setGithubActionsDefaultWorkflowPermissionsRepository: [
      "PUT /repos/{owner}/{repo}/actions/permissions/workflow"
    ],
    setGithubActionsPermissionsOrganization: [
      "PUT /orgs/{org}/actions/permissions"
    ],
    setGithubActionsPermissionsRepository: [
      "PUT /repos/{owner}/{repo}/actions/permissions"
    ],
    setSelectedReposForOrgSecret: [
      "PUT /orgs/{org}/actions/secrets/{secret_name}/repositories"
    ],
    setSelectedReposForOrgVariable: [
      "PUT /orgs/{org}/actions/variables/{name}/repositories"
    ],
    setSelectedRepositoriesEnabledGithubActionsOrganization: [
      "PUT /orgs/{org}/actions/permissions/repositories"
    ],
    setWorkflowAccessToRepository: [
      "PUT /repos/{owner}/{repo}/actions/permissions/access"
    ],
    updateEnvironmentVariable: [
      "PATCH /repos/{owner}/{repo}/environments/{environment_name}/variables/{name}"
    ],
    updateHostedRunnerForOrg: [
      "PATCH /orgs/{org}/actions/hosted-runners/{hosted_runner_id}"
    ],
    updateOrgVariable: ["PATCH /orgs/{org}/actions/variables/{name}"],
    updateRepoVariable: [
      "PATCH /repos/{owner}/{repo}/actions/variables/{name}"
    ]
  },
  activity: {
    checkRepoIsStarredByAuthenticatedUser: ["GET /user/starred/{owner}/{repo}"],
    deleteRepoSubscription: ["DELETE /repos/{owner}/{repo}/subscription"],
    deleteThreadSubscription: [
      "DELETE /notifications/threads/{thread_id}/subscription"
    ],
    getFeeds: ["GET /feeds"],
    getRepoSubscription: ["GET /repos/{owner}/{repo}/subscription"],
    getThread: ["GET /notifications/threads/{thread_id}"],
    getThreadSubscriptionForAuthenticatedUser: [
      "GET /notifications/threads/{thread_id}/subscription"
    ],
    listEventsForAuthenticatedUser: ["GET /users/{username}/events"],
    listNotificationsForAuthenticatedUser: ["GET /notifications"],
    listOrgEventsForAuthenticatedUser: [
      "GET /users/{username}/events/orgs/{org}"
    ],
    listPublicEvents: ["GET /events"],
    listPublicEventsForRepoNetwork: ["GET /networks/{owner}/{repo}/events"],
    listPublicEventsForUser: ["GET /users/{username}/events/public"],
    listPublicOrgEvents: ["GET /orgs/{org}/events"],
    listReceivedEventsForUser: ["GET /users/{username}/received_events"],
    listReceivedPublicEventsForUser: [
      "GET /users/{username}/received_events/public"
    ],
    listRepoEvents: ["GET /repos/{owner}/{repo}/events"],
    listRepoNotificationsForAuthenticatedUser: [
      "GET /repos/{owner}/{repo}/notifications"
    ],
    listReposStarredByAuthenticatedUser: ["GET /user/starred"],
    listReposStarredByUser: ["GET /users/{username}/starred"],
    listReposWatchedByUser: ["GET /users/{username}/subscriptions"],
    listStargazersForRepo: ["GET /repos/{owner}/{repo}/stargazers"],
    listWatchedReposForAuthenticatedUser: ["GET /user/subscriptions"],
    listWatchersForRepo: ["GET /repos/{owner}/{repo}/subscribers"],
    markNotificationsAsRead: ["PUT /notifications"],
    markRepoNotificationsAsRead: ["PUT /repos/{owner}/{repo}/notifications"],
    markThreadAsDone: ["DELETE /notifications/threads/{thread_id}"],
    markThreadAsRead: ["PATCH /notifications/threads/{thread_id}"],
    setRepoSubscription: ["PUT /repos/{owner}/{repo}/subscription"],
    setThreadSubscription: [
      "PUT /notifications/threads/{thread_id}/subscription"
    ],
    starRepoForAuthenticatedUser: ["PUT /user/starred/{owner}/{repo}"],
    unstarRepoForAuthenticatedUser: ["DELETE /user/starred/{owner}/{repo}"]
  },
  apps: {
    addRepoToInstallation: [
      "PUT /user/installations/{installation_id}/repositories/{repository_id}",
      {},
      { renamed: ["apps", "addRepoToInstallationForAuthenticatedUser"] }
    ],
    addRepoToInstallationForAuthenticatedUser: [
      "PUT /user/installations/{installation_id}/repositories/{repository_id}"
    ],
    checkToken: ["POST /applications/{client_id}/token"],
    createFromManifest: ["POST /app-manifests/{code}/conversions"],
    createInstallationAccessToken: [
      "POST /app/installations/{installation_id}/access_tokens"
    ],
    deleteAuthorization: ["DELETE /applications/{client_id}/grant"],
    deleteInstallation: ["DELETE /app/installations/{installation_id}"],
    deleteToken: ["DELETE /applications/{client_id}/token"],
    getAuthenticated: ["GET /app"],
    getBySlug: ["GET /apps/{app_slug}"],
    getInstallation: ["GET /app/installations/{installation_id}"],
    getOrgInstallation: ["GET /orgs/{org}/installation"],
    getRepoInstallation: ["GET /repos/{owner}/{repo}/installation"],
    getSubscriptionPlanForAccount: [
      "GET /marketplace_listing/accounts/{account_id}"
    ],
    getSubscriptionPlanForAccountStubbed: [
      "GET /marketplace_listing/stubbed/accounts/{account_id}"
    ],
    getUserInstallation: ["GET /users/{username}/installation"],
    getWebhookConfigForApp: ["GET /app/hook/config"],
    getWebhookDelivery: ["GET /app/hook/deliveries/{delivery_id}"],
    listAccountsForPlan: ["GET /marketplace_listing/plans/{plan_id}/accounts"],
    listAccountsForPlanStubbed: [
      "GET /marketplace_listing/stubbed/plans/{plan_id}/accounts"
    ],
    listInstallationReposForAuthenticatedUser: [
      "GET /user/installations/{installation_id}/repositories"
    ],
    listInstallationRequestsForAuthenticatedApp: [
      "GET /app/installation-requests"
    ],
    listInstallations: ["GET /app/installations"],
    listInstallationsForAuthenticatedUser: ["GET /user/installations"],
    listPlans: ["GET /marketplace_listing/plans"],
    listPlansStubbed: ["GET /marketplace_listing/stubbed/plans"],
    listReposAccessibleToInstallation: ["GET /installation/repositories"],
    listSubscriptionsForAuthenticatedUser: ["GET /user/marketplace_purchases"],
    listSubscriptionsForAuthenticatedUserStubbed: [
      "GET /user/marketplace_purchases/stubbed"
    ],
    listWebhookDeliveries: ["GET /app/hook/deliveries"],
    redeliverWebhookDelivery: [
      "POST /app/hook/deliveries/{delivery_id}/attempts"
    ],
    removeRepoFromInstallation: [
      "DELETE /user/installations/{installation_id}/repositories/{repository_id}",
      {},
      { renamed: ["apps", "removeRepoFromInstallationForAuthenticatedUser"] }
    ],
    removeRepoFromInstallationForAuthenticatedUser: [
      "DELETE /user/installations/{installation_id}/repositories/{repository_id}"
    ],
    resetToken: ["PATCH /applications/{client_id}/token"],
    revokeInstallationAccessToken: ["DELETE /installation/token"],
    scopeToken: ["POST /applications/{client_id}/token/scoped"],
    suspendInstallation: ["PUT /app/installations/{installation_id}/suspended"],
    unsuspendInstallation: [
      "DELETE /app/installations/{installation_id}/suspended"
    ],
    updateWebhookConfigForApp: ["PATCH /app/hook/config"]
  },
  billing: {
    getGithubActionsBillingOrg: ["GET /orgs/{org}/settings/billing/actions"],
    getGithubActionsBillingUser: [
      "GET /users/{username}/settings/billing/actions"
    ],
    getGithubBillingPremiumRequestUsageReportOrg: [
      "GET /organizations/{org}/settings/billing/premium_request/usage"
    ],
    getGithubBillingPremiumRequestUsageReportUser: [
      "GET /users/{username}/settings/billing/premium_request/usage"
    ],
    getGithubBillingUsageReportOrg: [
      "GET /organizations/{org}/settings/billing/usage"
    ],
    getGithubBillingUsageReportUser: [
      "GET /users/{username}/settings/billing/usage"
    ],
    getGithubPackagesBillingOrg: ["GET /orgs/{org}/settings/billing/packages"],
    getGithubPackagesBillingUser: [
      "GET /users/{username}/settings/billing/packages"
    ],
    getSharedStorageBillingOrg: [
      "GET /orgs/{org}/settings/billing/shared-storage"
    ],
    getSharedStorageBillingUser: [
      "GET /users/{username}/settings/billing/shared-storage"
    ]
  },
  campaigns: {
    createCampaign: ["POST /orgs/{org}/campaigns"],
    deleteCampaign: ["DELETE /orgs/{org}/campaigns/{campaign_number}"],
    getCampaignSummary: ["GET /orgs/{org}/campaigns/{campaign_number}"],
    listOrgCampaigns: ["GET /orgs/{org}/campaigns"],
    updateCampaign: ["PATCH /orgs/{org}/campaigns/{campaign_number}"]
  },
  checks: {
    create: ["POST /repos/{owner}/{repo}/check-runs"],
    createSuite: ["POST /repos/{owner}/{repo}/check-suites"],
    get: ["GET /repos/{owner}/{repo}/check-runs/{check_run_id}"],
    getSuite: ["GET /repos/{owner}/{repo}/check-suites/{check_suite_id}"],
    listAnnotations: [
      "GET /repos/{owner}/{repo}/check-runs/{check_run_id}/annotations"
    ],
    listForRef: ["GET /repos/{owner}/{repo}/commits/{ref}/check-runs"],
    listForSuite: [
      "GET /repos/{owner}/{repo}/check-suites/{check_suite_id}/check-runs"
    ],
    listSuitesForRef: ["GET /repos/{owner}/{repo}/commits/{ref}/check-suites"],
    rerequestRun: [
      "POST /repos/{owner}/{repo}/check-runs/{check_run_id}/rerequest"
    ],
    rerequestSuite: [
      "POST /repos/{owner}/{repo}/check-suites/{check_suite_id}/rerequest"
    ],
    setSuitesPreferences: [
      "PATCH /repos/{owner}/{repo}/check-suites/preferences"
    ],
    update: ["PATCH /repos/{owner}/{repo}/check-runs/{check_run_id}"]
  },
  codeScanning: {
    commitAutofix: [
      "POST /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/autofix/commits"
    ],
    createAutofix: [
      "POST /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/autofix"
    ],
    createVariantAnalysis: [
      "POST /repos/{owner}/{repo}/code-scanning/codeql/variant-analyses"
    ],
    deleteAnalysis: [
      "DELETE /repos/{owner}/{repo}/code-scanning/analyses/{analysis_id}{?confirm_delete}"
    ],
    deleteCodeqlDatabase: [
      "DELETE /repos/{owner}/{repo}/code-scanning/codeql/databases/{language}"
    ],
    getAlert: [
      "GET /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}",
      {},
      { renamedParameters: { alert_id: "alert_number" } }
    ],
    getAnalysis: [
      "GET /repos/{owner}/{repo}/code-scanning/analyses/{analysis_id}"
    ],
    getAutofix: [
      "GET /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/autofix"
    ],
    getCodeqlDatabase: [
      "GET /repos/{owner}/{repo}/code-scanning/codeql/databases/{language}"
    ],
    getDefaultSetup: ["GET /repos/{owner}/{repo}/code-scanning/default-setup"],
    getSarif: ["GET /repos/{owner}/{repo}/code-scanning/sarifs/{sarif_id}"],
    getVariantAnalysis: [
      "GET /repos/{owner}/{repo}/code-scanning/codeql/variant-analyses/{codeql_variant_analysis_id}"
    ],
    getVariantAnalysisRepoTask: [
      "GET /repos/{owner}/{repo}/code-scanning/codeql/variant-analyses/{codeql_variant_analysis_id}/repos/{repo_owner}/{repo_name}"
    ],
    listAlertInstances: [
      "GET /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/instances"
    ],
    listAlertsForOrg: ["GET /orgs/{org}/code-scanning/alerts"],
    listAlertsForRepo: ["GET /repos/{owner}/{repo}/code-scanning/alerts"],
    listAlertsInstances: [
      "GET /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/instances",
      {},
      { renamed: ["codeScanning", "listAlertInstances"] }
    ],
    listCodeqlDatabases: [
      "GET /repos/{owner}/{repo}/code-scanning/codeql/databases"
    ],
    listRecentAnalyses: ["GET /repos/{owner}/{repo}/code-scanning/analyses"],
    updateAlert: [
      "PATCH /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}"
    ],
    updateDefaultSetup: [
      "PATCH /repos/{owner}/{repo}/code-scanning/default-setup"
    ],
    uploadSarif: ["POST /repos/{owner}/{repo}/code-scanning/sarifs"]
  },
  codeSecurity: {
    attachConfiguration: [
      "POST /orgs/{org}/code-security/configurations/{configuration_id}/attach"
    ],
    attachEnterpriseConfiguration: [
      "POST /enterprises/{enterprise}/code-security/configurations/{configuration_id}/attach"
    ],
    createConfiguration: ["POST /orgs/{org}/code-security/configurations"],
    createConfigurationForEnterprise: [
      "POST /enterprises/{enterprise}/code-security/configurations"
    ],
    deleteConfiguration: [
      "DELETE /orgs/{org}/code-security/configurations/{configuration_id}"
    ],
    deleteConfigurationForEnterprise: [
      "DELETE /enterprises/{enterprise}/code-security/configurations/{configuration_id}"
    ],
    detachConfiguration: [
      "DELETE /orgs/{org}/code-security/configurations/detach"
    ],
    getConfiguration: [
      "GET /orgs/{org}/code-security/configurations/{configuration_id}"
    ],
    getConfigurationForRepository: [
      "GET /repos/{owner}/{repo}/code-security-configuration"
    ],
    getConfigurationsForEnterprise: [
      "GET /enterprises/{enterprise}/code-security/configurations"
    ],
    getConfigurationsForOrg: ["GET /orgs/{org}/code-security/configurations"],
    getDefaultConfigurations: [
      "GET /orgs/{org}/code-security/configurations/defaults"
    ],
    getDefaultConfigurationsForEnterprise: [
      "GET /enterprises/{enterprise}/code-security/configurations/defaults"
    ],
    getRepositoriesForConfiguration: [
      "GET /orgs/{org}/code-security/configurations/{configuration_id}/repositories"
    ],
    getRepositoriesForEnterpriseConfiguration: [
      "GET /enterprises/{enterprise}/code-security/configurations/{configuration_id}/repositories"
    ],
    getSingleConfigurationForEnterprise: [
      "GET /enterprises/{enterprise}/code-security/configurations/{configuration_id}"
    ],
    setConfigurationAsDefault: [
      "PUT /orgs/{org}/code-security/configurations/{configuration_id}/defaults"
    ],
    setConfigurationAsDefaultForEnterprise: [
      "PUT /enterprises/{enterprise}/code-security/configurations/{configuration_id}/defaults"
    ],
    updateConfiguration: [
      "PATCH /orgs/{org}/code-security/configurations/{configuration_id}"
    ],
    updateEnterpriseConfiguration: [
      "PATCH /enterprises/{enterprise}/code-security/configurations/{configuration_id}"
    ]
  },
  codesOfConduct: {
    getAllCodesOfConduct: ["GET /codes_of_conduct"],
    getConductCode: ["GET /codes_of_conduct/{key}"]
  },
  codespaces: {
    addRepositoryForSecretForAuthenticatedUser: [
      "PUT /user/codespaces/secrets/{secret_name}/repositories/{repository_id}"
    ],
    addSelectedRepoToOrgSecret: [
      "PUT /orgs/{org}/codespaces/secrets/{secret_name}/repositories/{repository_id}"
    ],
    checkPermissionsForDevcontainer: [
      "GET /repos/{owner}/{repo}/codespaces/permissions_check"
    ],
    codespaceMachinesForAuthenticatedUser: [
      "GET /user/codespaces/{codespace_name}/machines"
    ],
    createForAuthenticatedUser: ["POST /user/codespaces"],
    createOrUpdateOrgSecret: [
      "PUT /orgs/{org}/codespaces/secrets/{secret_name}"
    ],
    createOrUpdateRepoSecret: [
      "PUT /repos/{owner}/{repo}/codespaces/secrets/{secret_name}"
    ],
    createOrUpdateSecretForAuthenticatedUser: [
      "PUT /user/codespaces/secrets/{secret_name}"
    ],
    createWithPrForAuthenticatedUser: [
      "POST /repos/{owner}/{repo}/pulls/{pull_number}/codespaces"
    ],
    createWithRepoForAuthenticatedUser: [
      "POST /repos/{owner}/{repo}/codespaces"
    ],
    deleteForAuthenticatedUser: ["DELETE /user/codespaces/{codespace_name}"],
    deleteFromOrganization: [
      "DELETE /orgs/{org}/members/{username}/codespaces/{codespace_name}"
    ],
    deleteOrgSecret: ["DELETE /orgs/{org}/codespaces/secrets/{secret_name}"],
    deleteRepoSecret: [
      "DELETE /repos/{owner}/{repo}/codespaces/secrets/{secret_name}"
    ],
    deleteSecretForAuthenticatedUser: [
      "DELETE /user/codespaces/secrets/{secret_name}"
    ],
    exportForAuthenticatedUser: [
      "POST /user/codespaces/{codespace_name}/exports"
    ],
    getCodespacesForUserInOrg: [
      "GET /orgs/{org}/members/{username}/codespaces"
    ],
    getExportDetailsForAuthenticatedUser: [
      "GET /user/codespaces/{codespace_name}/exports/{export_id}"
    ],
    getForAuthenticatedUser: ["GET /user/codespaces/{codespace_name}"],
    getOrgPublicKey: ["GET /orgs/{org}/codespaces/secrets/public-key"],
    getOrgSecret: ["GET /orgs/{org}/codespaces/secrets/{secret_name}"],
    getPublicKeyForAuthenticatedUser: [
      "GET /user/codespaces/secrets/public-key"
    ],
    getRepoPublicKey: [
      "GET /repos/{owner}/{repo}/codespaces/secrets/public-key"
    ],
    getRepoSecret: [
      "GET /repos/{owner}/{repo}/codespaces/secrets/{secret_name}"
    ],
    getSecretForAuthenticatedUser: [
      "GET /user/codespaces/secrets/{secret_name}"
    ],
    listDevcontainersInRepositoryForAuthenticatedUser: [
      "GET /repos/{owner}/{repo}/codespaces/devcontainers"
    ],
    listForAuthenticatedUser: ["GET /user/codespaces"],
    listInOrganization: [
      "GET /orgs/{org}/codespaces",
      {},
      { renamedParameters: { org_id: "org" } }
    ],
    listInRepositoryForAuthenticatedUser: [
      "GET /repos/{owner}/{repo}/codespaces"
    ],
    listOrgSecrets: ["GET /orgs/{org}/codespaces/secrets"],
    listRepoSecrets: ["GET /repos/{owner}/{repo}/codespaces/secrets"],
    listRepositoriesForSecretForAuthenticatedUser: [
      "GET /user/codespaces/secrets/{secret_name}/repositories"
    ],
    listSecretsForAuthenticatedUser: ["GET /user/codespaces/secrets"],
    listSelectedReposForOrgSecret: [
      "GET /orgs/{org}/codespaces/secrets/{secret_name}/repositories"
    ],
    preFlightWithRepoForAuthenticatedUser: [
      "GET /repos/{owner}/{repo}/codespaces/new"
    ],
    publishForAuthenticatedUser: [
      "POST /user/codespaces/{codespace_name}/publish"
    ],
    removeRepositoryForSecretForAuthenticatedUser: [
      "DELETE /user/codespaces/secrets/{secret_name}/repositories/{repository_id}"
    ],
    removeSelectedRepoFromOrgSecret: [
      "DELETE /orgs/{org}/codespaces/secrets/{secret_name}/repositories/{repository_id}"
    ],
    repoMachinesForAuthenticatedUser: [
      "GET /repos/{owner}/{repo}/codespaces/machines"
    ],
    setRepositoriesForSecretForAuthenticatedUser: [
      "PUT /user/codespaces/secrets/{secret_name}/repositories"
    ],
    setSelectedReposForOrgSecret: [
      "PUT /orgs/{org}/codespaces/secrets/{secret_name}/repositories"
    ],
    startForAuthenticatedUser: ["POST /user/codespaces/{codespace_name}/start"],
    stopForAuthenticatedUser: ["POST /user/codespaces/{codespace_name}/stop"],
    stopInOrganization: [
      "POST /orgs/{org}/members/{username}/codespaces/{codespace_name}/stop"
    ],
    updateForAuthenticatedUser: ["PATCH /user/codespaces/{codespace_name}"]
  },
  copilot: {
    addCopilotSeatsForTeams: [
      "POST /orgs/{org}/copilot/billing/selected_teams"
    ],
    addCopilotSeatsForUsers: [
      "POST /orgs/{org}/copilot/billing/selected_users"
    ],
    cancelCopilotSeatAssignmentForTeams: [
      "DELETE /orgs/{org}/copilot/billing/selected_teams"
    ],
    cancelCopilotSeatAssignmentForUsers: [
      "DELETE /orgs/{org}/copilot/billing/selected_users"
    ],
    copilotMetricsForOrganization: ["GET /orgs/{org}/copilot/metrics"],
    copilotMetricsForTeam: ["GET /orgs/{org}/team/{team_slug}/copilot/metrics"],
    getCopilotOrganizationDetails: ["GET /orgs/{org}/copilot/billing"],
    getCopilotSeatDetailsForUser: [
      "GET /orgs/{org}/members/{username}/copilot"
    ],
    listCopilotSeats: ["GET /orgs/{org}/copilot/billing/seats"]
  },
  credentials: { revoke: ["POST /credentials/revoke"] },
  dependabot: {
    addSelectedRepoToOrgSecret: [
      "PUT /orgs/{org}/dependabot/secrets/{secret_name}/repositories/{repository_id}"
    ],
    createOrUpdateOrgSecret: [
      "PUT /orgs/{org}/dependabot/secrets/{secret_name}"
    ],
    createOrUpdateRepoSecret: [
      "PUT /repos/{owner}/{repo}/dependabot/secrets/{secret_name}"
    ],
    deleteOrgSecret: ["DELETE /orgs/{org}/dependabot/secrets/{secret_name}"],
    deleteRepoSecret: [
      "DELETE /repos/{owner}/{repo}/dependabot/secrets/{secret_name}"
    ],
    getAlert: ["GET /repos/{owner}/{repo}/dependabot/alerts/{alert_number}"],
    getOrgPublicKey: ["GET /orgs/{org}/dependabot/secrets/public-key"],
    getOrgSecret: ["GET /orgs/{org}/dependabot/secrets/{secret_name}"],
    getRepoPublicKey: [
      "GET /repos/{owner}/{repo}/dependabot/secrets/public-key"
    ],
    getRepoSecret: [
      "GET /repos/{owner}/{repo}/dependabot/secrets/{secret_name}"
    ],
    listAlertsForEnterprise: [
      "GET /enterprises/{enterprise}/dependabot/alerts"
    ],
    listAlertsForOrg: ["GET /orgs/{org}/dependabot/alerts"],
    listAlertsForRepo: ["GET /repos/{owner}/{repo}/dependabot/alerts"],
    listOrgSecrets: ["GET /orgs/{org}/dependabot/secrets"],
    listRepoSecrets: ["GET /repos/{owner}/{repo}/dependabot/secrets"],
    listSelectedReposForOrgSecret: [
      "GET /orgs/{org}/dependabot/secrets/{secret_name}/repositories"
    ],
    removeSelectedRepoFromOrgSecret: [
      "DELETE /orgs/{org}/dependabot/secrets/{secret_name}/repositories/{repository_id}"
    ],
    repositoryAccessForOrg: [
      "GET /organizations/{org}/dependabot/repository-access"
    ],
    setRepositoryAccessDefaultLevel: [
      "PUT /organizations/{org}/dependabot/repository-access/default-level"
    ],
    setSelectedReposForOrgSecret: [
      "PUT /orgs/{org}/dependabot/secrets/{secret_name}/repositories"
    ],
    updateAlert: [
      "PATCH /repos/{owner}/{repo}/dependabot/alerts/{alert_number}"
    ],
    updateRepositoryAccessForOrg: [
      "PATCH /organizations/{org}/dependabot/repository-access"
    ]
  },
  dependencyGraph: {
    createRepositorySnapshot: [
      "POST /repos/{owner}/{repo}/dependency-graph/snapshots"
    ],
    diffRange: [
      "GET /repos/{owner}/{repo}/dependency-graph/compare/{basehead}"
    ],
    exportSbom: ["GET /repos/{owner}/{repo}/dependency-graph/sbom"]
  },
  emojis: { get: ["GET /emojis"] },
  enterpriseTeamMemberships: {
    add: [
      "PUT /enterprises/{enterprise}/teams/{enterprise-team}/memberships/{username}"
    ],
    bulkAdd: [
      "POST /enterprises/{enterprise}/teams/{enterprise-team}/memberships/add"
    ],
    bulkRemove: [
      "POST /enterprises/{enterprise}/teams/{enterprise-team}/memberships/remove"
    ],
    get: [
      "GET /enterprises/{enterprise}/teams/{enterprise-team}/memberships/{username}"
    ],
    list: ["GET /enterprises/{enterprise}/teams/{enterprise-team}/memberships"],
    remove: [
      "DELETE /enterprises/{enterprise}/teams/{enterprise-team}/memberships/{username}"
    ]
  },
  enterpriseTeamOrganizations: {
    add: [
      "PUT /enterprises/{enterprise}/teams/{enterprise-team}/organizations/{org}"
    ],
    bulkAdd: [
      "POST /enterprises/{enterprise}/teams/{enterprise-team}/organizations/add"
    ],
    bulkRemove: [
      "POST /enterprises/{enterprise}/teams/{enterprise-team}/organizations/remove"
    ],
    delete: [
      "DELETE /enterprises/{enterprise}/teams/{enterprise-team}/organizations/{org}"
    ],
    getAssignment: [
      "GET /enterprises/{enterprise}/teams/{enterprise-team}/organizations/{org}"
    ],
    getAssignments: [
      "GET /enterprises/{enterprise}/teams/{enterprise-team}/organizations"
    ]
  },
  enterpriseTeams: {
    create: ["POST /enterprises/{enterprise}/teams"],
    delete: ["DELETE /enterprises/{enterprise}/teams/{team_slug}"],
    get: ["GET /enterprises/{enterprise}/teams/{team_slug}"],
    list: ["GET /enterprises/{enterprise}/teams"],
    update: ["PATCH /enterprises/{enterprise}/teams/{team_slug}"]
  },
  gists: {
    checkIsStarred: ["GET /gists/{gist_id}/star"],
    create: ["POST /gists"],
    createComment: ["POST /gists/{gist_id}/comments"],
    delete: ["DELETE /gists/{gist_id}"],
    deleteComment: ["DELETE /gists/{gist_id}/comments/{comment_id}"],
    fork: ["POST /gists/{gist_id}/forks"],
    get: ["GET /gists/{gist_id}"],
    getComment: ["GET /gists/{gist_id}/comments/{comment_id}"],
    getRevision: ["GET /gists/{gist_id}/{sha}"],
    list: ["GET /gists"],
    listComments: ["GET /gists/{gist_id}/comments"],
    listCommits: ["GET /gists/{gist_id}/commits"],
    listForUser: ["GET /users/{username}/gists"],
    listForks: ["GET /gists/{gist_id}/forks"],
    listPublic: ["GET /gists/public"],
    listStarred: ["GET /gists/starred"],
    star: ["PUT /gists/{gist_id}/star"],
    unstar: ["DELETE /gists/{gist_id}/star"],
    update: ["PATCH /gists/{gist_id}"],
    updateComment: ["PATCH /gists/{gist_id}/comments/{comment_id}"]
  },
  git: {
    createBlob: ["POST /repos/{owner}/{repo}/git/blobs"],
    createCommit: ["POST /repos/{owner}/{repo}/git/commits"],
    createRef: ["POST /repos/{owner}/{repo}/git/refs"],
    createTag: ["POST /repos/{owner}/{repo}/git/tags"],
    createTree: ["POST /repos/{owner}/{repo}/git/trees"],
    deleteRef: ["DELETE /repos/{owner}/{repo}/git/refs/{ref}"],
    getBlob: ["GET /repos/{owner}/{repo}/git/blobs/{file_sha}"],
    getCommit: ["GET /repos/{owner}/{repo}/git/commits/{commit_sha}"],
    getRef: ["GET /repos/{owner}/{repo}/git/ref/{ref}"],
    getTag: ["GET /repos/{owner}/{repo}/git/tags/{tag_sha}"],
    getTree: ["GET /repos/{owner}/{repo}/git/trees/{tree_sha}"],
    listMatchingRefs: ["GET /repos/{owner}/{repo}/git/matching-refs/{ref}"],
    updateRef: ["PATCH /repos/{owner}/{repo}/git/refs/{ref}"]
  },
  gitignore: {
    getAllTemplates: ["GET /gitignore/templates"],
    getTemplate: ["GET /gitignore/templates/{name}"]
  },
  hostedCompute: {
    createNetworkConfigurationForOrg: [
      "POST /orgs/{org}/settings/network-configurations"
    ],
    deleteNetworkConfigurationFromOrg: [
      "DELETE /orgs/{org}/settings/network-configurations/{network_configuration_id}"
    ],
    getNetworkConfigurationForOrg: [
      "GET /orgs/{org}/settings/network-configurations/{network_configuration_id}"
    ],
    getNetworkSettingsForOrg: [
      "GET /orgs/{org}/settings/network-settings/{network_settings_id}"
    ],
    listNetworkConfigurationsForOrg: [
      "GET /orgs/{org}/settings/network-configurations"
    ],
    updateNetworkConfigurationForOrg: [
      "PATCH /orgs/{org}/settings/network-configurations/{network_configuration_id}"
    ]
  },
  interactions: {
    getRestrictionsForAuthenticatedUser: ["GET /user/interaction-limits"],
    getRestrictionsForOrg: ["GET /orgs/{org}/interaction-limits"],
    getRestrictionsForRepo: ["GET /repos/{owner}/{repo}/interaction-limits"],
    getRestrictionsForYourPublicRepos: [
      "GET /user/interaction-limits",
      {},
      { renamed: ["interactions", "getRestrictionsForAuthenticatedUser"] }
    ],
    removeRestrictionsForAuthenticatedUser: ["DELETE /user/interaction-limits"],
    removeRestrictionsForOrg: ["DELETE /orgs/{org}/interaction-limits"],
    removeRestrictionsForRepo: [
      "DELETE /repos/{owner}/{repo}/interaction-limits"
    ],
    removeRestrictionsForYourPublicRepos: [
      "DELETE /user/interaction-limits",
      {},
      { renamed: ["interactions", "removeRestrictionsForAuthenticatedUser"] }
    ],
    setRestrictionsForAuthenticatedUser: ["PUT /user/interaction-limits"],
    setRestrictionsForOrg: ["PUT /orgs/{org}/interaction-limits"],
    setRestrictionsForRepo: ["PUT /repos/{owner}/{repo}/interaction-limits"],
    setRestrictionsForYourPublicRepos: [
      "PUT /user/interaction-limits",
      {},
      { renamed: ["interactions", "setRestrictionsForAuthenticatedUser"] }
    ]
  },
  issues: {
    addAssignees: [
      "POST /repos/{owner}/{repo}/issues/{issue_number}/assignees"
    ],
    addBlockedByDependency: [
      "POST /repos/{owner}/{repo}/issues/{issue_number}/dependencies/blocked_by"
    ],
    addLabels: ["POST /repos/{owner}/{repo}/issues/{issue_number}/labels"],
    addSubIssue: [
      "POST /repos/{owner}/{repo}/issues/{issue_number}/sub_issues"
    ],
    checkUserCanBeAssigned: ["GET /repos/{owner}/{repo}/assignees/{assignee}"],
    checkUserCanBeAssignedToIssue: [
      "GET /repos/{owner}/{repo}/issues/{issue_number}/assignees/{assignee}"
    ],
    create: ["POST /repos/{owner}/{repo}/issues"],
    createComment: [
      "POST /repos/{owner}/{repo}/issues/{issue_number}/comments"
    ],
    createLabel: ["POST /repos/{owner}/{repo}/labels"],
    createMilestone: ["POST /repos/{owner}/{repo}/milestones"],
    deleteComment: [
      "DELETE /repos/{owner}/{repo}/issues/comments/{comment_id}"
    ],
    deleteLabel: ["DELETE /repos/{owner}/{repo}/labels/{name}"],
    deleteMilestone: [
      "DELETE /repos/{owner}/{repo}/milestones/{milestone_number}"
    ],
    get: ["GET /repos/{owner}/{repo}/issues/{issue_number}"],
    getComment: ["GET /repos/{owner}/{repo}/issues/comments/{comment_id}"],
    getEvent: ["GET /repos/{owner}/{repo}/issues/events/{event_id}"],
    getLabel: ["GET /repos/{owner}/{repo}/labels/{name}"],
    getMilestone: ["GET /repos/{owner}/{repo}/milestones/{milestone_number}"],
    getParent: ["GET /repos/{owner}/{repo}/issues/{issue_number}/parent"],
    list: ["GET /issues"],
    listAssignees: ["GET /repos/{owner}/{repo}/assignees"],
    listComments: ["GET /repos/{owner}/{repo}/issues/{issue_number}/comments"],
    listCommentsForRepo: ["GET /repos/{owner}/{repo}/issues/comments"],
    listDependenciesBlockedBy: [
      "GET /repos/{owner}/{repo}/issues/{issue_number}/dependencies/blocked_by"
    ],
    listDependenciesBlocking: [
      "GET /repos/{owner}/{repo}/issues/{issue_number}/dependencies/blocking"
    ],
    listEvents: ["GET /repos/{owner}/{repo}/issues/{issue_number}/events"],
    listEventsForRepo: ["GET /repos/{owner}/{repo}/issues/events"],
    listEventsForTimeline: [
      "GET /repos/{owner}/{repo}/issues/{issue_number}/timeline"
    ],
    listForAuthenticatedUser: ["GET /user/issues"],
    listForOrg: ["GET /orgs/{org}/issues"],
    listForRepo: ["GET /repos/{owner}/{repo}/issues"],
    listLabelsForMilestone: [
      "GET /repos/{owner}/{repo}/milestones/{milestone_number}/labels"
    ],
    listLabelsForRepo: ["GET /repos/{owner}/{repo}/labels"],
    listLabelsOnIssue: [
      "GET /repos/{owner}/{repo}/issues/{issue_number}/labels"
    ],
    listMilestones: ["GET /repos/{owner}/{repo}/milestones"],
    listSubIssues: [
      "GET /repos/{owner}/{repo}/issues/{issue_number}/sub_issues"
    ],
    lock: ["PUT /repos/{owner}/{repo}/issues/{issue_number}/lock"],
    removeAllLabels: [
      "DELETE /repos/{owner}/{repo}/issues/{issue_number}/labels"
    ],
    removeAssignees: [
      "DELETE /repos/{owner}/{repo}/issues/{issue_number}/assignees"
    ],
    removeDependencyBlockedBy: [
      "DELETE /repos/{owner}/{repo}/issues/{issue_number}/dependencies/blocked_by/{issue_id}"
    ],
    removeLabel: [
      "DELETE /repos/{owner}/{repo}/issues/{issue_number}/labels/{name}"
    ],
    removeSubIssue: [
      "DELETE /repos/{owner}/{repo}/issues/{issue_number}/sub_issue"
    ],
    reprioritizeSubIssue: [
      "PATCH /repos/{owner}/{repo}/issues/{issue_number}/sub_issues/priority"
    ],
    setLabels: ["PUT /repos/{owner}/{repo}/issues/{issue_number}/labels"],
    unlock: ["DELETE /repos/{owner}/{repo}/issues/{issue_number}/lock"],
    update: ["PATCH /repos/{owner}/{repo}/issues/{issue_number}"],
    updateComment: ["PATCH /repos/{owner}/{repo}/issues/comments/{comment_id}"],
    updateLabel: ["PATCH /repos/{owner}/{repo}/labels/{name}"],
    updateMilestone: [
      "PATCH /repos/{owner}/{repo}/milestones/{milestone_number}"
    ]
  },
  licenses: {
    get: ["GET /licenses/{license}"],
    getAllCommonlyUsed: ["GET /licenses"],
    getForRepo: ["GET /repos/{owner}/{repo}/license"]
  },
  markdown: {
    render: ["POST /markdown"],
    renderRaw: [
      "POST /markdown/raw",
      { headers: { "content-type": "text/plain; charset=utf-8" } }
    ]
  },
  meta: {
    get: ["GET /meta"],
    getAllVersions: ["GET /versions"],
    getOctocat: ["GET /octocat"],
    getZen: ["GET /zen"],
    root: ["GET /"]
  },
  migrations: {
    deleteArchiveForAuthenticatedUser: [
      "DELETE /user/migrations/{migration_id}/archive"
    ],
    deleteArchiveForOrg: [
      "DELETE /orgs/{org}/migrations/{migration_id}/archive"
    ],
    downloadArchiveForOrg: [
      "GET /orgs/{org}/migrations/{migration_id}/archive"
    ],
    getArchiveForAuthenticatedUser: [
      "GET /user/migrations/{migration_id}/archive"
    ],
    getStatusForAuthenticatedUser: ["GET /user/migrations/{migration_id}"],
    getStatusForOrg: ["GET /orgs/{org}/migrations/{migration_id}"],
    listForAuthenticatedUser: ["GET /user/migrations"],
    listForOrg: ["GET /orgs/{org}/migrations"],
    listReposForAuthenticatedUser: [
      "GET /user/migrations/{migration_id}/repositories"
    ],
    listReposForOrg: ["GET /orgs/{org}/migrations/{migration_id}/repositories"],
    listReposForUser: [
      "GET /user/migrations/{migration_id}/repositories",
      {},
      { renamed: ["migrations", "listReposForAuthenticatedUser"] }
    ],
    startForAuthenticatedUser: ["POST /user/migrations"],
    startForOrg: ["POST /orgs/{org}/migrations"],
    unlockRepoForAuthenticatedUser: [
      "DELETE /user/migrations/{migration_id}/repos/{repo_name}/lock"
    ],
    unlockRepoForOrg: [
      "DELETE /orgs/{org}/migrations/{migration_id}/repos/{repo_name}/lock"
    ]
  },
  oidc: {
    getOidcCustomSubTemplateForOrg: [
      "GET /orgs/{org}/actions/oidc/customization/sub"
    ],
    updateOidcCustomSubTemplateForOrg: [
      "PUT /orgs/{org}/actions/oidc/customization/sub"
    ]
  },
  orgs: {
    addSecurityManagerTeam: [
      "PUT /orgs/{org}/security-managers/teams/{team_slug}",
      {},
      {
        deprecated: "octokit.rest.orgs.addSecurityManagerTeam() is deprecated, see https://docs.github.com/rest/orgs/security-managers#add-a-security-manager-team"
      }
    ],
    assignTeamToOrgRole: [
      "PUT /orgs/{org}/organization-roles/teams/{team_slug}/{role_id}"
    ],
    assignUserToOrgRole: [
      "PUT /orgs/{org}/organization-roles/users/{username}/{role_id}"
    ],
    blockUser: ["PUT /orgs/{org}/blocks/{username}"],
    cancelInvitation: ["DELETE /orgs/{org}/invitations/{invitation_id}"],
    checkBlockedUser: ["GET /orgs/{org}/blocks/{username}"],
    checkMembershipForUser: ["GET /orgs/{org}/members/{username}"],
    checkPublicMembershipForUser: ["GET /orgs/{org}/public_members/{username}"],
    convertMemberToOutsideCollaborator: [
      "PUT /orgs/{org}/outside_collaborators/{username}"
    ],
    createArtifactStorageRecord: [
      "POST /orgs/{org}/artifacts/metadata/storage-record"
    ],
    createInvitation: ["POST /orgs/{org}/invitations"],
    createIssueType: ["POST /orgs/{org}/issue-types"],
    createWebhook: ["POST /orgs/{org}/hooks"],
    customPropertiesForOrgsCreateOrUpdateOrganizationValues: [
      "PATCH /organizations/{org}/org-properties/values"
    ],
    customPropertiesForOrgsGetOrganizationValues: [
      "GET /organizations/{org}/org-properties/values"
    ],
    customPropertiesForReposCreateOrUpdateOrganizationDefinition: [
      "PUT /orgs/{org}/properties/schema/{custom_property_name}"
    ],
    customPropertiesForReposCreateOrUpdateOrganizationDefinitions: [
      "PATCH /orgs/{org}/properties/schema"
    ],
    customPropertiesForReposCreateOrUpdateOrganizationValues: [
      "PATCH /orgs/{org}/properties/values"
    ],
    customPropertiesForReposDeleteOrganizationDefinition: [
      "DELETE /orgs/{org}/properties/schema/{custom_property_name}"
    ],
    customPropertiesForReposGetOrganizationDefinition: [
      "GET /orgs/{org}/properties/schema/{custom_property_name}"
    ],
    customPropertiesForReposGetOrganizationDefinitions: [
      "GET /orgs/{org}/properties/schema"
    ],
    customPropertiesForReposGetOrganizationValues: [
      "GET /orgs/{org}/properties/values"
    ],
    delete: ["DELETE /orgs/{org}"],
    deleteAttestationsBulk: ["POST /orgs/{org}/attestations/delete-request"],
    deleteAttestationsById: [
      "DELETE /orgs/{org}/attestations/{attestation_id}"
    ],
    deleteAttestationsBySubjectDigest: [
      "DELETE /orgs/{org}/attestations/digest/{subject_digest}"
    ],
    deleteIssueType: ["DELETE /orgs/{org}/issue-types/{issue_type_id}"],
    deleteWebhook: ["DELETE /orgs/{org}/hooks/{hook_id}"],
    disableSelectedRepositoryImmutableReleasesOrganization: [
      "DELETE /orgs/{org}/settings/immutable-releases/repositories/{repository_id}"
    ],
    enableSelectedRepositoryImmutableReleasesOrganization: [
      "PUT /orgs/{org}/settings/immutable-releases/repositories/{repository_id}"
    ],
    get: ["GET /orgs/{org}"],
    getImmutableReleasesSettings: [
      "GET /orgs/{org}/settings/immutable-releases"
    ],
    getImmutableReleasesSettingsRepositories: [
      "GET /orgs/{org}/settings/immutable-releases/repositories"
    ],
    getMembershipForAuthenticatedUser: ["GET /user/memberships/orgs/{org}"],
    getMembershipForUser: ["GET /orgs/{org}/memberships/{username}"],
    getOrgRole: ["GET /orgs/{org}/organization-roles/{role_id}"],
    getOrgRulesetHistory: ["GET /orgs/{org}/rulesets/{ruleset_id}/history"],
    getOrgRulesetVersion: [
      "GET /orgs/{org}/rulesets/{ruleset_id}/history/{version_id}"
    ],
    getWebhook: ["GET /orgs/{org}/hooks/{hook_id}"],
    getWebhookConfigForOrg: ["GET /orgs/{org}/hooks/{hook_id}/config"],
    getWebhookDelivery: [
      "GET /orgs/{org}/hooks/{hook_id}/deliveries/{delivery_id}"
    ],
    list: ["GET /organizations"],
    listAppInstallations: ["GET /orgs/{org}/installations"],
    listArtifactStorageRecords: [
      "GET /orgs/{org}/artifacts/{subject_digest}/metadata/storage-records"
    ],
    listAttestationRepositories: ["GET /orgs/{org}/attestations/repositories"],
    listAttestations: ["GET /orgs/{org}/attestations/{subject_digest}"],
    listAttestationsBulk: [
      "POST /orgs/{org}/attestations/bulk-list{?per_page,before,after}"
    ],
    listBlockedUsers: ["GET /orgs/{org}/blocks"],
    listFailedInvitations: ["GET /orgs/{org}/failed_invitations"],
    listForAuthenticatedUser: ["GET /user/orgs"],
    listForUser: ["GET /users/{username}/orgs"],
    listInvitationTeams: ["GET /orgs/{org}/invitations/{invitation_id}/teams"],
    listIssueTypes: ["GET /orgs/{org}/issue-types"],
    listMembers: ["GET /orgs/{org}/members"],
    listMembershipsForAuthenticatedUser: ["GET /user/memberships/orgs"],
    listOrgRoleTeams: ["GET /orgs/{org}/organization-roles/{role_id}/teams"],
    listOrgRoleUsers: ["GET /orgs/{org}/organization-roles/{role_id}/users"],
    listOrgRoles: ["GET /orgs/{org}/organization-roles"],
    listOrganizationFineGrainedPermissions: [
      "GET /orgs/{org}/organization-fine-grained-permissions"
    ],
    listOutsideCollaborators: ["GET /orgs/{org}/outside_collaborators"],
    listPatGrantRepositories: [
      "GET /orgs/{org}/personal-access-tokens/{pat_id}/repositories"
    ],
    listPatGrantRequestRepositories: [
      "GET /orgs/{org}/personal-access-token-requests/{pat_request_id}/repositories"
    ],
    listPatGrantRequests: ["GET /orgs/{org}/personal-access-token-requests"],
    listPatGrants: ["GET /orgs/{org}/personal-access-tokens"],
    listPendingInvitations: ["GET /orgs/{org}/invitations"],
    listPublicMembers: ["GET /orgs/{org}/public_members"],
    listSecurityManagerTeams: [
      "GET /orgs/{org}/security-managers",
      {},
      {
        deprecated: "octokit.rest.orgs.listSecurityManagerTeams() is deprecated, see https://docs.github.com/rest/orgs/security-managers#list-security-manager-teams"
      }
    ],
    listWebhookDeliveries: ["GET /orgs/{org}/hooks/{hook_id}/deliveries"],
    listWebhooks: ["GET /orgs/{org}/hooks"],
    pingWebhook: ["POST /orgs/{org}/hooks/{hook_id}/pings"],
    redeliverWebhookDelivery: [
      "POST /orgs/{org}/hooks/{hook_id}/deliveries/{delivery_id}/attempts"
    ],
    removeMember: ["DELETE /orgs/{org}/members/{username}"],
    removeMembershipForUser: ["DELETE /orgs/{org}/memberships/{username}"],
    removeOutsideCollaborator: [
      "DELETE /orgs/{org}/outside_collaborators/{username}"
    ],
    removePublicMembershipForAuthenticatedUser: [
      "DELETE /orgs/{org}/public_members/{username}"
    ],
    removeSecurityManagerTeam: [
      "DELETE /orgs/{org}/security-managers/teams/{team_slug}",
      {},
      {
        deprecated: "octokit.rest.orgs.removeSecurityManagerTeam() is deprecated, see https://docs.github.com/rest/orgs/security-managers#remove-a-security-manager-team"
      }
    ],
    reviewPatGrantRequest: [
      "POST /orgs/{org}/personal-access-token-requests/{pat_request_id}"
    ],
    reviewPatGrantRequestsInBulk: [
      "POST /orgs/{org}/personal-access-token-requests"
    ],
    revokeAllOrgRolesTeam: [
      "DELETE /orgs/{org}/organization-roles/teams/{team_slug}"
    ],
    revokeAllOrgRolesUser: [
      "DELETE /orgs/{org}/organization-roles/users/{username}"
    ],
    revokeOrgRoleTeam: [
      "DELETE /orgs/{org}/organization-roles/teams/{team_slug}/{role_id}"
    ],
    revokeOrgRoleUser: [
      "DELETE /orgs/{org}/organization-roles/users/{username}/{role_id}"
    ],
    setImmutableReleasesSettings: [
      "PUT /orgs/{org}/settings/immutable-releases"
    ],
    setImmutableReleasesSettingsRepositories: [
      "PUT /orgs/{org}/settings/immutable-releases/repositories"
    ],
    setMembershipForUser: ["PUT /orgs/{org}/memberships/{username}"],
    setPublicMembershipForAuthenticatedUser: [
      "PUT /orgs/{org}/public_members/{username}"
    ],
    unblockUser: ["DELETE /orgs/{org}/blocks/{username}"],
    update: ["PATCH /orgs/{org}"],
    updateIssueType: ["PUT /orgs/{org}/issue-types/{issue_type_id}"],
    updateMembershipForAuthenticatedUser: [
      "PATCH /user/memberships/orgs/{org}"
    ],
    updatePatAccess: ["POST /orgs/{org}/personal-access-tokens/{pat_id}"],
    updatePatAccesses: ["POST /orgs/{org}/personal-access-tokens"],
    updateWebhook: ["PATCH /orgs/{org}/hooks/{hook_id}"],
    updateWebhookConfigForOrg: ["PATCH /orgs/{org}/hooks/{hook_id}/config"]
  },
  packages: {
    deletePackageForAuthenticatedUser: [
      "DELETE /user/packages/{package_type}/{package_name}"
    ],
    deletePackageForOrg: [
      "DELETE /orgs/{org}/packages/{package_type}/{package_name}"
    ],
    deletePackageForUser: [
      "DELETE /users/{username}/packages/{package_type}/{package_name}"
    ],
    deletePackageVersionForAuthenticatedUser: [
      "DELETE /user/packages/{package_type}/{package_name}/versions/{package_version_id}"
    ],
    deletePackageVersionForOrg: [
      "DELETE /orgs/{org}/packages/{package_type}/{package_name}/versions/{package_version_id}"
    ],
    deletePackageVersionForUser: [
      "DELETE /users/{username}/packages/{package_type}/{package_name}/versions/{package_version_id}"
    ],
    getAllPackageVersionsForAPackageOwnedByAnOrg: [
      "GET /orgs/{org}/packages/{package_type}/{package_name}/versions",
      {},
      { renamed: ["packages", "getAllPackageVersionsForPackageOwnedByOrg"] }
    ],
    getAllPackageVersionsForAPackageOwnedByTheAuthenticatedUser: [
      "GET /user/packages/{package_type}/{package_name}/versions",
      {},
      {
        renamed: [
          "packages",
          "getAllPackageVersionsForPackageOwnedByAuthenticatedUser"
        ]
      }
    ],
    getAllPackageVersionsForPackageOwnedByAuthenticatedUser: [
      "GET /user/packages/{package_type}/{package_name}/versions"
    ],
    getAllPackageVersionsForPackageOwnedByOrg: [
      "GET /orgs/{org}/packages/{package_type}/{package_name}/versions"
    ],
    getAllPackageVersionsForPackageOwnedByUser: [
      "GET /users/{username}/packages/{package_type}/{package_name}/versions"
    ],
    getPackageForAuthenticatedUser: [
      "GET /user/packages/{package_type}/{package_name}"
    ],
    getPackageForOrganization: [
      "GET /orgs/{org}/packages/{package_type}/{package_name}"
    ],
    getPackageForUser: [
      "GET /users/{username}/packages/{package_type}/{package_name}"
    ],
    getPackageVersionForAuthenticatedUser: [
      "GET /user/packages/{package_type}/{package_name}/versions/{package_version_id}"
    ],
    getPackageVersionForOrganization: [
      "GET /orgs/{org}/packages/{package_type}/{package_name}/versions/{package_version_id}"
    ],
    getPackageVersionForUser: [
      "GET /users/{username}/packages/{package_type}/{package_name}/versions/{package_version_id}"
    ],
    listDockerMigrationConflictingPackagesForAuthenticatedUser: [
      "GET /user/docker/conflicts"
    ],
    listDockerMigrationConflictingPackagesForOrganization: [
      "GET /orgs/{org}/docker/conflicts"
    ],
    listDockerMigrationConflictingPackagesForUser: [
      "GET /users/{username}/docker/conflicts"
    ],
    listPackagesForAuthenticatedUser: ["GET /user/packages"],
    listPackagesForOrganization: ["GET /orgs/{org}/packages"],
    listPackagesForUser: ["GET /users/{username}/packages"],
    restorePackageForAuthenticatedUser: [
      "POST /user/packages/{package_type}/{package_name}/restore{?token}"
    ],
    restorePackageForOrg: [
      "POST /orgs/{org}/packages/{package_type}/{package_name}/restore{?token}"
    ],
    restorePackageForUser: [
      "POST /users/{username}/packages/{package_type}/{package_name}/restore{?token}"
    ],
    restorePackageVersionForAuthenticatedUser: [
      "POST /user/packages/{package_type}/{package_name}/versions/{package_version_id}/restore"
    ],
    restorePackageVersionForOrg: [
      "POST /orgs/{org}/packages/{package_type}/{package_name}/versions/{package_version_id}/restore"
    ],
    restorePackageVersionForUser: [
      "POST /users/{username}/packages/{package_type}/{package_name}/versions/{package_version_id}/restore"
    ]
  },
  privateRegistries: {
    createOrgPrivateRegistry: ["POST /orgs/{org}/private-registries"],
    deleteOrgPrivateRegistry: [
      "DELETE /orgs/{org}/private-registries/{secret_name}"
    ],
    getOrgPrivateRegistry: ["GET /orgs/{org}/private-registries/{secret_name}"],
    getOrgPublicKey: ["GET /orgs/{org}/private-registries/public-key"],
    listOrgPrivateRegistries: ["GET /orgs/{org}/private-registries"],
    updateOrgPrivateRegistry: [
      "PATCH /orgs/{org}/private-registries/{secret_name}"
    ]
  },
  projects: {
    addItemForOrg: ["POST /orgs/{org}/projectsV2/{project_number}/items"],
    addItemForUser: [
      "POST /users/{username}/projectsV2/{project_number}/items"
    ],
    deleteItemForOrg: [
      "DELETE /orgs/{org}/projectsV2/{project_number}/items/{item_id}"
    ],
    deleteItemForUser: [
      "DELETE /users/{username}/projectsV2/{project_number}/items/{item_id}"
    ],
    getFieldForOrg: [
      "GET /orgs/{org}/projectsV2/{project_number}/fields/{field_id}"
    ],
    getFieldForUser: [
      "GET /users/{username}/projectsV2/{project_number}/fields/{field_id}"
    ],
    getForOrg: ["GET /orgs/{org}/projectsV2/{project_number}"],
    getForUser: ["GET /users/{username}/projectsV2/{project_number}"],
    getOrgItem: ["GET /orgs/{org}/projectsV2/{project_number}/items/{item_id}"],
    getUserItem: [
      "GET /users/{username}/projectsV2/{project_number}/items/{item_id}"
    ],
    listFieldsForOrg: ["GET /orgs/{org}/projectsV2/{project_number}/fields"],
    listFieldsForUser: [
      "GET /users/{username}/projectsV2/{project_number}/fields"
    ],
    listForOrg: ["GET /orgs/{org}/projectsV2"],
    listForUser: ["GET /users/{username}/projectsV2"],
    listItemsForOrg: ["GET /orgs/{org}/projectsV2/{project_number}/items"],
    listItemsForUser: [
      "GET /users/{username}/projectsV2/{project_number}/items"
    ],
    updateItemForOrg: [
      "PATCH /orgs/{org}/projectsV2/{project_number}/items/{item_id}"
    ],
    updateItemForUser: [
      "PATCH /users/{username}/projectsV2/{project_number}/items/{item_id}"
    ]
  },
  pulls: {
    checkIfMerged: ["GET /repos/{owner}/{repo}/pulls/{pull_number}/merge"],
    create: ["POST /repos/{owner}/{repo}/pulls"],
    createReplyForReviewComment: [
      "POST /repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies"
    ],
    createReview: ["POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews"],
    createReviewComment: [
      "POST /repos/{owner}/{repo}/pulls/{pull_number}/comments"
    ],
    deletePendingReview: [
      "DELETE /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}"
    ],
    deleteReviewComment: [
      "DELETE /repos/{owner}/{repo}/pulls/comments/{comment_id}"
    ],
    dismissReview: [
      "PUT /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/dismissals"
    ],
    get: ["GET /repos/{owner}/{repo}/pulls/{pull_number}"],
    getReview: [
      "GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}"
    ],
    getReviewComment: ["GET /repos/{owner}/{repo}/pulls/comments/{comment_id}"],
    list: ["GET /repos/{owner}/{repo}/pulls"],
    listCommentsForReview: [
      "GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/comments"
    ],
    listCommits: ["GET /repos/{owner}/{repo}/pulls/{pull_number}/commits"],
    listFiles: ["GET /repos/{owner}/{repo}/pulls/{pull_number}/files"],
    listRequestedReviewers: [
      "GET /repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers"
    ],
    listReviewComments: [
      "GET /repos/{owner}/{repo}/pulls/{pull_number}/comments"
    ],
    listReviewCommentsForRepo: ["GET /repos/{owner}/{repo}/pulls/comments"],
    listReviews: ["GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews"],
    merge: ["PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge"],
    removeRequestedReviewers: [
      "DELETE /repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers"
    ],
    requestReviewers: [
      "POST /repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers"
    ],
    submitReview: [
      "POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/events"
    ],
    update: ["PATCH /repos/{owner}/{repo}/pulls/{pull_number}"],
    updateBranch: [
      "PUT /repos/{owner}/{repo}/pulls/{pull_number}/update-branch"
    ],
    updateReview: [
      "PUT /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}"
    ],
    updateReviewComment: [
      "PATCH /repos/{owner}/{repo}/pulls/comments/{comment_id}"
    ]
  },
  rateLimit: { get: ["GET /rate_limit"] },
  reactions: {
    createForCommitComment: [
      "POST /repos/{owner}/{repo}/comments/{comment_id}/reactions"
    ],
    createForIssue: [
      "POST /repos/{owner}/{repo}/issues/{issue_number}/reactions"
    ],
    createForIssueComment: [
      "POST /repos/{owner}/{repo}/issues/comments/{comment_id}/reactions"
    ],
    createForPullRequestReviewComment: [
      "POST /repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions"
    ],
    createForRelease: [
      "POST /repos/{owner}/{repo}/releases/{release_id}/reactions"
    ],
    createForTeamDiscussionCommentInOrg: [
      "POST /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments/{comment_number}/reactions"
    ],
    createForTeamDiscussionInOrg: [
      "POST /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/reactions"
    ],
    deleteForCommitComment: [
      "DELETE /repos/{owner}/{repo}/comments/{comment_id}/reactions/{reaction_id}"
    ],
    deleteForIssue: [
      "DELETE /repos/{owner}/{repo}/issues/{issue_number}/reactions/{reaction_id}"
    ],
    deleteForIssueComment: [
      "DELETE /repos/{owner}/{repo}/issues/comments/{comment_id}/reactions/{reaction_id}"
    ],
    deleteForPullRequestComment: [
      "DELETE /repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions/{reaction_id}"
    ],
    deleteForRelease: [
      "DELETE /repos/{owner}/{repo}/releases/{release_id}/reactions/{reaction_id}"
    ],
    deleteForTeamDiscussion: [
      "DELETE /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/reactions/{reaction_id}"
    ],
    deleteForTeamDiscussionComment: [
      "DELETE /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments/{comment_number}/reactions/{reaction_id}"
    ],
    listForCommitComment: [
      "GET /repos/{owner}/{repo}/comments/{comment_id}/reactions"
    ],
    listForIssue: ["GET /repos/{owner}/{repo}/issues/{issue_number}/reactions"],
    listForIssueComment: [
      "GET /repos/{owner}/{repo}/issues/comments/{comment_id}/reactions"
    ],
    listForPullRequestReviewComment: [
      "GET /repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions"
    ],
    listForRelease: [
      "GET /repos/{owner}/{repo}/releases/{release_id}/reactions"
    ],
    listForTeamDiscussionCommentInOrg: [
      "GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments/{comment_number}/reactions"
    ],
    listForTeamDiscussionInOrg: [
      "GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/reactions"
    ]
  },
  repos: {
    acceptInvitation: [
      "PATCH /user/repository_invitations/{invitation_id}",
      {},
      { renamed: ["repos", "acceptInvitationForAuthenticatedUser"] }
    ],
    acceptInvitationForAuthenticatedUser: [
      "PATCH /user/repository_invitations/{invitation_id}"
    ],
    addAppAccessRestrictions: [
      "POST /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/apps",
      {},
      { mapToData: "apps" }
    ],
    addCollaborator: ["PUT /repos/{owner}/{repo}/collaborators/{username}"],
    addStatusCheckContexts: [
      "POST /repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks/contexts",
      {},
      { mapToData: "contexts" }
    ],
    addTeamAccessRestrictions: [
      "POST /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/teams",
      {},
      { mapToData: "teams" }
    ],
    addUserAccessRestrictions: [
      "POST /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/users",
      {},
      { mapToData: "users" }
    ],
    cancelPagesDeployment: [
      "POST /repos/{owner}/{repo}/pages/deployments/{pages_deployment_id}/cancel"
    ],
    checkAutomatedSecurityFixes: [
      "GET /repos/{owner}/{repo}/automated-security-fixes"
    ],
    checkCollaborator: ["GET /repos/{owner}/{repo}/collaborators/{username}"],
    checkImmutableReleases: ["GET /repos/{owner}/{repo}/immutable-releases"],
    checkPrivateVulnerabilityReporting: [
      "GET /repos/{owner}/{repo}/private-vulnerability-reporting"
    ],
    checkVulnerabilityAlerts: [
      "GET /repos/{owner}/{repo}/vulnerability-alerts"
    ],
    codeownersErrors: ["GET /repos/{owner}/{repo}/codeowners/errors"],
    compareCommits: ["GET /repos/{owner}/{repo}/compare/{base}...{head}"],
    compareCommitsWithBasehead: [
      "GET /repos/{owner}/{repo}/compare/{basehead}"
    ],
    createAttestation: ["POST /repos/{owner}/{repo}/attestations"],
    createAutolink: ["POST /repos/{owner}/{repo}/autolinks"],
    createCommitComment: [
      "POST /repos/{owner}/{repo}/commits/{commit_sha}/comments"
    ],
    createCommitSignatureProtection: [
      "POST /repos/{owner}/{repo}/branches/{branch}/protection/required_signatures"
    ],
    createCommitStatus: ["POST /repos/{owner}/{repo}/statuses/{sha}"],
    createDeployKey: ["POST /repos/{owner}/{repo}/keys"],
    createDeployment: ["POST /repos/{owner}/{repo}/deployments"],
    createDeploymentBranchPolicy: [
      "POST /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies"
    ],
    createDeploymentProtectionRule: [
      "POST /repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules"
    ],
    createDeploymentStatus: [
      "POST /repos/{owner}/{repo}/deployments/{deployment_id}/statuses"
    ],
    createDispatchEvent: ["POST /repos/{owner}/{repo}/dispatches"],
    createForAuthenticatedUser: ["POST /user/repos"],
    createFork: ["POST /repos/{owner}/{repo}/forks"],
    createInOrg: ["POST /orgs/{org}/repos"],
    createOrUpdateEnvironment: [
      "PUT /repos/{owner}/{repo}/environments/{environment_name}"
    ],
    createOrUpdateFileContents: ["PUT /repos/{owner}/{repo}/contents/{path}"],
    createOrgRuleset: ["POST /orgs/{org}/rulesets"],
    createPagesDeployment: ["POST /repos/{owner}/{repo}/pages/deployments"],
    createPagesSite: ["POST /repos/{owner}/{repo}/pages"],
    createRelease: ["POST /repos/{owner}/{repo}/releases"],
    createRepoRuleset: ["POST /repos/{owner}/{repo}/rulesets"],
    createUsingTemplate: [
      "POST /repos/{template_owner}/{template_repo}/generate"
    ],
    createWebhook: ["POST /repos/{owner}/{repo}/hooks"],
    customPropertiesForReposCreateOrUpdateRepositoryValues: [
      "PATCH /repos/{owner}/{repo}/properties/values"
    ],
    customPropertiesForReposGetRepositoryValues: [
      "GET /repos/{owner}/{repo}/properties/values"
    ],
    declineInvitation: [
      "DELETE /user/repository_invitations/{invitation_id}",
      {},
      { renamed: ["repos", "declineInvitationForAuthenticatedUser"] }
    ],
    declineInvitationForAuthenticatedUser: [
      "DELETE /user/repository_invitations/{invitation_id}"
    ],
    delete: ["DELETE /repos/{owner}/{repo}"],
    deleteAccessRestrictions: [
      "DELETE /repos/{owner}/{repo}/branches/{branch}/protection/restrictions"
    ],
    deleteAdminBranchProtection: [
      "DELETE /repos/{owner}/{repo}/branches/{branch}/protection/enforce_admins"
    ],
    deleteAnEnvironment: [
      "DELETE /repos/{owner}/{repo}/environments/{environment_name}"
    ],
    deleteAutolink: ["DELETE /repos/{owner}/{repo}/autolinks/{autolink_id}"],
    deleteBranchProtection: [
      "DELETE /repos/{owner}/{repo}/branches/{branch}/protection"
    ],
    deleteCommitComment: ["DELETE /repos/{owner}/{repo}/comments/{comment_id}"],
    deleteCommitSignatureProtection: [
      "DELETE /repos/{owner}/{repo}/branches/{branch}/protection/required_signatures"
    ],
    deleteDeployKey: ["DELETE /repos/{owner}/{repo}/keys/{key_id}"],
    deleteDeployment: [
      "DELETE /repos/{owner}/{repo}/deployments/{deployment_id}"
    ],
    deleteDeploymentBranchPolicy: [
      "DELETE /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies/{branch_policy_id}"
    ],
    deleteFile: ["DELETE /repos/{owner}/{repo}/contents/{path}"],
    deleteInvitation: [
      "DELETE /repos/{owner}/{repo}/invitations/{invitation_id}"
    ],
    deleteOrgRuleset: ["DELETE /orgs/{org}/rulesets/{ruleset_id}"],
    deletePagesSite: ["DELETE /repos/{owner}/{repo}/pages"],
    deletePullRequestReviewProtection: [
      "DELETE /repos/{owner}/{repo}/branches/{branch}/protection/required_pull_request_reviews"
    ],
    deleteRelease: ["DELETE /repos/{owner}/{repo}/releases/{release_id}"],
    deleteReleaseAsset: [
      "DELETE /repos/{owner}/{repo}/releases/assets/{asset_id}"
    ],
    deleteRepoRuleset: ["DELETE /repos/{owner}/{repo}/rulesets/{ruleset_id}"],
    deleteWebhook: ["DELETE /repos/{owner}/{repo}/hooks/{hook_id}"],
    disableAutomatedSecurityFixes: [
      "DELETE /repos/{owner}/{repo}/automated-security-fixes"
    ],
    disableDeploymentProtectionRule: [
      "DELETE /repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules/{protection_rule_id}"
    ],
    disableImmutableReleases: [
      "DELETE /repos/{owner}/{repo}/immutable-releases"
    ],
    disablePrivateVulnerabilityReporting: [
      "DELETE /repos/{owner}/{repo}/private-vulnerability-reporting"
    ],
    disableVulnerabilityAlerts: [
      "DELETE /repos/{owner}/{repo}/vulnerability-alerts"
    ],
    downloadArchive: [
      "GET /repos/{owner}/{repo}/zipball/{ref}",
      {},
      { renamed: ["repos", "downloadZipballArchive"] }
    ],
    downloadTarballArchive: ["GET /repos/{owner}/{repo}/tarball/{ref}"],
    downloadZipballArchive: ["GET /repos/{owner}/{repo}/zipball/{ref}"],
    enableAutomatedSecurityFixes: [
      "PUT /repos/{owner}/{repo}/automated-security-fixes"
    ],
    enableImmutableReleases: ["PUT /repos/{owner}/{repo}/immutable-releases"],
    enablePrivateVulnerabilityReporting: [
      "PUT /repos/{owner}/{repo}/private-vulnerability-reporting"
    ],
    enableVulnerabilityAlerts: [
      "PUT /repos/{owner}/{repo}/vulnerability-alerts"
    ],
    generateReleaseNotes: [
      "POST /repos/{owner}/{repo}/releases/generate-notes"
    ],
    get: ["GET /repos/{owner}/{repo}"],
    getAccessRestrictions: [
      "GET /repos/{owner}/{repo}/branches/{branch}/protection/restrictions"
    ],
    getAdminBranchProtection: [
      "GET /repos/{owner}/{repo}/branches/{branch}/protection/enforce_admins"
    ],
    getAllDeploymentProtectionRules: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules"
    ],
    getAllEnvironments: ["GET /repos/{owner}/{repo}/environments"],
    getAllStatusCheckContexts: [
      "GET /repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks/contexts"
    ],
    getAllTopics: ["GET /repos/{owner}/{repo}/topics"],
    getAppsWithAccessToProtectedBranch: [
      "GET /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/apps"
    ],
    getAutolink: ["GET /repos/{owner}/{repo}/autolinks/{autolink_id}"],
    getBranch: ["GET /repos/{owner}/{repo}/branches/{branch}"],
    getBranchProtection: [
      "GET /repos/{owner}/{repo}/branches/{branch}/protection"
    ],
    getBranchRules: ["GET /repos/{owner}/{repo}/rules/branches/{branch}"],
    getClones: ["GET /repos/{owner}/{repo}/traffic/clones"],
    getCodeFrequencyStats: ["GET /repos/{owner}/{repo}/stats/code_frequency"],
    getCollaboratorPermissionLevel: [
      "GET /repos/{owner}/{repo}/collaborators/{username}/permission"
    ],
    getCombinedStatusForRef: ["GET /repos/{owner}/{repo}/commits/{ref}/status"],
    getCommit: ["GET /repos/{owner}/{repo}/commits/{ref}"],
    getCommitActivityStats: ["GET /repos/{owner}/{repo}/stats/commit_activity"],
    getCommitComment: ["GET /repos/{owner}/{repo}/comments/{comment_id}"],
    getCommitSignatureProtection: [
      "GET /repos/{owner}/{repo}/branches/{branch}/protection/required_signatures"
    ],
    getCommunityProfileMetrics: ["GET /repos/{owner}/{repo}/community/profile"],
    getContent: ["GET /repos/{owner}/{repo}/contents/{path}"],
    getContributorsStats: ["GET /repos/{owner}/{repo}/stats/contributors"],
    getCustomDeploymentProtectionRule: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules/{protection_rule_id}"
    ],
    getDeployKey: ["GET /repos/{owner}/{repo}/keys/{key_id}"],
    getDeployment: ["GET /repos/{owner}/{repo}/deployments/{deployment_id}"],
    getDeploymentBranchPolicy: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies/{branch_policy_id}"
    ],
    getDeploymentStatus: [
      "GET /repos/{owner}/{repo}/deployments/{deployment_id}/statuses/{status_id}"
    ],
    getEnvironment: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}"
    ],
    getLatestPagesBuild: ["GET /repos/{owner}/{repo}/pages/builds/latest"],
    getLatestRelease: ["GET /repos/{owner}/{repo}/releases/latest"],
    getOrgRuleSuite: ["GET /orgs/{org}/rulesets/rule-suites/{rule_suite_id}"],
    getOrgRuleSuites: ["GET /orgs/{org}/rulesets/rule-suites"],
    getOrgRuleset: ["GET /orgs/{org}/rulesets/{ruleset_id}"],
    getOrgRulesets: ["GET /orgs/{org}/rulesets"],
    getPages: ["GET /repos/{owner}/{repo}/pages"],
    getPagesBuild: ["GET /repos/{owner}/{repo}/pages/builds/{build_id}"],
    getPagesDeployment: [
      "GET /repos/{owner}/{repo}/pages/deployments/{pages_deployment_id}"
    ],
    getPagesHealthCheck: ["GET /repos/{owner}/{repo}/pages/health"],
    getParticipationStats: ["GET /repos/{owner}/{repo}/stats/participation"],
    getPullRequestReviewProtection: [
      "GET /repos/{owner}/{repo}/branches/{branch}/protection/required_pull_request_reviews"
    ],
    getPunchCardStats: ["GET /repos/{owner}/{repo}/stats/punch_card"],
    getReadme: ["GET /repos/{owner}/{repo}/readme"],
    getReadmeInDirectory: ["GET /repos/{owner}/{repo}/readme/{dir}"],
    getRelease: ["GET /repos/{owner}/{repo}/releases/{release_id}"],
    getReleaseAsset: ["GET /repos/{owner}/{repo}/releases/assets/{asset_id}"],
    getReleaseByTag: ["GET /repos/{owner}/{repo}/releases/tags/{tag}"],
    getRepoRuleSuite: [
      "GET /repos/{owner}/{repo}/rulesets/rule-suites/{rule_suite_id}"
    ],
    getRepoRuleSuites: ["GET /repos/{owner}/{repo}/rulesets/rule-suites"],
    getRepoRuleset: ["GET /repos/{owner}/{repo}/rulesets/{ruleset_id}"],
    getRepoRulesetHistory: [
      "GET /repos/{owner}/{repo}/rulesets/{ruleset_id}/history"
    ],
    getRepoRulesetVersion: [
      "GET /repos/{owner}/{repo}/rulesets/{ruleset_id}/history/{version_id}"
    ],
    getRepoRulesets: ["GET /repos/{owner}/{repo}/rulesets"],
    getStatusChecksProtection: [
      "GET /repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks"
    ],
    getTeamsWithAccessToProtectedBranch: [
      "GET /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/teams"
    ],
    getTopPaths: ["GET /repos/{owner}/{repo}/traffic/popular/paths"],
    getTopReferrers: ["GET /repos/{owner}/{repo}/traffic/popular/referrers"],
    getUsersWithAccessToProtectedBranch: [
      "GET /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/users"
    ],
    getViews: ["GET /repos/{owner}/{repo}/traffic/views"],
    getWebhook: ["GET /repos/{owner}/{repo}/hooks/{hook_id}"],
    getWebhookConfigForRepo: [
      "GET /repos/{owner}/{repo}/hooks/{hook_id}/config"
    ],
    getWebhookDelivery: [
      "GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}"
    ],
    listActivities: ["GET /repos/{owner}/{repo}/activity"],
    listAttestations: [
      "GET /repos/{owner}/{repo}/attestations/{subject_digest}"
    ],
    listAutolinks: ["GET /repos/{owner}/{repo}/autolinks"],
    listBranches: ["GET /repos/{owner}/{repo}/branches"],
    listBranchesForHeadCommit: [
      "GET /repos/{owner}/{repo}/commits/{commit_sha}/branches-where-head"
    ],
    listCollaborators: ["GET /repos/{owner}/{repo}/collaborators"],
    listCommentsForCommit: [
      "GET /repos/{owner}/{repo}/commits/{commit_sha}/comments"
    ],
    listCommitCommentsForRepo: ["GET /repos/{owner}/{repo}/comments"],
    listCommitStatusesForRef: [
      "GET /repos/{owner}/{repo}/commits/{ref}/statuses"
    ],
    listCommits: ["GET /repos/{owner}/{repo}/commits"],
    listContributors: ["GET /repos/{owner}/{repo}/contributors"],
    listCustomDeploymentRuleIntegrations: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules/apps"
    ],
    listDeployKeys: ["GET /repos/{owner}/{repo}/keys"],
    listDeploymentBranchPolicies: [
      "GET /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies"
    ],
    listDeploymentStatuses: [
      "GET /repos/{owner}/{repo}/deployments/{deployment_id}/statuses"
    ],
    listDeployments: ["GET /repos/{owner}/{repo}/deployments"],
    listForAuthenticatedUser: ["GET /user/repos"],
    listForOrg: ["GET /orgs/{org}/repos"],
    listForUser: ["GET /users/{username}/repos"],
    listForks: ["GET /repos/{owner}/{repo}/forks"],
    listInvitations: ["GET /repos/{owner}/{repo}/invitations"],
    listInvitationsForAuthenticatedUser: ["GET /user/repository_invitations"],
    listLanguages: ["GET /repos/{owner}/{repo}/languages"],
    listPagesBuilds: ["GET /repos/{owner}/{repo}/pages/builds"],
    listPublic: ["GET /repositories"],
    listPullRequestsAssociatedWithCommit: [
      "GET /repos/{owner}/{repo}/commits/{commit_sha}/pulls"
    ],
    listReleaseAssets: [
      "GET /repos/{owner}/{repo}/releases/{release_id}/assets"
    ],
    listReleases: ["GET /repos/{owner}/{repo}/releases"],
    listTags: ["GET /repos/{owner}/{repo}/tags"],
    listTeams: ["GET /repos/{owner}/{repo}/teams"],
    listWebhookDeliveries: [
      "GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries"
    ],
    listWebhooks: ["GET /repos/{owner}/{repo}/hooks"],
    merge: ["POST /repos/{owner}/{repo}/merges"],
    mergeUpstream: ["POST /repos/{owner}/{repo}/merge-upstream"],
    pingWebhook: ["POST /repos/{owner}/{repo}/hooks/{hook_id}/pings"],
    redeliverWebhookDelivery: [
      "POST /repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}/attempts"
    ],
    removeAppAccessRestrictions: [
      "DELETE /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/apps",
      {},
      { mapToData: "apps" }
    ],
    removeCollaborator: [
      "DELETE /repos/{owner}/{repo}/collaborators/{username}"
    ],
    removeStatusCheckContexts: [
      "DELETE /repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks/contexts",
      {},
      { mapToData: "contexts" }
    ],
    removeStatusCheckProtection: [
      "DELETE /repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks"
    ],
    removeTeamAccessRestrictions: [
      "DELETE /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/teams",
      {},
      { mapToData: "teams" }
    ],
    removeUserAccessRestrictions: [
      "DELETE /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/users",
      {},
      { mapToData: "users" }
    ],
    renameBranch: ["POST /repos/{owner}/{repo}/branches/{branch}/rename"],
    replaceAllTopics: ["PUT /repos/{owner}/{repo}/topics"],
    requestPagesBuild: ["POST /repos/{owner}/{repo}/pages/builds"],
    setAdminBranchProtection: [
      "POST /repos/{owner}/{repo}/branches/{branch}/protection/enforce_admins"
    ],
    setAppAccessRestrictions: [
      "PUT /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/apps",
      {},
      { mapToData: "apps" }
    ],
    setStatusCheckContexts: [
      "PUT /repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks/contexts",
      {},
      { mapToData: "contexts" }
    ],
    setTeamAccessRestrictions: [
      "PUT /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/teams",
      {},
      { mapToData: "teams" }
    ],
    setUserAccessRestrictions: [
      "PUT /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/users",
      {},
      { mapToData: "users" }
    ],
    testPushWebhook: ["POST /repos/{owner}/{repo}/hooks/{hook_id}/tests"],
    transfer: ["POST /repos/{owner}/{repo}/transfer"],
    update: ["PATCH /repos/{owner}/{repo}"],
    updateBranchProtection: [
      "PUT /repos/{owner}/{repo}/branches/{branch}/protection"
    ],
    updateCommitComment: ["PATCH /repos/{owner}/{repo}/comments/{comment_id}"],
    updateDeploymentBranchPolicy: [
      "PUT /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies/{branch_policy_id}"
    ],
    updateInformationAboutPagesSite: ["PUT /repos/{owner}/{repo}/pages"],
    updateInvitation: [
      "PATCH /repos/{owner}/{repo}/invitations/{invitation_id}"
    ],
    updateOrgRuleset: ["PUT /orgs/{org}/rulesets/{ruleset_id}"],
    updatePullRequestReviewProtection: [
      "PATCH /repos/{owner}/{repo}/branches/{branch}/protection/required_pull_request_reviews"
    ],
    updateRelease: ["PATCH /repos/{owner}/{repo}/releases/{release_id}"],
    updateReleaseAsset: [
      "PATCH /repos/{owner}/{repo}/releases/assets/{asset_id}"
    ],
    updateRepoRuleset: ["PUT /repos/{owner}/{repo}/rulesets/{ruleset_id}"],
    updateStatusCheckPotection: [
      "PATCH /repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks",
      {},
      { renamed: ["repos", "updateStatusCheckProtection"] }
    ],
    updateStatusCheckProtection: [
      "PATCH /repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks"
    ],
    updateWebhook: ["PATCH /repos/{owner}/{repo}/hooks/{hook_id}"],
    updateWebhookConfigForRepo: [
      "PATCH /repos/{owner}/{repo}/hooks/{hook_id}/config"
    ],
    uploadReleaseAsset: [
      "POST /repos/{owner}/{repo}/releases/{release_id}/assets{?name,label}",
      { baseUrl: "https://uploads.github.com" }
    ]
  },
  search: {
    code: ["GET /search/code"],
    commits: ["GET /search/commits"],
    issuesAndPullRequests: ["GET /search/issues"],
    labels: ["GET /search/labels"],
    repos: ["GET /search/repositories"],
    topics: ["GET /search/topics"],
    users: ["GET /search/users"]
  },
  secretScanning: {
    createPushProtectionBypass: [
      "POST /repos/{owner}/{repo}/secret-scanning/push-protection-bypasses"
    ],
    getAlert: [
      "GET /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}"
    ],
    getScanHistory: ["GET /repos/{owner}/{repo}/secret-scanning/scan-history"],
    listAlertsForOrg: ["GET /orgs/{org}/secret-scanning/alerts"],
    listAlertsForRepo: ["GET /repos/{owner}/{repo}/secret-scanning/alerts"],
    listLocationsForAlert: [
      "GET /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}/locations"
    ],
    listOrgPatternConfigs: [
      "GET /orgs/{org}/secret-scanning/pattern-configurations"
    ],
    updateAlert: [
      "PATCH /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}"
    ],
    updateOrgPatternConfigs: [
      "PATCH /orgs/{org}/secret-scanning/pattern-configurations"
    ]
  },
  securityAdvisories: {
    createFork: [
      "POST /repos/{owner}/{repo}/security-advisories/{ghsa_id}/forks"
    ],
    createPrivateVulnerabilityReport: [
      "POST /repos/{owner}/{repo}/security-advisories/reports"
    ],
    createRepositoryAdvisory: [
      "POST /repos/{owner}/{repo}/security-advisories"
    ],
    createRepositoryAdvisoryCveRequest: [
      "POST /repos/{owner}/{repo}/security-advisories/{ghsa_id}/cve"
    ],
    getGlobalAdvisory: ["GET /advisories/{ghsa_id}"],
    getRepositoryAdvisory: [
      "GET /repos/{owner}/{repo}/security-advisories/{ghsa_id}"
    ],
    listGlobalAdvisories: ["GET /advisories"],
    listOrgRepositoryAdvisories: ["GET /orgs/{org}/security-advisories"],
    listRepositoryAdvisories: ["GET /repos/{owner}/{repo}/security-advisories"],
    updateRepositoryAdvisory: [
      "PATCH /repos/{owner}/{repo}/security-advisories/{ghsa_id}"
    ]
  },
  teams: {
    addOrUpdateMembershipForUserInOrg: [
      "PUT /orgs/{org}/teams/{team_slug}/memberships/{username}"
    ],
    addOrUpdateRepoPermissionsInOrg: [
      "PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}"
    ],
    checkPermissionsForRepoInOrg: [
      "GET /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}"
    ],
    create: ["POST /orgs/{org}/teams"],
    createDiscussionCommentInOrg: [
      "POST /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments"
    ],
    createDiscussionInOrg: ["POST /orgs/{org}/teams/{team_slug}/discussions"],
    deleteDiscussionCommentInOrg: [
      "DELETE /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments/{comment_number}"
    ],
    deleteDiscussionInOrg: [
      "DELETE /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}"
    ],
    deleteInOrg: ["DELETE /orgs/{org}/teams/{team_slug}"],
    getByName: ["GET /orgs/{org}/teams/{team_slug}"],
    getDiscussionCommentInOrg: [
      "GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments/{comment_number}"
    ],
    getDiscussionInOrg: [
      "GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}"
    ],
    getMembershipForUserInOrg: [
      "GET /orgs/{org}/teams/{team_slug}/memberships/{username}"
    ],
    list: ["GET /orgs/{org}/teams"],
    listChildInOrg: ["GET /orgs/{org}/teams/{team_slug}/teams"],
    listDiscussionCommentsInOrg: [
      "GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments"
    ],
    listDiscussionsInOrg: ["GET /orgs/{org}/teams/{team_slug}/discussions"],
    listForAuthenticatedUser: ["GET /user/teams"],
    listMembersInOrg: ["GET /orgs/{org}/teams/{team_slug}/members"],
    listPendingInvitationsInOrg: [
      "GET /orgs/{org}/teams/{team_slug}/invitations"
    ],
    listReposInOrg: ["GET /orgs/{org}/teams/{team_slug}/repos"],
    removeMembershipForUserInOrg: [
      "DELETE /orgs/{org}/teams/{team_slug}/memberships/{username}"
    ],
    removeRepoInOrg: [
      "DELETE /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}"
    ],
    updateDiscussionCommentInOrg: [
      "PATCH /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments/{comment_number}"
    ],
    updateDiscussionInOrg: [
      "PATCH /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}"
    ],
    updateInOrg: ["PATCH /orgs/{org}/teams/{team_slug}"]
  },
  users: {
    addEmailForAuthenticated: [
      "POST /user/emails",
      {},
      { renamed: ["users", "addEmailForAuthenticatedUser"] }
    ],
    addEmailForAuthenticatedUser: ["POST /user/emails"],
    addSocialAccountForAuthenticatedUser: ["POST /user/social_accounts"],
    block: ["PUT /user/blocks/{username}"],
    checkBlocked: ["GET /user/blocks/{username}"],
    checkFollowingForUser: ["GET /users/{username}/following/{target_user}"],
    checkPersonIsFollowedByAuthenticated: ["GET /user/following/{username}"],
    createGpgKeyForAuthenticated: [
      "POST /user/gpg_keys",
      {},
      { renamed: ["users", "createGpgKeyForAuthenticatedUser"] }
    ],
    createGpgKeyForAuthenticatedUser: ["POST /user/gpg_keys"],
    createPublicSshKeyForAuthenticated: [
      "POST /user/keys",
      {},
      { renamed: ["users", "createPublicSshKeyForAuthenticatedUser"] }
    ],
    createPublicSshKeyForAuthenticatedUser: ["POST /user/keys"],
    createSshSigningKeyForAuthenticatedUser: ["POST /user/ssh_signing_keys"],
    deleteAttestationsBulk: [
      "POST /users/{username}/attestations/delete-request"
    ],
    deleteAttestationsById: [
      "DELETE /users/{username}/attestations/{attestation_id}"
    ],
    deleteAttestationsBySubjectDigest: [
      "DELETE /users/{username}/attestations/digest/{subject_digest}"
    ],
    deleteEmailForAuthenticated: [
      "DELETE /user/emails",
      {},
      { renamed: ["users", "deleteEmailForAuthenticatedUser"] }
    ],
    deleteEmailForAuthenticatedUser: ["DELETE /user/emails"],
    deleteGpgKeyForAuthenticated: [
      "DELETE /user/gpg_keys/{gpg_key_id}",
      {},
      { renamed: ["users", "deleteGpgKeyForAuthenticatedUser"] }
    ],
    deleteGpgKeyForAuthenticatedUser: ["DELETE /user/gpg_keys/{gpg_key_id}"],
    deletePublicSshKeyForAuthenticated: [
      "DELETE /user/keys/{key_id}",
      {},
      { renamed: ["users", "deletePublicSshKeyForAuthenticatedUser"] }
    ],
    deletePublicSshKeyForAuthenticatedUser: ["DELETE /user/keys/{key_id}"],
    deleteSocialAccountForAuthenticatedUser: ["DELETE /user/social_accounts"],
    deleteSshSigningKeyForAuthenticatedUser: [
      "DELETE /user/ssh_signing_keys/{ssh_signing_key_id}"
    ],
    follow: ["PUT /user/following/{username}"],
    getAuthenticated: ["GET /user"],
    getById: ["GET /user/{account_id}"],
    getByUsername: ["GET /users/{username}"],
    getContextForUser: ["GET /users/{username}/hovercard"],
    getGpgKeyForAuthenticated: [
      "GET /user/gpg_keys/{gpg_key_id}",
      {},
      { renamed: ["users", "getGpgKeyForAuthenticatedUser"] }
    ],
    getGpgKeyForAuthenticatedUser: ["GET /user/gpg_keys/{gpg_key_id}"],
    getPublicSshKeyForAuthenticated: [
      "GET /user/keys/{key_id}",
      {},
      { renamed: ["users", "getPublicSshKeyForAuthenticatedUser"] }
    ],
    getPublicSshKeyForAuthenticatedUser: ["GET /user/keys/{key_id}"],
    getSshSigningKeyForAuthenticatedUser: [
      "GET /user/ssh_signing_keys/{ssh_signing_key_id}"
    ],
    list: ["GET /users"],
    listAttestations: ["GET /users/{username}/attestations/{subject_digest}"],
    listAttestationsBulk: [
      "POST /users/{username}/attestations/bulk-list{?per_page,before,after}"
    ],
    listBlockedByAuthenticated: [
      "GET /user/blocks",
      {},
      { renamed: ["users", "listBlockedByAuthenticatedUser"] }
    ],
    listBlockedByAuthenticatedUser: ["GET /user/blocks"],
    listEmailsForAuthenticated: [
      "GET /user/emails",
      {},
      { renamed: ["users", "listEmailsForAuthenticatedUser"] }
    ],
    listEmailsForAuthenticatedUser: ["GET /user/emails"],
    listFollowedByAuthenticated: [
      "GET /user/following",
      {},
      { renamed: ["users", "listFollowedByAuthenticatedUser"] }
    ],
    listFollowedByAuthenticatedUser: ["GET /user/following"],
    listFollowersForAuthenticatedUser: ["GET /user/followers"],
    listFollowersForUser: ["GET /users/{username}/followers"],
    listFollowingForUser: ["GET /users/{username}/following"],
    listGpgKeysForAuthenticated: [
      "GET /user/gpg_keys",
      {},
      { renamed: ["users", "listGpgKeysForAuthenticatedUser"] }
    ],
    listGpgKeysForAuthenticatedUser: ["GET /user/gpg_keys"],
    listGpgKeysForUser: ["GET /users/{username}/gpg_keys"],
    listPublicEmailsForAuthenticated: [
      "GET /user/public_emails",
      {},
      { renamed: ["users", "listPublicEmailsForAuthenticatedUser"] }
    ],
    listPublicEmailsForAuthenticatedUser: ["GET /user/public_emails"],
    listPublicKeysForUser: ["GET /users/{username}/keys"],
    listPublicSshKeysForAuthenticated: [
      "GET /user/keys",
      {},
      { renamed: ["users", "listPublicSshKeysForAuthenticatedUser"] }
    ],
    listPublicSshKeysForAuthenticatedUser: ["GET /user/keys"],
    listSocialAccountsForAuthenticatedUser: ["GET /user/social_accounts"],
    listSocialAccountsForUser: ["GET /users/{username}/social_accounts"],
    listSshSigningKeysForAuthenticatedUser: ["GET /user/ssh_signing_keys"],
    listSshSigningKeysForUser: ["GET /users/{username}/ssh_signing_keys"],
    setPrimaryEmailVisibilityForAuthenticated: [
      "PATCH /user/email/visibility",
      {},
      { renamed: ["users", "setPrimaryEmailVisibilityForAuthenticatedUser"] }
    ],
    setPrimaryEmailVisibilityForAuthenticatedUser: [
      "PATCH /user/email/visibility"
    ],
    unblock: ["DELETE /user/blocks/{username}"],
    unfollow: ["DELETE /user/following/{username}"],
    updateAuthenticated: ["PATCH /user"]
  }
};
var endpoints_default = Endpoints;

//# sourceMappingURL=endpoints.js.map

;// CONCATENATED MODULE: ./node_modules/@octokit/plugin-rest-endpoint-methods/dist-src/endpoints-to-methods.js

const endpointMethodsMap = /* @__PURE__ */ new Map();
for (const [scope, endpoints] of Object.entries(endpoints_default)) {
  for (const [methodName, endpoint] of Object.entries(endpoints)) {
    const [route, defaults, decorations] = endpoint;
    const [method, url] = route.split(/ /);
    const endpointDefaults = Object.assign(
      {
        method,
        url
      },
      defaults
    );
    if (!endpointMethodsMap.has(scope)) {
      endpointMethodsMap.set(scope, /* @__PURE__ */ new Map());
    }
    endpointMethodsMap.get(scope).set(methodName, {
      scope,
      methodName,
      endpointDefaults,
      decorations
    });
  }
}
const handler = {
  has({ scope }, methodName) {
    return endpointMethodsMap.get(scope).has(methodName);
  },
  getOwnPropertyDescriptor(target, methodName) {
    return {
      value: this.get(target, methodName),
      // ensures method is in the cache
      configurable: true,
      writable: true,
      enumerable: true
    };
  },
  defineProperty(target, methodName, descriptor) {
    Object.defineProperty(target.cache, methodName, descriptor);
    return true;
  },
  deleteProperty(target, methodName) {
    delete target.cache[methodName];
    return true;
  },
  ownKeys({ scope }) {
    return [...endpointMethodsMap.get(scope).keys()];
  },
  set(target, methodName, value) {
    return target.cache[methodName] = value;
  },
  get({ octokit, scope, cache }, methodName) {
    if (cache[methodName]) {
      return cache[methodName];
    }
    const method = endpointMethodsMap.get(scope).get(methodName);
    if (!method) {
      return void 0;
    }
    const { endpointDefaults, decorations } = method;
    if (decorations) {
      cache[methodName] = decorate(
        octokit,
        scope,
        methodName,
        endpointDefaults,
        decorations
      );
    } else {
      cache[methodName] = octokit.request.defaults(endpointDefaults);
    }
    return cache[methodName];
  }
};
function endpointsToMethods(octokit) {
  const newMethods = {};
  for (const scope of endpointMethodsMap.keys()) {
    newMethods[scope] = new Proxy({ octokit, scope, cache: {} }, handler);
  }
  return newMethods;
}
function decorate(octokit, scope, methodName, defaults, decorations) {
  const requestWithDefaults = octokit.request.defaults(defaults);
  function withDecorations(...args) {
    let options = requestWithDefaults.endpoint.merge(...args);
    if (decorations.mapToData) {
      options = Object.assign({}, options, {
        data: options[decorations.mapToData],
        [decorations.mapToData]: void 0
      });
      return requestWithDefaults(options);
    }
    if (decorations.renamed) {
      const [newScope, newMethodName] = decorations.renamed;
      octokit.log.warn(
        `octokit.${scope}.${methodName}() has been renamed to octokit.${newScope}.${newMethodName}()`
      );
    }
    if (decorations.deprecated) {
      octokit.log.warn(decorations.deprecated);
    }
    if (decorations.renamedParameters) {
      const options2 = requestWithDefaults.endpoint.merge(...args);
      for (const [name, alias] of Object.entries(
        decorations.renamedParameters
      )) {
        if (name in options2) {
          octokit.log.warn(
            `"${name}" parameter is deprecated for "octokit.${scope}.${methodName}()". Use "${alias}" instead`
          );
          if (!(alias in options2)) {
            options2[alias] = options2[name];
          }
          delete options2[name];
        }
      }
      return requestWithDefaults(options2);
    }
    return requestWithDefaults(...args);
  }
  return Object.assign(withDecorations, requestWithDefaults);
}

//# sourceMappingURL=endpoints-to-methods.js.map

;// CONCATENATED MODULE: ./node_modules/@octokit/plugin-rest-endpoint-methods/dist-src/index.js


function restEndpointMethods(octokit) {
  const api = endpointsToMethods(octokit);
  return {
    rest: api
  };
}
restEndpointMethods.VERSION = dist_src_version_VERSION;
function legacyRestEndpointMethods(octokit) {
  const api = endpointsToMethods(octokit);
  return {
    ...api,
    rest: api
  };
}
legacyRestEndpointMethods.VERSION = dist_src_version_VERSION;

//# sourceMappingURL=index.js.map

;// CONCATENATED MODULE: ./node_modules/@octokit/plugin-paginate-rest/dist-bundle/index.js
// pkg/dist-src/version.js
var plugin_paginate_rest_dist_bundle_VERSION = "0.0.0-development";

// pkg/dist-src/normalize-paginated-list-response.js
function normalizePaginatedListResponse(response) {
  if (!response.data) {
    return {
      ...response,
      data: []
    };
  }
  const responseNeedsNormalization = ("total_count" in response.data || "total_commits" in response.data) && !("url" in response.data);
  if (!responseNeedsNormalization) return response;
  const incompleteResults = response.data.incomplete_results;
  const repositorySelection = response.data.repository_selection;
  const totalCount = response.data.total_count;
  const totalCommits = response.data.total_commits;
  delete response.data.incomplete_results;
  delete response.data.repository_selection;
  delete response.data.total_count;
  delete response.data.total_commits;
  const namespaceKey = Object.keys(response.data)[0];
  const data = response.data[namespaceKey];
  response.data = data;
  if (typeof incompleteResults !== "undefined") {
    response.data.incomplete_results = incompleteResults;
  }
  if (typeof repositorySelection !== "undefined") {
    response.data.repository_selection = repositorySelection;
  }
  response.data.total_count = totalCount;
  response.data.total_commits = totalCommits;
  return response;
}

// pkg/dist-src/iterator.js
function iterator(octokit, route, parameters) {
  const options = typeof route === "function" ? route.endpoint(parameters) : octokit.request.endpoint(route, parameters);
  const requestMethod = typeof route === "function" ? route : octokit.request;
  const method = options.method;
  const headers = options.headers;
  let url = options.url;
  return {
    [Symbol.asyncIterator]: () => ({
      async next() {
        if (!url) return { done: true };
        try {
          const response = await requestMethod({ method, url, headers });
          const normalizedResponse = normalizePaginatedListResponse(response);
          url = ((normalizedResponse.headers.link || "").match(
            /<([^<>]+)>;\s*rel="next"/
          ) || [])[1];
          if (!url && "total_commits" in normalizedResponse.data) {
            const parsedUrl = new URL(normalizedResponse.url);
            const params = parsedUrl.searchParams;
            const page = parseInt(params.get("page") || "1", 10);
            const per_page = parseInt(params.get("per_page") || "250", 10);
            if (page * per_page < normalizedResponse.data.total_commits) {
              params.set("page", String(page + 1));
              url = parsedUrl.toString();
            }
          }
          return { value: normalizedResponse };
        } catch (error) {
          if (error.status !== 409) throw error;
          url = "";
          return {
            value: {
              status: 200,
              headers: {},
              data: []
            }
          };
        }
      }
    })
  };
}

// pkg/dist-src/paginate.js
function paginate(octokit, route, parameters, mapFn) {
  if (typeof parameters === "function") {
    mapFn = parameters;
    parameters = void 0;
  }
  return gather(
    octokit,
    [],
    iterator(octokit, route, parameters)[Symbol.asyncIterator](),
    mapFn
  );
}
function gather(octokit, results, iterator2, mapFn) {
  return iterator2.next().then((result) => {
    if (result.done) {
      return results;
    }
    let earlyExit = false;
    function done() {
      earlyExit = true;
    }
    results = results.concat(
      mapFn ? mapFn(result.value, done) : result.value.data
    );
    if (earlyExit) {
      return results;
    }
    return gather(octokit, results, iterator2, mapFn);
  });
}

// pkg/dist-src/compose-paginate.js
var composePaginateRest = Object.assign(paginate, {
  iterator
});

// pkg/dist-src/generated/paginating-endpoints.js
var paginatingEndpoints = (/* unused pure expression or super */ null && ([
  "GET /advisories",
  "GET /app/hook/deliveries",
  "GET /app/installation-requests",
  "GET /app/installations",
  "GET /assignments/{assignment_id}/accepted_assignments",
  "GET /classrooms",
  "GET /classrooms/{classroom_id}/assignments",
  "GET /enterprises/{enterprise}/code-security/configurations",
  "GET /enterprises/{enterprise}/code-security/configurations/{configuration_id}/repositories",
  "GET /enterprises/{enterprise}/dependabot/alerts",
  "GET /enterprises/{enterprise}/teams",
  "GET /enterprises/{enterprise}/teams/{enterprise-team}/memberships",
  "GET /enterprises/{enterprise}/teams/{enterprise-team}/organizations",
  "GET /events",
  "GET /gists",
  "GET /gists/public",
  "GET /gists/starred",
  "GET /gists/{gist_id}/comments",
  "GET /gists/{gist_id}/commits",
  "GET /gists/{gist_id}/forks",
  "GET /installation/repositories",
  "GET /issues",
  "GET /licenses",
  "GET /marketplace_listing/plans",
  "GET /marketplace_listing/plans/{plan_id}/accounts",
  "GET /marketplace_listing/stubbed/plans",
  "GET /marketplace_listing/stubbed/plans/{plan_id}/accounts",
  "GET /networks/{owner}/{repo}/events",
  "GET /notifications",
  "GET /organizations",
  "GET /organizations/{org}/dependabot/repository-access",
  "GET /orgs/{org}/actions/cache/usage-by-repository",
  "GET /orgs/{org}/actions/hosted-runners",
  "GET /orgs/{org}/actions/permissions/repositories",
  "GET /orgs/{org}/actions/permissions/self-hosted-runners/repositories",
  "GET /orgs/{org}/actions/runner-groups",
  "GET /orgs/{org}/actions/runner-groups/{runner_group_id}/hosted-runners",
  "GET /orgs/{org}/actions/runner-groups/{runner_group_id}/repositories",
  "GET /orgs/{org}/actions/runner-groups/{runner_group_id}/runners",
  "GET /orgs/{org}/actions/runners",
  "GET /orgs/{org}/actions/secrets",
  "GET /orgs/{org}/actions/secrets/{secret_name}/repositories",
  "GET /orgs/{org}/actions/variables",
  "GET /orgs/{org}/actions/variables/{name}/repositories",
  "GET /orgs/{org}/attestations/repositories",
  "GET /orgs/{org}/attestations/{subject_digest}",
  "GET /orgs/{org}/blocks",
  "GET /orgs/{org}/campaigns",
  "GET /orgs/{org}/code-scanning/alerts",
  "GET /orgs/{org}/code-security/configurations",
  "GET /orgs/{org}/code-security/configurations/{configuration_id}/repositories",
  "GET /orgs/{org}/codespaces",
  "GET /orgs/{org}/codespaces/secrets",
  "GET /orgs/{org}/codespaces/secrets/{secret_name}/repositories",
  "GET /orgs/{org}/copilot/billing/seats",
  "GET /orgs/{org}/copilot/metrics",
  "GET /orgs/{org}/dependabot/alerts",
  "GET /orgs/{org}/dependabot/secrets",
  "GET /orgs/{org}/dependabot/secrets/{secret_name}/repositories",
  "GET /orgs/{org}/events",
  "GET /orgs/{org}/failed_invitations",
  "GET /orgs/{org}/hooks",
  "GET /orgs/{org}/hooks/{hook_id}/deliveries",
  "GET /orgs/{org}/insights/api/route-stats/{actor_type}/{actor_id}",
  "GET /orgs/{org}/insights/api/subject-stats",
  "GET /orgs/{org}/insights/api/user-stats/{user_id}",
  "GET /orgs/{org}/installations",
  "GET /orgs/{org}/invitations",
  "GET /orgs/{org}/invitations/{invitation_id}/teams",
  "GET /orgs/{org}/issues",
  "GET /orgs/{org}/members",
  "GET /orgs/{org}/members/{username}/codespaces",
  "GET /orgs/{org}/migrations",
  "GET /orgs/{org}/migrations/{migration_id}/repositories",
  "GET /orgs/{org}/organization-roles/{role_id}/teams",
  "GET /orgs/{org}/organization-roles/{role_id}/users",
  "GET /orgs/{org}/outside_collaborators",
  "GET /orgs/{org}/packages",
  "GET /orgs/{org}/packages/{package_type}/{package_name}/versions",
  "GET /orgs/{org}/personal-access-token-requests",
  "GET /orgs/{org}/personal-access-token-requests/{pat_request_id}/repositories",
  "GET /orgs/{org}/personal-access-tokens",
  "GET /orgs/{org}/personal-access-tokens/{pat_id}/repositories",
  "GET /orgs/{org}/private-registries",
  "GET /orgs/{org}/projects",
  "GET /orgs/{org}/projectsV2",
  "GET /orgs/{org}/projectsV2/{project_number}/fields",
  "GET /orgs/{org}/projectsV2/{project_number}/items",
  "GET /orgs/{org}/properties/values",
  "GET /orgs/{org}/public_members",
  "GET /orgs/{org}/repos",
  "GET /orgs/{org}/rulesets",
  "GET /orgs/{org}/rulesets/rule-suites",
  "GET /orgs/{org}/rulesets/{ruleset_id}/history",
  "GET /orgs/{org}/secret-scanning/alerts",
  "GET /orgs/{org}/security-advisories",
  "GET /orgs/{org}/settings/immutable-releases/repositories",
  "GET /orgs/{org}/settings/network-configurations",
  "GET /orgs/{org}/team/{team_slug}/copilot/metrics",
  "GET /orgs/{org}/teams",
  "GET /orgs/{org}/teams/{team_slug}/discussions",
  "GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments",
  "GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments/{comment_number}/reactions",
  "GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/reactions",
  "GET /orgs/{org}/teams/{team_slug}/invitations",
  "GET /orgs/{org}/teams/{team_slug}/members",
  "GET /orgs/{org}/teams/{team_slug}/projects",
  "GET /orgs/{org}/teams/{team_slug}/repos",
  "GET /orgs/{org}/teams/{team_slug}/teams",
  "GET /projects/{project_id}/collaborators",
  "GET /repos/{owner}/{repo}/actions/artifacts",
  "GET /repos/{owner}/{repo}/actions/caches",
  "GET /repos/{owner}/{repo}/actions/organization-secrets",
  "GET /repos/{owner}/{repo}/actions/organization-variables",
  "GET /repos/{owner}/{repo}/actions/runners",
  "GET /repos/{owner}/{repo}/actions/runs",
  "GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts",
  "GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}/jobs",
  "GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
  "GET /repos/{owner}/{repo}/actions/secrets",
  "GET /repos/{owner}/{repo}/actions/variables",
  "GET /repos/{owner}/{repo}/actions/workflows",
  "GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
  "GET /repos/{owner}/{repo}/activity",
  "GET /repos/{owner}/{repo}/assignees",
  "GET /repos/{owner}/{repo}/attestations/{subject_digest}",
  "GET /repos/{owner}/{repo}/branches",
  "GET /repos/{owner}/{repo}/check-runs/{check_run_id}/annotations",
  "GET /repos/{owner}/{repo}/check-suites/{check_suite_id}/check-runs",
  "GET /repos/{owner}/{repo}/code-scanning/alerts",
  "GET /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/instances",
  "GET /repos/{owner}/{repo}/code-scanning/analyses",
  "GET /repos/{owner}/{repo}/codespaces",
  "GET /repos/{owner}/{repo}/codespaces/devcontainers",
  "GET /repos/{owner}/{repo}/codespaces/secrets",
  "GET /repos/{owner}/{repo}/collaborators",
  "GET /repos/{owner}/{repo}/comments",
  "GET /repos/{owner}/{repo}/comments/{comment_id}/reactions",
  "GET /repos/{owner}/{repo}/commits",
  "GET /repos/{owner}/{repo}/commits/{commit_sha}/comments",
  "GET /repos/{owner}/{repo}/commits/{commit_sha}/pulls",
  "GET /repos/{owner}/{repo}/commits/{ref}/check-runs",
  "GET /repos/{owner}/{repo}/commits/{ref}/check-suites",
  "GET /repos/{owner}/{repo}/commits/{ref}/status",
  "GET /repos/{owner}/{repo}/commits/{ref}/statuses",
  "GET /repos/{owner}/{repo}/compare/{basehead}",
  "GET /repos/{owner}/{repo}/compare/{base}...{head}",
  "GET /repos/{owner}/{repo}/contributors",
  "GET /repos/{owner}/{repo}/dependabot/alerts",
  "GET /repos/{owner}/{repo}/dependabot/secrets",
  "GET /repos/{owner}/{repo}/deployments",
  "GET /repos/{owner}/{repo}/deployments/{deployment_id}/statuses",
  "GET /repos/{owner}/{repo}/environments",
  "GET /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies",
  "GET /repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules/apps",
  "GET /repos/{owner}/{repo}/environments/{environment_name}/secrets",
  "GET /repos/{owner}/{repo}/environments/{environment_name}/variables",
  "GET /repos/{owner}/{repo}/events",
  "GET /repos/{owner}/{repo}/forks",
  "GET /repos/{owner}/{repo}/hooks",
  "GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries",
  "GET /repos/{owner}/{repo}/invitations",
  "GET /repos/{owner}/{repo}/issues",
  "GET /repos/{owner}/{repo}/issues/comments",
  "GET /repos/{owner}/{repo}/issues/comments/{comment_id}/reactions",
  "GET /repos/{owner}/{repo}/issues/events",
  "GET /repos/{owner}/{repo}/issues/{issue_number}/comments",
  "GET /repos/{owner}/{repo}/issues/{issue_number}/dependencies/blocked_by",
  "GET /repos/{owner}/{repo}/issues/{issue_number}/dependencies/blocking",
  "GET /repos/{owner}/{repo}/issues/{issue_number}/events",
  "GET /repos/{owner}/{repo}/issues/{issue_number}/labels",
  "GET /repos/{owner}/{repo}/issues/{issue_number}/reactions",
  "GET /repos/{owner}/{repo}/issues/{issue_number}/sub_issues",
  "GET /repos/{owner}/{repo}/issues/{issue_number}/timeline",
  "GET /repos/{owner}/{repo}/keys",
  "GET /repos/{owner}/{repo}/labels",
  "GET /repos/{owner}/{repo}/milestones",
  "GET /repos/{owner}/{repo}/milestones/{milestone_number}/labels",
  "GET /repos/{owner}/{repo}/notifications",
  "GET /repos/{owner}/{repo}/pages/builds",
  "GET /repos/{owner}/{repo}/projects",
  "GET /repos/{owner}/{repo}/pulls",
  "GET /repos/{owner}/{repo}/pulls/comments",
  "GET /repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions",
  "GET /repos/{owner}/{repo}/pulls/{pull_number}/comments",
  "GET /repos/{owner}/{repo}/pulls/{pull_number}/commits",
  "GET /repos/{owner}/{repo}/pulls/{pull_number}/files",
  "GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews",
  "GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/comments",
  "GET /repos/{owner}/{repo}/releases",
  "GET /repos/{owner}/{repo}/releases/{release_id}/assets",
  "GET /repos/{owner}/{repo}/releases/{release_id}/reactions",
  "GET /repos/{owner}/{repo}/rules/branches/{branch}",
  "GET /repos/{owner}/{repo}/rulesets",
  "GET /repos/{owner}/{repo}/rulesets/rule-suites",
  "GET /repos/{owner}/{repo}/rulesets/{ruleset_id}/history",
  "GET /repos/{owner}/{repo}/secret-scanning/alerts",
  "GET /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}/locations",
  "GET /repos/{owner}/{repo}/security-advisories",
  "GET /repos/{owner}/{repo}/stargazers",
  "GET /repos/{owner}/{repo}/subscribers",
  "GET /repos/{owner}/{repo}/tags",
  "GET /repos/{owner}/{repo}/teams",
  "GET /repos/{owner}/{repo}/topics",
  "GET /repositories",
  "GET /search/code",
  "GET /search/commits",
  "GET /search/issues",
  "GET /search/labels",
  "GET /search/repositories",
  "GET /search/topics",
  "GET /search/users",
  "GET /teams/{team_id}/discussions",
  "GET /teams/{team_id}/discussions/{discussion_number}/comments",
  "GET /teams/{team_id}/discussions/{discussion_number}/comments/{comment_number}/reactions",
  "GET /teams/{team_id}/discussions/{discussion_number}/reactions",
  "GET /teams/{team_id}/invitations",
  "GET /teams/{team_id}/members",
  "GET /teams/{team_id}/projects",
  "GET /teams/{team_id}/repos",
  "GET /teams/{team_id}/teams",
  "GET /user/blocks",
  "GET /user/codespaces",
  "GET /user/codespaces/secrets",
  "GET /user/emails",
  "GET /user/followers",
  "GET /user/following",
  "GET /user/gpg_keys",
  "GET /user/installations",
  "GET /user/installations/{installation_id}/repositories",
  "GET /user/issues",
  "GET /user/keys",
  "GET /user/marketplace_purchases",
  "GET /user/marketplace_purchases/stubbed",
  "GET /user/memberships/orgs",
  "GET /user/migrations",
  "GET /user/migrations/{migration_id}/repositories",
  "GET /user/orgs",
  "GET /user/packages",
  "GET /user/packages/{package_type}/{package_name}/versions",
  "GET /user/public_emails",
  "GET /user/repos",
  "GET /user/repository_invitations",
  "GET /user/social_accounts",
  "GET /user/ssh_signing_keys",
  "GET /user/starred",
  "GET /user/subscriptions",
  "GET /user/teams",
  "GET /users",
  "GET /users/{username}/attestations/{subject_digest}",
  "GET /users/{username}/events",
  "GET /users/{username}/events/orgs/{org}",
  "GET /users/{username}/events/public",
  "GET /users/{username}/followers",
  "GET /users/{username}/following",
  "GET /users/{username}/gists",
  "GET /users/{username}/gpg_keys",
  "GET /users/{username}/keys",
  "GET /users/{username}/orgs",
  "GET /users/{username}/packages",
  "GET /users/{username}/projects",
  "GET /users/{username}/projectsV2",
  "GET /users/{username}/projectsV2/{project_number}/fields",
  "GET /users/{username}/projectsV2/{project_number}/items",
  "GET /users/{username}/received_events",
  "GET /users/{username}/received_events/public",
  "GET /users/{username}/repos",
  "GET /users/{username}/social_accounts",
  "GET /users/{username}/ssh_signing_keys",
  "GET /users/{username}/starred",
  "GET /users/{username}/subscriptions"
]));

// pkg/dist-src/paginating-endpoints.js
function isPaginatingEndpoint(arg) {
  if (typeof arg === "string") {
    return paginatingEndpoints.includes(arg);
  } else {
    return false;
  }
}

// pkg/dist-src/index.js
function paginateRest(octokit) {
  return {
    paginate: Object.assign(paginate.bind(null, octokit), {
      iterator: iterator.bind(null, octokit)
    })
  };
}
paginateRest.VERSION = plugin_paginate_rest_dist_bundle_VERSION;


;// CONCATENATED MODULE: ./node_modules/@actions/github/lib/utils.js


// octokit + plugins



const utils_context = new Context();
const baseUrl = getApiBaseUrl();
const defaults = {
    baseUrl,
    request: {
        agent: getProxyAgent(baseUrl),
        fetch: getProxyFetch(baseUrl)
    }
};
const GitHub = Octokit.plugin(restEndpointMethods, paginateRest).defaults(defaults);
/**
 * Convience function to correctly format Octokit Options to pass into the constructor.
 *
 * @param     token    the repo PAT or GITHUB_TOKEN
 * @param     options  other options to set
 */
function getOctokitOptions(token, options) {
    const opts = Object.assign({}, options || {}); // Shallow clone - don't mutate the object provided by the caller
    // Auth
    const auth = getAuthString(token, opts);
    if (auth) {
        opts.auth = auth;
    }
    return opts;
}
//# sourceMappingURL=utils.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/github/lib/github.js


const github_context = new Context();
/**
 * Returns a hydrated octokit ready to use for GitHub Actions
 *
 * @param     token    the repo PAT or GITHUB_TOKEN
 * @param     options  other options to set
 */
function getOctokit(token, options, ...additionalPlugins) {
    const GitHubWithPlugins = GitHub.plugin(...additionalPlugins);
    return new GitHubWithPlugins(getOctokitOptions(token, options));
}
//# sourceMappingURL=github.js.map
// EXTERNAL MODULE: ./node_modules/unzip-stream/unzip.js
var unzip = __nccwpck_require__(3991);
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/download/download-artifact.js
var download_artifact_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};















const scrubQueryParameters = (url) => {
    const parsed = new URL(url);
    parsed.search = '';
    return parsed.toString();
};
function download_artifact_exists(path) {
    return download_artifact_awaiter(this, void 0, void 0, function* () {
        try {
            yield promises_namespaceObject.access(path);
            return true;
        }
        catch (error) {
            if (error.code === 'ENOENT') {
                return false;
            }
            else {
                throw error;
            }
        }
    });
}
function streamExtract(url, directory, skipDecompress) {
    return download_artifact_awaiter(this, void 0, void 0, function* () {
        let retryCount = 0;
        while (retryCount < 5) {
            try {
                return yield streamExtractExternal(url, directory, { skipDecompress });
            }
            catch (error) {
                retryCount++;
                core_debug(`Failed to download artifact after ${retryCount} retries due to ${error.message}. Retrying in 5 seconds...`);
                // wait 5 seconds before retrying
                yield new Promise(resolve => setTimeout(resolve, 5000));
            }
        }
        throw new Error(`Artifact download failed after ${retryCount} retries.`);
    });
}
function streamExtractExternal(url_1, directory_1) {
    return download_artifact_awaiter(this, arguments, void 0, function* (url, directory, opts = {}) {
        const { timeout = 30 * 1000, skipDecompress = false } = opts;
        const client = new lib_HttpClient(getUserAgentString());
        const response = yield client.get(url);
        if (response.message.statusCode !== 200) {
            throw new Error(`Unexpected HTTP response from blob storage: ${response.message.statusCode} ${response.message.statusMessage}`);
        }
        const contentType = response.message.headers['content-type'] || '';
        const mimeType = contentType.split(';', 1)[0].trim().toLowerCase();
        // Check if the URL path ends with .zip (ignoring query parameters)
        const urlPath = new URL(url).pathname.toLowerCase();
        const urlEndsWithZip = urlPath.endsWith('.zip');
        const isZip = mimeType === 'application/zip' ||
            mimeType === 'application/x-zip-compressed' ||
            mimeType === 'application/zip-compressed' ||
            urlEndsWithZip;
        // Extract filename from Content-Disposition header
        const contentDisposition = response.message.headers['content-disposition'] || '';
        let fileName = 'artifact';
        const filenameMatch = contentDisposition.match(/filename\*?=['"]?(?:UTF-\d['"]*)?([^;\r\n"']*)['"]?/i);
        if (filenameMatch && filenameMatch[1]) {
            // Sanitize fileName to prevent path traversal attacks
            // Use path.basename to extract only the filename component
            fileName = external_path_.basename(decodeURIComponent(filenameMatch[1].trim()));
        }
        core_debug(`Content-Type: ${contentType}, mimeType: ${mimeType}, urlEndsWithZip: ${urlEndsWithZip}, isZip: ${isZip}, skipDecompress: ${skipDecompress}`);
        core_debug(`Content-Disposition: ${contentDisposition}, fileName: ${fileName}`);
        let sha256Digest = undefined;
        return new Promise((resolve, reject) => {
            const timerFn = () => {
                const timeoutError = new Error(`Blob storage chunk did not respond in ${timeout}ms`);
                response.message.destroy(timeoutError);
                reject(timeoutError);
            };
            const timer = setTimeout(timerFn, timeout);
            const onError = (error) => {
                core_debug(`response.message: Artifact download failed: ${error.message}`);
                clearTimeout(timer);
                reject(error);
            };
            const hashStream = external_crypto_namespaceObject.createHash('sha256').setEncoding('hex');
            const passThrough = new external_stream_.PassThrough()
                .on('data', () => {
                timer.refresh();
            })
                .on('error', onError);
            response.message.pipe(passThrough);
            passThrough.pipe(hashStream);
            const onClose = () => {
                clearTimeout(timer);
                if (hashStream) {
                    hashStream.end();
                    sha256Digest = hashStream.read();
                    info(`SHA256 digest of downloaded artifact is ${sha256Digest}`);
                }
                resolve({ sha256Digest: `sha256:${sha256Digest}` });
            };
            if (isZip && !skipDecompress) {
                // Extract zip file
                passThrough
                    .pipe(unzip.Extract({ path: directory }))
                    .on('close', onClose)
                    .on('error', onError);
            }
            else {
                // Save raw file without extracting
                const filePath = external_path_.join(directory, fileName);
                const writeStream = external_fs_.createWriteStream(filePath);
                info(`Downloading raw file (non-zip) to: ${filePath}`);
                passThrough.pipe(writeStream).on('close', onClose).on('error', onError);
            }
        });
    });
}
function downloadArtifactPublic(artifactId, repositoryOwner, repositoryName, token, options) {
    return download_artifact_awaiter(this, void 0, void 0, function* () {
        const downloadPath = yield resolveOrCreateDirectory(options === null || options === void 0 ? void 0 : options.path);
        const api = getOctokit(token);
        let digestMismatch = false;
        info(`Downloading artifact '${artifactId}' from '${repositoryOwner}/${repositoryName}'`);
        const { headers, status } = yield api.rest.actions.downloadArtifact({
            owner: repositoryOwner,
            repo: repositoryName,
            artifact_id: artifactId,
            archive_format: 'zip',
            request: {
                redirect: 'manual'
            }
        });
        if (status !== 302) {
            throw new Error(`Unable to download artifact. Unexpected status: ${status}`);
        }
        const { location } = headers;
        if (!location) {
            throw new Error(`Unable to redirect to artifact download url`);
        }
        info(`Redirecting to blob download url: ${scrubQueryParameters(location)}`);
        try {
            info(`Starting download of artifact to: ${downloadPath}`);
            const extractResponse = yield streamExtract(location, downloadPath, options === null || options === void 0 ? void 0 : options.skipDecompress);
            info(`Artifact download completed successfully.`);
            if (options === null || options === void 0 ? void 0 : options.expectedHash) {
                if ((options === null || options === void 0 ? void 0 : options.expectedHash) !== extractResponse.sha256Digest) {
                    digestMismatch = true;
                    core_debug(`Computed digest: ${extractResponse.sha256Digest}`);
                    core_debug(`Expected digest: ${options.expectedHash}`);
                }
            }
        }
        catch (error) {
            throw new Error(`Unable to download and extract artifact: ${error.message}`);
        }
        return { downloadPath, digestMismatch };
    });
}
function downloadArtifactInternal(artifactId, options) {
    return download_artifact_awaiter(this, void 0, void 0, function* () {
        const downloadPath = yield resolveOrCreateDirectory(options === null || options === void 0 ? void 0 : options.path);
        const artifactClient = internalArtifactTwirpClient();
        let digestMismatch = false;
        const { workflowRunBackendId, workflowJobRunBackendId } = getBackendIdsFromToken();
        const listReq = {
            workflowRunBackendId,
            workflowJobRunBackendId,
            idFilter: Int64Value.create({ value: artifactId.toString() })
        };
        const { artifacts } = yield artifactClient.ListArtifacts(listReq);
        if (artifacts.length === 0) {
            throw new ArtifactNotFoundError(`No artifacts found for ID: ${artifactId}\nAre you trying to download from a different run? Try specifying a github-token with \`actions:read\` scope.`);
        }
        if (artifacts.length > 1) {
            warning('Multiple artifacts found, defaulting to first.');
        }
        const signedReq = {
            workflowRunBackendId: artifacts[0].workflowRunBackendId,
            workflowJobRunBackendId: artifacts[0].workflowJobRunBackendId,
            name: artifacts[0].name
        };
        const { signedUrl } = yield artifactClient.GetSignedArtifactURL(signedReq);
        info(`Redirecting to blob download url: ${scrubQueryParameters(signedUrl)}`);
        try {
            info(`Starting download of artifact to: ${downloadPath}`);
            const extractResponse = yield streamExtract(signedUrl, downloadPath, options === null || options === void 0 ? void 0 : options.skipDecompress);
            info(`Artifact download completed successfully.`);
            if (options === null || options === void 0 ? void 0 : options.expectedHash) {
                if ((options === null || options === void 0 ? void 0 : options.expectedHash) !== extractResponse.sha256Digest) {
                    digestMismatch = true;
                    core_debug(`Computed digest: ${extractResponse.sha256Digest}`);
                    core_debug(`Expected digest: ${options.expectedHash}`);
                }
            }
        }
        catch (error) {
            throw new Error(`Unable to download and extract artifact: ${error.message}`);
        }
        return { downloadPath, digestMismatch };
    });
}
function resolveOrCreateDirectory() {
    return download_artifact_awaiter(this, arguments, void 0, function* (downloadPath = getGitHubWorkspaceDir()) {
        if (!(yield download_artifact_exists(downloadPath))) {
            core_debug(`Artifact destination folder does not exist, creating: ${downloadPath}`);
            yield promises_namespaceObject.mkdir(downloadPath, { recursive: true });
        }
        else {
            core_debug(`Artifact destination folder already exists: ${downloadPath}`);
        }
        return downloadPath;
    });
}
//# sourceMappingURL=download-artifact.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/find/retry-options.js

// Defaults for fetching artifacts
const defaultMaxRetryNumber = 5;
const defaultExemptStatusCodes = [400, 401, 403, 404, 422]; // https://github.com/octokit/plugin-retry.js/blob/9a2443746c350b3beedec35cf26e197ea318a261/src/index.ts#L14
function getRetryOptions(defaultOptions, retries = defaultMaxRetryNumber, exemptStatusCodes = defaultExemptStatusCodes) {
    var _a;
    if (retries <= 0) {
        return [{ enabled: false }, defaultOptions.request];
    }
    const retryOptions = {
        enabled: true
    };
    if (exemptStatusCodes.length > 0) {
        retryOptions.doNotRetry = exemptStatusCodes;
    }
    // The GitHub type has some defaults for `options.request`
    // see: https://github.com/actions/toolkit/blob/4fbc5c941a57249b19562015edbd72add14be93d/packages/github/src/utils.ts#L15
    // We pass these in here so they are not overridden.
    const requestOptions = Object.assign(Object.assign({}, defaultOptions.request), { retries });
    core_debug(`GitHub client configured with: (retries: ${requestOptions.retries}, retry-exempt-status-code: ${(_a = retryOptions.doNotRetry) !== null && _a !== void 0 ? _a : 'octokit default: [400, 401, 403, 404, 422]'})`);
    return [retryOptions, requestOptions];
}
//# sourceMappingURL=retry-options.js.map
;// CONCATENATED MODULE: ./node_modules/@octokit/plugin-request-log/dist-src/version.js
const plugin_request_log_dist_src_version_VERSION = "6.0.0";


;// CONCATENATED MODULE: ./node_modules/@octokit/plugin-request-log/dist-src/index.js

function requestLog(octokit) {
  octokit.hook.wrap("request", (request, options) => {
    octokit.log.debug("request", options);
    const start = Date.now();
    const requestOptions = octokit.request.endpoint.parse(options);
    const path = requestOptions.url.replace(options.baseUrl, "");
    return request(options).then((response) => {
      const requestId = response.headers["x-github-request-id"];
      octokit.log.info(
        `${requestOptions.method} ${path} - ${response.status} with id ${requestId} in ${Date.now() - start}ms`
      );
      return response;
    }).catch((error) => {
      const requestId = error.response?.headers["x-github-request-id"] || "UNKNOWN";
      octokit.log.error(
        `${requestOptions.method} ${path} - ${error.status} with id ${requestId} in ${Date.now() - start}ms`
      );
      throw error;
    });
  });
}
requestLog.VERSION = plugin_request_log_dist_src_version_VERSION;


// EXTERNAL MODULE: ./node_modules/bottleneck/light.js
var light = __nccwpck_require__(3251);
;// CONCATENATED MODULE: ./node_modules/@octokit/plugin-retry/dist-bundle/index.js
// pkg/dist-src/version.js
var plugin_retry_dist_bundle_VERSION = "0.0.0-development";

// pkg/dist-src/error-request.js
function isRequestError(error) {
  return error.request !== void 0;
}
async function errorRequest(state, octokit, error, options) {
  if (!isRequestError(error) || !error?.request.request) {
    throw error;
  }
  if (error.status >= 400 && !state.doNotRetry.includes(error.status)) {
    const retries = options.request.retries != null ? options.request.retries : state.retries;
    const retryAfter = Math.pow((options.request.retryCount || 0) + 1, 2);
    throw octokit.retry.retryRequest(error, retries, retryAfter);
  }
  throw error;
}

// pkg/dist-src/wrap-request.js


async function wrapRequest(state, octokit, request, options) {
  const limiter = new light();
  limiter.on("failed", function(error, info) {
    const maxRetries = ~~error.request.request?.retries;
    const after = ~~error.request.request?.retryAfter;
    options.request.retryCount = info.retryCount + 1;
    if (maxRetries > info.retryCount) {
      return after * state.retryAfterBaseValue;
    }
  });
  return limiter.schedule(
    requestWithGraphqlErrorHandling.bind(null, state, octokit, request),
    options
  );
}
async function requestWithGraphqlErrorHandling(state, octokit, request, options) {
  const response = await request(options);
  if (response.data && response.data.errors && response.data.errors.length > 0 && /Something went wrong while executing your query/.test(
    response.data.errors[0].message
  )) {
    const error = new RequestError(response.data.errors[0].message, 500, {
      request: options,
      response
    });
    return errorRequest(state, octokit, error, options);
  }
  return response;
}

// pkg/dist-src/index.js
function retry(octokit, octokitOptions) {
  const state = Object.assign(
    {
      enabled: true,
      retryAfterBaseValue: 1e3,
      doNotRetry: [400, 401, 403, 404, 410, 422, 451],
      retries: 3
    },
    octokitOptions.retry
  );
  const retryPlugin = {
    retry: {
      retryRequest: (error, retries, retryAfter) => {
        error.request.request = Object.assign({}, error.request.request, {
          retries,
          retryAfter
        });
        return error;
      }
    }
  };
  if (state.enabled) {
    octokit.hook.error("request", errorRequest.bind(null, state, retryPlugin));
    octokit.hook.wrap("request", wrapRequest.bind(null, state, retryPlugin));
  }
  return retryPlugin;
}
retry.VERSION = plugin_retry_dist_bundle_VERSION;


;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/find/get-artifact.js
var get_artifact_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};











function getArtifactPublic(artifactName, workflowRunId, repositoryOwner, repositoryName, token) {
    return get_artifact_awaiter(this, void 0, void 0, function* () {
        var _a;
        const [retryOpts, requestOpts] = getRetryOptions(defaults);
        const opts = {
            log: undefined,
            userAgent: getUserAgentString(),
            previews: undefined,
            retry: retryOpts,
            request: requestOpts
        };
        const github = getOctokit(token, opts, retry, requestLog);
        const getArtifactResp = yield github.request('GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts{?name}', {
            owner: repositoryOwner,
            repo: repositoryName,
            run_id: workflowRunId,
            name: artifactName
        });
        if (getArtifactResp.status !== 200) {
            throw new InvalidResponseError(`Invalid response from GitHub API: ${getArtifactResp.status} (${(_a = getArtifactResp === null || getArtifactResp === void 0 ? void 0 : getArtifactResp.headers) === null || _a === void 0 ? void 0 : _a['x-github-request-id']})`);
        }
        if (getArtifactResp.data.artifacts.length === 0) {
            throw new ArtifactNotFoundError(`Artifact not found for name: ${artifactName}
        Please ensure that your artifact is not expired and the artifact was uploaded using a compatible version of toolkit/upload-artifact.
        For more information, visit the GitHub Artifacts FAQ: https://github.com/actions/toolkit/blob/main/packages/artifact/docs/faq.md`);
        }
        let artifact = getArtifactResp.data.artifacts[0];
        if (getArtifactResp.data.artifacts.length > 1) {
            artifact = getArtifactResp.data.artifacts.sort((a, b) => b.id - a.id)[0];
            core_debug(`More than one artifact found for a single name, returning newest (id: ${artifact.id})`);
        }
        return {
            artifact: {
                name: artifact.name,
                id: artifact.id,
                size: artifact.size_in_bytes,
                createdAt: artifact.created_at
                    ? new Date(artifact.created_at)
                    : undefined,
                digest: artifact.digest
            }
        };
    });
}
function getArtifactInternal(artifactName) {
    return get_artifact_awaiter(this, void 0, void 0, function* () {
        var _a;
        const artifactClient = internalArtifactTwirpClient();
        const { workflowRunBackendId, workflowJobRunBackendId } = getBackendIdsFromToken();
        const req = {
            workflowRunBackendId,
            workflowJobRunBackendId,
            nameFilter: StringValue.create({ value: artifactName })
        };
        const res = yield artifactClient.ListArtifacts(req);
        if (res.artifacts.length === 0) {
            throw new ArtifactNotFoundError(`Artifact not found for name: ${artifactName}
        Please ensure that your artifact is not expired and the artifact was uploaded using a compatible version of toolkit/upload-artifact.
        For more information, visit the GitHub Artifacts FAQ: https://github.com/actions/toolkit/blob/main/packages/artifact/docs/faq.md`);
        }
        let artifact = res.artifacts[0];
        if (res.artifacts.length > 1) {
            artifact = res.artifacts.sort((a, b) => Number(b.databaseId) - Number(a.databaseId))[0];
            core_debug(`More than one artifact found for a single name, returning newest (id: ${artifact.databaseId})`);
        }
        return {
            artifact: {
                name: artifact.name,
                id: Number(artifact.databaseId),
                size: Number(artifact.size),
                createdAt: artifact.createdAt
                    ? Timestamp.toDate(artifact.createdAt)
                    : undefined,
                digest: (_a = artifact.digest) === null || _a === void 0 ? void 0 : _a.value
            }
        };
    });
}
//# sourceMappingURL=get-artifact.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/delete/delete-artifact.js
var delete_artifact_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};












function deleteArtifactPublic(artifactName, workflowRunId, repositoryOwner, repositoryName, token) {
    return delete_artifact_awaiter(this, void 0, void 0, function* () {
        var _a;
        const [retryOpts, requestOpts] = getRetryOptions(defaults);
        const opts = {
            log: undefined,
            userAgent: getUserAgentString(),
            previews: undefined,
            retry: retryOpts,
            request: requestOpts
        };
        const github = getOctokit(token, opts, retry, requestLog);
        const getArtifactResp = yield getArtifactPublic(artifactName, workflowRunId, repositoryOwner, repositoryName, token);
        const deleteArtifactResp = yield github.rest.actions.deleteArtifact({
            owner: repositoryOwner,
            repo: repositoryName,
            artifact_id: getArtifactResp.artifact.id
        });
        if (deleteArtifactResp.status !== 204) {
            throw new InvalidResponseError(`Invalid response from GitHub API: ${deleteArtifactResp.status} (${(_a = deleteArtifactResp === null || deleteArtifactResp === void 0 ? void 0 : deleteArtifactResp.headers) === null || _a === void 0 ? void 0 : _a['x-github-request-id']})`);
        }
        return {
            id: getArtifactResp.artifact.id
        };
    });
}
function deleteArtifactInternal(artifactName) {
    return delete_artifact_awaiter(this, void 0, void 0, function* () {
        const artifactClient = internalArtifactTwirpClient();
        const { workflowRunBackendId, workflowJobRunBackendId } = getBackendIdsFromToken();
        const listReq = {
            workflowRunBackendId,
            workflowJobRunBackendId,
            nameFilter: StringValue.create({ value: artifactName })
        };
        const listRes = yield artifactClient.ListArtifacts(listReq);
        if (listRes.artifacts.length === 0) {
            throw new ArtifactNotFoundError(`Artifact not found for name: ${artifactName}`);
        }
        let artifact = listRes.artifacts[0];
        if (listRes.artifacts.length > 1) {
            artifact = listRes.artifacts.sort((a, b) => Number(b.databaseId) - Number(a.databaseId))[0];
            core_debug(`More than one artifact found for a single name, returning newest (id: ${artifact.databaseId})`);
        }
        const req = {
            workflowRunBackendId: artifact.workflowRunBackendId,
            workflowJobRunBackendId: artifact.workflowJobRunBackendId,
            name: artifact.name
        };
        const res = yield artifactClient.DeleteArtifact(req);
        info(`Artifact '${artifactName}' (ID: ${res.artifactId}) deleted`);
        return {
            id: Number(res.artifactId)
        };
    });
}
//# sourceMappingURL=delete-artifact.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/find/list-artifacts.js
var list_artifacts_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};











const maximumArtifactCount = getMaxArtifactListCount();
const paginationCount = 100;
const maxNumberOfPages = Math.ceil(maximumArtifactCount / paginationCount);
function listArtifactsPublic(workflowRunId_1, repositoryOwner_1, repositoryName_1, token_1) {
    return list_artifacts_awaiter(this, arguments, void 0, function* (workflowRunId, repositoryOwner, repositoryName, token, latest = false) {
        info(`Fetching artifact list for workflow run ${workflowRunId} in repository ${repositoryOwner}/${repositoryName}`);
        let artifacts = [];
        const [retryOpts, requestOpts] = getRetryOptions(defaults);
        const opts = {
            log: undefined,
            userAgent: getUserAgentString(),
            previews: undefined,
            retry: retryOpts,
            request: requestOpts
        };
        const github = getOctokit(token, opts, retry, requestLog);
        let currentPageNumber = 1;
        const { data: listArtifactResponse } = yield github.request('GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts', {
            owner: repositoryOwner,
            repo: repositoryName,
            run_id: workflowRunId,
            per_page: paginationCount,
            page: currentPageNumber
        });
        let numberOfPages = Math.ceil(listArtifactResponse.total_count / paginationCount);
        const totalArtifactCount = listArtifactResponse.total_count;
        if (totalArtifactCount > maximumArtifactCount) {
            warning(`Workflow run ${workflowRunId} has ${totalArtifactCount} artifacts, exceeding the limit of ${maximumArtifactCount}. Results will be incomplete as only the first ${maximumArtifactCount} artifacts will be returned`);
            numberOfPages = maxNumberOfPages;
        }
        // Iterate over the first page
        for (const artifact of listArtifactResponse.artifacts) {
            artifacts.push({
                name: artifact.name,
                id: artifact.id,
                size: artifact.size_in_bytes,
                createdAt: artifact.created_at
                    ? new Date(artifact.created_at)
                    : undefined,
                digest: artifact.digest
            });
        }
        // Move to the next page
        currentPageNumber++;
        // Iterate over any remaining pages
        for (currentPageNumber; currentPageNumber <= numberOfPages; currentPageNumber++) {
            core_debug(`Fetching page ${currentPageNumber} of artifact list`);
            const { data: listArtifactResponse } = yield github.request('GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts', {
                owner: repositoryOwner,
                repo: repositoryName,
                run_id: workflowRunId,
                per_page: paginationCount,
                page: currentPageNumber
            });
            for (const artifact of listArtifactResponse.artifacts) {
                artifacts.push({
                    name: artifact.name,
                    id: artifact.id,
                    size: artifact.size_in_bytes,
                    createdAt: artifact.created_at
                        ? new Date(artifact.created_at)
                        : undefined,
                    digest: artifact.digest
                });
            }
        }
        if (latest) {
            artifacts = filterLatest(artifacts);
        }
        info(`Found ${artifacts.length} artifact(s)`);
        return {
            artifacts
        };
    });
}
function listArtifactsInternal() {
    return list_artifacts_awaiter(this, arguments, void 0, function* (latest = false) {
        const artifactClient = internalArtifactTwirpClient();
        const { workflowRunBackendId, workflowJobRunBackendId } = getBackendIdsFromToken();
        const req = {
            workflowRunBackendId,
            workflowJobRunBackendId
        };
        const res = yield artifactClient.ListArtifacts(req);
        let artifacts = res.artifacts.map(artifact => {
            var _a;
            return ({
                name: artifact.name,
                id: Number(artifact.databaseId),
                size: Number(artifact.size),
                createdAt: artifact.createdAt
                    ? Timestamp.toDate(artifact.createdAt)
                    : undefined,
                digest: (_a = artifact.digest) === null || _a === void 0 ? void 0 : _a.value
            });
        });
        if (latest) {
            artifacts = filterLatest(artifacts);
        }
        info(`Found ${artifacts.length} artifact(s)`);
        return {
            artifacts
        };
    });
}
/**
 * Filters a list of artifacts to only include the latest artifact for each name
 * @param artifacts The artifacts to filter
 * @returns The filtered list of artifacts
 */
function filterLatest(artifacts) {
    artifacts.sort((a, b) => b.id - a.id);
    const latestArtifacts = [];
    const seenArtifactNames = new Set();
    for (const artifact of artifacts) {
        if (!seenArtifactNames.has(artifact.name)) {
            latestArtifacts.push(artifact);
            seenArtifactNames.add(artifact.name);
        }
    }
    return latestArtifacts;
}
//# sourceMappingURL=list-artifacts.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/client.js
var client_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __rest = (undefined && undefined.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};








/**
 * The default artifact client that is used by the artifact action(s).
 */
class DefaultArtifactClient {
    uploadArtifact(name, files, rootDirectory, options) {
        return client_awaiter(this, void 0, void 0, function* () {
            try {
                if (isGhes()) {
                    throw new GHESNotSupportedError();
                }
                return uploadArtifact(name, files, rootDirectory, options);
            }
            catch (error) {
                warning(`Artifact upload failed with error: ${error}.

Errors can be temporary, so please try again and optionally run the action with debug mode enabled for more information.

If the error persists, please check whether Actions is operating normally at [https://githubstatus.com](https://www.githubstatus.com).`);
                throw error;
            }
        });
    }
    downloadArtifact(artifactId, options) {
        return client_awaiter(this, void 0, void 0, function* () {
            try {
                if (isGhes()) {
                    throw new GHESNotSupportedError();
                }
                if (options === null || options === void 0 ? void 0 : options.findBy) {
                    const { findBy: { repositoryOwner, repositoryName, token } } = options, downloadOptions = __rest(options, ["findBy"]);
                    return downloadArtifactPublic(artifactId, repositoryOwner, repositoryName, token, downloadOptions);
                }
                return downloadArtifactInternal(artifactId, options);
            }
            catch (error) {
                warning(`Download Artifact failed with error: ${error}.

Errors can be temporary, so please try again and optionally run the action with debug mode enabled for more information.

If the error persists, please check whether Actions and API requests are operating normally at [https://githubstatus.com](https://www.githubstatus.com).`);
                throw error;
            }
        });
    }
    listArtifacts(options) {
        return client_awaiter(this, void 0, void 0, function* () {
            try {
                if (isGhes()) {
                    throw new GHESNotSupportedError();
                }
                if (options === null || options === void 0 ? void 0 : options.findBy) {
                    const { findBy: { workflowRunId, repositoryOwner, repositoryName, token } } = options;
                    return listArtifactsPublic(workflowRunId, repositoryOwner, repositoryName, token, options === null || options === void 0 ? void 0 : options.latest);
                }
                return listArtifactsInternal(options === null || options === void 0 ? void 0 : options.latest);
            }
            catch (error) {
                warning(`Listing Artifacts failed with error: ${error}.

Errors can be temporary, so please try again and optionally run the action with debug mode enabled for more information.

If the error persists, please check whether Actions and API requests are operating normally at [https://githubstatus.com](https://www.githubstatus.com).`);
                throw error;
            }
        });
    }
    getArtifact(artifactName, options) {
        return client_awaiter(this, void 0, void 0, function* () {
            try {
                if (isGhes()) {
                    throw new GHESNotSupportedError();
                }
                if (options === null || options === void 0 ? void 0 : options.findBy) {
                    const { findBy: { workflowRunId, repositoryOwner, repositoryName, token } } = options;
                    return getArtifactPublic(artifactName, workflowRunId, repositoryOwner, repositoryName, token);
                }
                return getArtifactInternal(artifactName);
            }
            catch (error) {
                warning(`Get Artifact failed with error: ${error}.

Errors can be temporary, so please try again and optionally run the action with debug mode enabled for more information.

If the error persists, please check whether Actions and API requests are operating normally at [https://githubstatus.com](https://www.githubstatus.com).`);
                throw error;
            }
        });
    }
    deleteArtifact(artifactName, options) {
        return client_awaiter(this, void 0, void 0, function* () {
            try {
                if (isGhes()) {
                    throw new GHESNotSupportedError();
                }
                if (options === null || options === void 0 ? void 0 : options.findBy) {
                    const { findBy: { repositoryOwner, repositoryName, workflowRunId, token } } = options;
                    return deleteArtifactPublic(artifactName, workflowRunId, repositoryOwner, repositoryName, token);
                }
                return deleteArtifactInternal(artifactName);
            }
            catch (error) {
                warning(`Delete Artifact failed with error: ${error}.

Errors can be temporary, so please try again and optionally run the action with debug mode enabled for more information.

If the error persists, please check whether Actions and API requests are operating normally at [https://githubstatus.com](https://www.githubstatus.com).`);
                throw error;
            }
        });
    }
}
//# sourceMappingURL=client.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/artifact.js




const client = new DefaultArtifactClient();
/* harmony default export */ const artifact = (client);
//# sourceMappingURL=artifact.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/glob/lib/internal-glob-options-helper.js

/**
 * Returns a copy with defaults filled in.
 */
function getOptions(copy) {
    const result = {
        followSymbolicLinks: true,
        implicitDescendants: true,
        matchDirectories: true,
        omitBrokenSymbolicLinks: true,
        excludeHiddenFiles: false
    };
    if (copy) {
        if (typeof copy.followSymbolicLinks === 'boolean') {
            result.followSymbolicLinks = copy.followSymbolicLinks;
            core_debug(`followSymbolicLinks '${result.followSymbolicLinks}'`);
        }
        if (typeof copy.implicitDescendants === 'boolean') {
            result.implicitDescendants = copy.implicitDescendants;
            core_debug(`implicitDescendants '${result.implicitDescendants}'`);
        }
        if (typeof copy.matchDirectories === 'boolean') {
            result.matchDirectories = copy.matchDirectories;
            core_debug(`matchDirectories '${result.matchDirectories}'`);
        }
        if (typeof copy.omitBrokenSymbolicLinks === 'boolean') {
            result.omitBrokenSymbolicLinks = copy.omitBrokenSymbolicLinks;
            core_debug(`omitBrokenSymbolicLinks '${result.omitBrokenSymbolicLinks}'`);
        }
        if (typeof copy.excludeHiddenFiles === 'boolean') {
            result.excludeHiddenFiles = copy.excludeHiddenFiles;
            core_debug(`excludeHiddenFiles '${result.excludeHiddenFiles}'`);
        }
    }
    return result;
}
//# sourceMappingURL=internal-glob-options-helper.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/glob/lib/internal-path-helper.js


const internal_path_helper_IS_WINDOWS = process.platform === 'win32';
/**
 * Similar to path.dirname except normalizes the path separators and slightly better handling for Windows UNC paths.
 *
 * For example, on Linux/macOS:
 * - `/               => /`
 * - `/hello          => /`
 *
 * For example, on Windows:
 * - `C:\             => C:\`
 * - `C:\hello        => C:\`
 * - `C:              => C:`
 * - `C:hello         => C:`
 * - `\               => \`
 * - `\hello          => \`
 * - `\\hello         => \\hello`
 * - `\\hello\world   => \\hello\world`
 */
function dirname(p) {
    // Normalize slashes and trim unnecessary trailing slash
    p = safeTrimTrailingSeparator(p);
    // Windows UNC root, e.g. \\hello or \\hello\world
    if (internal_path_helper_IS_WINDOWS && /^\\\\[^\\]+(\\[^\\]+)?$/.test(p)) {
        return p;
    }
    // Get dirname
    let result = external_path_.dirname(p);
    // Trim trailing slash for Windows UNC root, e.g. \\hello\world\
    if (internal_path_helper_IS_WINDOWS && /^\\\\[^\\]+\\[^\\]+\\$/.test(result)) {
        result = safeTrimTrailingSeparator(result);
    }
    return result;
}
/**
 * Roots the path if not already rooted. On Windows, relative roots like `\`
 * or `C:` are expanded based on the current working directory.
 */
function ensureAbsoluteRoot(root, itemPath) {
    external_assert_(root, `ensureAbsoluteRoot parameter 'root' must not be empty`);
    external_assert_(itemPath, `ensureAbsoluteRoot parameter 'itemPath' must not be empty`);
    // Already rooted
    if (hasAbsoluteRoot(itemPath)) {
        return itemPath;
    }
    // Windows
    if (internal_path_helper_IS_WINDOWS) {
        // Check for itemPath like C: or C:foo
        if (itemPath.match(/^[A-Z]:[^\\/]|^[A-Z]:$/i)) {
            let cwd = process.cwd();
            external_assert_(cwd.match(/^[A-Z]:\\/i), `Expected current directory to start with an absolute drive root. Actual '${cwd}'`);
            // Drive letter matches cwd? Expand to cwd
            if (itemPath[0].toUpperCase() === cwd[0].toUpperCase()) {
                // Drive only, e.g. C:
                if (itemPath.length === 2) {
                    // Preserve specified drive letter case (upper or lower)
                    return `${itemPath[0]}:\\${cwd.substr(3)}`;
                }
                // Drive + path, e.g. C:foo
                else {
                    if (!cwd.endsWith('\\')) {
                        cwd += '\\';
                    }
                    // Preserve specified drive letter case (upper or lower)
                    return `${itemPath[0]}:\\${cwd.substr(3)}${itemPath.substr(2)}`;
                }
            }
            // Different drive
            else {
                return `${itemPath[0]}:\\${itemPath.substr(2)}`;
            }
        }
        // Check for itemPath like \ or \foo
        else if (internal_path_helper_normalizeSeparators(itemPath).match(/^\\$|^\\[^\\]/)) {
            const cwd = process.cwd();
            external_assert_(cwd.match(/^[A-Z]:\\/i), `Expected current directory to start with an absolute drive root. Actual '${cwd}'`);
            return `${cwd[0]}:\\${itemPath.substr(1)}`;
        }
    }
    external_assert_(hasAbsoluteRoot(root), `ensureAbsoluteRoot parameter 'root' must have an absolute root`);
    // Otherwise ensure root ends with a separator
    if (root.endsWith('/') || (internal_path_helper_IS_WINDOWS && root.endsWith('\\'))) {
        // Intentionally empty
    }
    else {
        // Append separator
        root += external_path_.sep;
    }
    return root + itemPath;
}
/**
 * On Linux/macOS, true if path starts with `/`. On Windows, true for paths like:
 * `\\hello\share` and `C:\hello` (and using alternate separator).
 */
function hasAbsoluteRoot(itemPath) {
    external_assert_(itemPath, `hasAbsoluteRoot parameter 'itemPath' must not be empty`);
    // Normalize separators
    itemPath = internal_path_helper_normalizeSeparators(itemPath);
    // Windows
    if (internal_path_helper_IS_WINDOWS) {
        // E.g. \\hello\share or C:\hello
        return itemPath.startsWith('\\\\') || /^[A-Z]:\\/i.test(itemPath);
    }
    // E.g. /hello
    return itemPath.startsWith('/');
}
/**
 * On Linux/macOS, true if path starts with `/`. On Windows, true for paths like:
 * `\`, `\hello`, `\\hello\share`, `C:`, and `C:\hello` (and using alternate separator).
 */
function hasRoot(itemPath) {
    external_assert_(itemPath, `isRooted parameter 'itemPath' must not be empty`);
    // Normalize separators
    itemPath = internal_path_helper_normalizeSeparators(itemPath);
    // Windows
    if (internal_path_helper_IS_WINDOWS) {
        // E.g. \ or \hello or \\hello
        // E.g. C: or C:\hello
        return itemPath.startsWith('\\') || /^[A-Z]:/i.test(itemPath);
    }
    // E.g. /hello
    return itemPath.startsWith('/');
}
/**
 * Removes redundant slashes and converts `/` to `\` on Windows
 */
function internal_path_helper_normalizeSeparators(p) {
    p = p || '';
    // Windows
    if (internal_path_helper_IS_WINDOWS) {
        // Convert slashes on Windows
        p = p.replace(/\//g, '\\');
        // Remove redundant slashes
        const isUnc = /^\\\\+[^\\]/.test(p); // e.g. \\hello
        return (isUnc ? '\\' : '') + p.replace(/\\\\+/g, '\\'); // preserve leading \\ for UNC
    }
    // Remove redundant slashes
    return p.replace(/\/\/+/g, '/');
}
/**
 * Normalizes the path separators and trims the trailing separator (when safe).
 * For example, `/foo/ => /foo` but `/ => /`
 */
function safeTrimTrailingSeparator(p) {
    // Short-circuit if empty
    if (!p) {
        return '';
    }
    // Normalize separators
    p = internal_path_helper_normalizeSeparators(p);
    // No trailing slash
    if (!p.endsWith(external_path_.sep)) {
        return p;
    }
    // Check '/' on Linux/macOS and '\' on Windows
    if (p === external_path_.sep) {
        return p;
    }
    // On Windows check if drive root. E.g. C:\
    if (internal_path_helper_IS_WINDOWS && /^[A-Z]:\\$/i.test(p)) {
        return p;
    }
    // Otherwise trim trailing slash
    return p.substr(0, p.length - 1);
}
//# sourceMappingURL=internal-path-helper.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/glob/lib/internal-match-kind.js
/**
 * Indicates whether a pattern matches a path
 */
var MatchKind;
(function (MatchKind) {
    /** Not matched */
    MatchKind[MatchKind["None"] = 0] = "None";
    /** Matched if the path is a directory */
    MatchKind[MatchKind["Directory"] = 1] = "Directory";
    /** Matched if the path is a regular file */
    MatchKind[MatchKind["File"] = 2] = "File";
    /** Matched */
    MatchKind[MatchKind["All"] = 3] = "All";
})(MatchKind || (MatchKind = {}));
//# sourceMappingURL=internal-match-kind.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/glob/lib/internal-pattern-helper.js


const internal_pattern_helper_IS_WINDOWS = process.platform === 'win32';
/**
 * Given an array of patterns, returns an array of paths to search.
 * Duplicates and paths under other included paths are filtered out.
 */
function getSearchPaths(patterns) {
    // Ignore negate patterns
    patterns = patterns.filter(x => !x.negate);
    // Create a map of all search paths
    const searchPathMap = {};
    for (const pattern of patterns) {
        const key = internal_pattern_helper_IS_WINDOWS
            ? pattern.searchPath.toUpperCase()
            : pattern.searchPath;
        searchPathMap[key] = 'candidate';
    }
    const result = [];
    for (const pattern of patterns) {
        // Check if already included
        const key = internal_pattern_helper_IS_WINDOWS
            ? pattern.searchPath.toUpperCase()
            : pattern.searchPath;
        if (searchPathMap[key] === 'included') {
            continue;
        }
        // Check for an ancestor search path
        let foundAncestor = false;
        let tempKey = key;
        let parent = dirname(tempKey);
        while (parent !== tempKey) {
            if (searchPathMap[parent]) {
                foundAncestor = true;
                break;
            }
            tempKey = parent;
            parent = dirname(tempKey);
        }
        // Include the search pattern in the result
        if (!foundAncestor) {
            result.push(pattern.searchPath);
            searchPathMap[key] = 'included';
        }
    }
    return result;
}
/**
 * Matches the patterns against the path
 */
function internal_pattern_helper_match(patterns, itemPath) {
    let result = MatchKind.None;
    for (const pattern of patterns) {
        if (pattern.negate) {
            result &= ~pattern.match(itemPath);
        }
        else {
            result |= pattern.match(itemPath);
        }
    }
    return result;
}
/**
 * Checks whether to descend further into the directory
 */
function internal_pattern_helper_partialMatch(patterns, itemPath) {
    return patterns.some(x => !x.negate && x.partialMatch(itemPath));
}
//# sourceMappingURL=internal-pattern-helper.js.map
// EXTERNAL MODULE: ./node_modules/@actions/glob/node_modules/minimatch/minimatch.js
var minimatch = __nccwpck_require__(7145);
;// CONCATENATED MODULE: ./node_modules/@actions/glob/lib/internal-path.js



const internal_path_IS_WINDOWS = process.platform === 'win32';
/**
 * Helper class for parsing paths into segments
 */
class Path {
    /**
     * Constructs a Path
     * @param itemPath Path or array of segments
     */
    constructor(itemPath) {
        this.segments = [];
        // String
        if (typeof itemPath === 'string') {
            external_assert_(itemPath, `Parameter 'itemPath' must not be empty`);
            // Normalize slashes and trim unnecessary trailing slash
            itemPath = safeTrimTrailingSeparator(itemPath);
            // Not rooted
            if (!hasRoot(itemPath)) {
                this.segments = itemPath.split(external_path_.sep);
            }
            // Rooted
            else {
                // Add all segments, while not at the root
                let remaining = itemPath;
                let dir = dirname(remaining);
                while (dir !== remaining) {
                    // Add the segment
                    const basename = external_path_.basename(remaining);
                    this.segments.unshift(basename);
                    // Truncate the last segment
                    remaining = dir;
                    dir = dirname(remaining);
                }
                // Remainder is the root
                this.segments.unshift(remaining);
            }
        }
        // Array
        else {
            // Must not be empty
            external_assert_(itemPath.length > 0, `Parameter 'itemPath' must not be an empty array`);
            // Each segment
            for (let i = 0; i < itemPath.length; i++) {
                let segment = itemPath[i];
                // Must not be empty
                external_assert_(segment, `Parameter 'itemPath' must not contain any empty segments`);
                // Normalize slashes
                segment = internal_path_helper_normalizeSeparators(itemPath[i]);
                // Root segment
                if (i === 0 && hasRoot(segment)) {
                    segment = safeTrimTrailingSeparator(segment);
                    external_assert_(segment === dirname(segment), `Parameter 'itemPath' root segment contains information for multiple segments`);
                    this.segments.push(segment);
                }
                // All other segments
                else {
                    // Must not contain slash
                    external_assert_(!segment.includes(external_path_.sep), `Parameter 'itemPath' contains unexpected path separators`);
                    this.segments.push(segment);
                }
            }
        }
    }
    /**
     * Converts the path to it's string representation
     */
    toString() {
        // First segment
        let result = this.segments[0];
        // All others
        let skipSlash = result.endsWith(external_path_.sep) || (internal_path_IS_WINDOWS && /^[A-Z]:$/i.test(result));
        for (let i = 1; i < this.segments.length; i++) {
            if (skipSlash) {
                skipSlash = false;
            }
            else {
                result += external_path_.sep;
            }
            result += this.segments[i];
        }
        return result;
    }
}
//# sourceMappingURL=internal-path.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/glob/lib/internal-pattern.js







const { Minimatch } = minimatch;
const internal_pattern_IS_WINDOWS = process.platform === 'win32';
class Pattern {
    constructor(patternOrNegate, isImplicitPattern = false, segments, homedir) {
        /**
         * Indicates whether matches should be excluded from the result set
         */
        this.negate = false;
        // Pattern overload
        let pattern;
        if (typeof patternOrNegate === 'string') {
            pattern = patternOrNegate.trim();
        }
        // Segments overload
        else {
            // Convert to pattern
            segments = segments || [];
            external_assert_(segments.length, `Parameter 'segments' must not empty`);
            const root = Pattern.getLiteral(segments[0]);
            external_assert_(root && hasAbsoluteRoot(root), `Parameter 'segments' first element must be a root path`);
            pattern = new Path(segments).toString().trim();
            if (patternOrNegate) {
                pattern = `!${pattern}`;
            }
        }
        // Negate
        while (pattern.startsWith('!')) {
            this.negate = !this.negate;
            pattern = pattern.substr(1).trim();
        }
        // Normalize slashes and ensures absolute root
        pattern = Pattern.fixupPattern(pattern, homedir);
        // Segments
        this.segments = new Path(pattern).segments;
        // Trailing slash indicates the pattern should only match directories, not regular files
        this.trailingSeparator = internal_path_helper_normalizeSeparators(pattern)
            .endsWith(external_path_.sep);
        pattern = safeTrimTrailingSeparator(pattern);
        // Search path (literal path prior to the first glob segment)
        let foundGlob = false;
        const searchSegments = this.segments
            .map(x => Pattern.getLiteral(x))
            .filter(x => !foundGlob && !(foundGlob = x === ''));
        this.searchPath = new Path(searchSegments).toString();
        // Root RegExp (required when determining partial match)
        this.rootRegExp = new RegExp(Pattern.regExpEscape(searchSegments[0]), internal_pattern_IS_WINDOWS ? 'i' : '');
        this.isImplicitPattern = isImplicitPattern;
        // Create minimatch
        const minimatchOptions = {
            dot: true,
            nobrace: true,
            nocase: internal_pattern_IS_WINDOWS,
            nocomment: true,
            noext: true,
            nonegate: true
        };
        pattern = internal_pattern_IS_WINDOWS ? pattern.replace(/\\/g, '/') : pattern;
        this.minimatch = new Minimatch(pattern, minimatchOptions);
    }
    /**
     * Matches the pattern against the specified path
     */
    match(itemPath) {
        // Last segment is globstar?
        if (this.segments[this.segments.length - 1] === '**') {
            // Normalize slashes
            itemPath = internal_path_helper_normalizeSeparators(itemPath);
            // Append a trailing slash. Otherwise Minimatch will not match the directory immediately
            // preceding the globstar. For example, given the pattern `/foo/**`, Minimatch returns
            // false for `/foo` but returns true for `/foo/`. Append a trailing slash to handle that quirk.
            if (!itemPath.endsWith(external_path_.sep) && this.isImplicitPattern === false) {
                // Note, this is safe because the constructor ensures the pattern has an absolute root.
                // For example, formats like C: and C:foo on Windows are resolved to an absolute root.
                itemPath = `${itemPath}${external_path_.sep}`;
            }
        }
        else {
            // Normalize slashes and trim unnecessary trailing slash
            itemPath = safeTrimTrailingSeparator(itemPath);
        }
        // Match
        if (this.minimatch.match(itemPath)) {
            return this.trailingSeparator ? MatchKind.Directory : MatchKind.All;
        }
        return MatchKind.None;
    }
    /**
     * Indicates whether the pattern may match descendants of the specified path
     */
    partialMatch(itemPath) {
        // Normalize slashes and trim unnecessary trailing slash
        itemPath = safeTrimTrailingSeparator(itemPath);
        // matchOne does not handle root path correctly
        if (dirname(itemPath) === itemPath) {
            return this.rootRegExp.test(itemPath);
        }
        return this.minimatch.matchOne(itemPath.split(internal_pattern_IS_WINDOWS ? /\\+/ : /\/+/), this.minimatch.set[0], true);
    }
    /**
     * Escapes glob patterns within a path
     */
    static globEscape(s) {
        return (internal_pattern_IS_WINDOWS ? s : s.replace(/\\/g, '\\\\')) // escape '\' on Linux/macOS
            .replace(/(\[)(?=[^/]+\])/g, '[[]') // escape '[' when ']' follows within the path segment
            .replace(/\?/g, '[?]') // escape '?'
            .replace(/\*/g, '[*]'); // escape '*'
    }
    /**
     * Normalizes slashes and ensures absolute root
     */
    static fixupPattern(pattern, homedir) {
        // Empty
        external_assert_(pattern, 'pattern cannot be empty');
        // Must not contain `.` segment, unless first segment
        // Must not contain `..` segment
        const literalSegments = new Path(pattern).segments.map(x => Pattern.getLiteral(x));
        external_assert_(literalSegments.every((x, i) => (x !== '.' || i === 0) && x !== '..'), `Invalid pattern '${pattern}'. Relative pathing '.' and '..' is not allowed.`);
        // Must not contain globs in root, e.g. Windows UNC path \\foo\b*r
        external_assert_(!hasRoot(pattern) || literalSegments[0], `Invalid pattern '${pattern}'. Root segment must not contain globs.`);
        // Normalize slashes
        pattern = internal_path_helper_normalizeSeparators(pattern);
        // Replace leading `.` segment
        if (pattern === '.' || pattern.startsWith(`.${external_path_.sep}`)) {
            pattern = Pattern.globEscape(process.cwd()) + pattern.substr(1);
        }
        // Replace leading `~` segment
        else if (pattern === '~' || pattern.startsWith(`~${external_path_.sep}`)) {
            homedir = homedir || external_os_.homedir();
            external_assert_(homedir, 'Unable to determine HOME directory');
            external_assert_(hasAbsoluteRoot(homedir), `Expected HOME directory to be a rooted path. Actual '${homedir}'`);
            pattern = Pattern.globEscape(homedir) + pattern.substr(1);
        }
        // Replace relative drive root, e.g. pattern is C: or C:foo
        else if (internal_pattern_IS_WINDOWS &&
            (pattern.match(/^[A-Z]:$/i) || pattern.match(/^[A-Z]:[^\\]/i))) {
            let root = ensureAbsoluteRoot('C:\\dummy-root', pattern.substr(0, 2));
            if (pattern.length > 2 && !root.endsWith('\\')) {
                root += '\\';
            }
            pattern = Pattern.globEscape(root) + pattern.substr(2);
        }
        // Replace relative root, e.g. pattern is \ or \foo
        else if (internal_pattern_IS_WINDOWS && (pattern === '\\' || pattern.match(/^\\[^\\]/))) {
            let root = ensureAbsoluteRoot('C:\\dummy-root', '\\');
            if (!root.endsWith('\\')) {
                root += '\\';
            }
            pattern = Pattern.globEscape(root) + pattern.substr(1);
        }
        // Otherwise ensure absolute root
        else {
            pattern = ensureAbsoluteRoot(Pattern.globEscape(process.cwd()), pattern);
        }
        return internal_path_helper_normalizeSeparators(pattern);
    }
    /**
     * Attempts to unescape a pattern segment to create a literal path segment.
     * Otherwise returns empty string.
     */
    static getLiteral(segment) {
        let literal = '';
        for (let i = 0; i < segment.length; i++) {
            const c = segment[i];
            // Escape
            if (c === '\\' && !internal_pattern_IS_WINDOWS && i + 1 < segment.length) {
                literal += segment[++i];
                continue;
            }
            // Wildcard
            else if (c === '*' || c === '?') {
                return '';
            }
            // Character set
            else if (c === '[' && i + 1 < segment.length) {
                let set = '';
                let closed = -1;
                for (let i2 = i + 1; i2 < segment.length; i2++) {
                    const c2 = segment[i2];
                    // Escape
                    if (c2 === '\\' && !internal_pattern_IS_WINDOWS && i2 + 1 < segment.length) {
                        set += segment[++i2];
                        continue;
                    }
                    // Closed
                    else if (c2 === ']') {
                        closed = i2;
                        break;
                    }
                    // Otherwise
                    else {
                        set += c2;
                    }
                }
                // Closed?
                if (closed >= 0) {
                    // Cannot convert
                    if (set.length > 1) {
                        return '';
                    }
                    // Convert to literal
                    if (set) {
                        literal += set;
                        i = closed;
                        continue;
                    }
                }
                // Otherwise fall thru
            }
            // Append
            literal += c;
        }
        return literal;
    }
    /**
     * Escapes regexp special characters
     * https://javascript.info/regexp-escaping
     */
    static regExpEscape(s) {
        return s.replace(/[[\\^$.|?*+()]/g, '\\$&');
    }
}
//# sourceMappingURL=internal-pattern.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/glob/lib/internal-search-state.js
class SearchState {
    constructor(path, level) {
        this.path = path;
        this.level = level;
    }
}
//# sourceMappingURL=internal-search-state.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/glob/lib/internal-globber.js
var internal_globber_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __asyncValues = (undefined && undefined.__asyncValues) || function (o) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var m = o[Symbol.asyncIterator], i;
    return m ? m.call(o) : (o = typeof __values === "function" ? __values(o) : o[Symbol.iterator](), i = {}, verb("next"), verb("throw"), verb("return"), i[Symbol.asyncIterator] = function () { return this; }, i);
    function verb(n) { i[n] = o[n] && function (v) { return new Promise(function (resolve, reject) { v = o[n](v), settle(resolve, reject, v.done, v.value); }); }; }
    function settle(resolve, reject, d, v) { Promise.resolve(v).then(function(v) { resolve({ value: v, done: d }); }, reject); }
};
var __await = (undefined && undefined.__await) || function (v) { return this instanceof __await ? (this.v = v, this) : new __await(v); }
var __asyncGenerator = (undefined && undefined.__asyncGenerator) || function (thisArg, _arguments, generator) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var g = generator.apply(thisArg, _arguments || []), i, q = [];
    return i = Object.create((typeof AsyncIterator === "function" ? AsyncIterator : Object).prototype), verb("next"), verb("throw"), verb("return", awaitReturn), i[Symbol.asyncIterator] = function () { return this; }, i;
    function awaitReturn(f) { return function (v) { return Promise.resolve(v).then(f, reject); }; }
    function verb(n, f) { if (g[n]) { i[n] = function (v) { return new Promise(function (a, b) { q.push([n, v, a, b]) > 1 || resume(n, v); }); }; if (f) i[n] = f(i[n]); } }
    function resume(n, v) { try { step(g[n](v)); } catch (e) { settle(q[0][3], e); } }
    function step(r) { r.value instanceof __await ? Promise.resolve(r.value.v).then(fulfill, reject) : settle(q[0][2], r); }
    function fulfill(value) { resume("next", value); }
    function reject(value) { resume("throw", value); }
    function settle(f, v) { if (f(v), q.shift(), q.length) resume(q[0][0], q[0][1]); }
};








const internal_globber_IS_WINDOWS = process.platform === 'win32';
class DefaultGlobber {
    constructor(options) {
        this.patterns = [];
        this.searchPaths = [];
        this.options = getOptions(options);
    }
    getSearchPaths() {
        // Return a copy
        return this.searchPaths.slice();
    }
    glob() {
        return internal_globber_awaiter(this, void 0, void 0, function* () {
            var _a, e_1, _b, _c;
            const result = [];
            try {
                for (var _d = true, _e = __asyncValues(this.globGenerator()), _f; _f = yield _e.next(), _a = _f.done, !_a; _d = true) {
                    _c = _f.value;
                    _d = false;
                    const itemPath = _c;
                    result.push(itemPath);
                }
            }
            catch (e_1_1) { e_1 = { error: e_1_1 }; }
            finally {
                try {
                    if (!_d && !_a && (_b = _e.return)) yield _b.call(_e);
                }
                finally { if (e_1) throw e_1.error; }
            }
            return result;
        });
    }
    globGenerator() {
        return __asyncGenerator(this, arguments, function* globGenerator_1() {
            // Fill in defaults options
            const options = getOptions(this.options);
            // Implicit descendants?
            const patterns = [];
            for (const pattern of this.patterns) {
                patterns.push(pattern);
                if (options.implicitDescendants &&
                    (pattern.trailingSeparator ||
                        pattern.segments[pattern.segments.length - 1] !== '**')) {
                    patterns.push(new Pattern(pattern.negate, true, pattern.segments.concat('**')));
                }
            }
            // Push the search paths
            const stack = [];
            for (const searchPath of getSearchPaths(patterns)) {
                core_debug(`Search path '${searchPath}'`);
                // Exists?
                try {
                    // Intentionally using lstat. Detection for broken symlink
                    // will be performed later (if following symlinks).
                    yield __await(external_fs_.promises.lstat(searchPath));
                }
                catch (err) {
                    if (err.code === 'ENOENT') {
                        continue;
                    }
                    throw err;
                }
                stack.unshift(new SearchState(searchPath, 1));
            }
            // Search
            const traversalChain = []; // used to detect cycles
            while (stack.length) {
                // Pop
                const item = stack.pop();
                // Match?
                const match = internal_pattern_helper_match(patterns, item.path);
                const partialMatch = !!match || internal_pattern_helper_partialMatch(patterns, item.path);
                if (!match && !partialMatch) {
                    continue;
                }
                // Stat
                const stats = yield __await(DefaultGlobber.stat(item, options, traversalChain)
                // Broken symlink, or symlink cycle detected, or no longer exists
                );
                // Broken symlink, or symlink cycle detected, or no longer exists
                if (!stats) {
                    continue;
                }
                // Hidden file or directory?
                if (options.excludeHiddenFiles && external_path_.basename(item.path).match(/^\./)) {
                    continue;
                }
                // Directory
                if (stats.isDirectory()) {
                    // Matched
                    if (match & MatchKind.Directory && options.matchDirectories) {
                        yield yield __await(item.path);
                    }
                    // Descend?
                    else if (!partialMatch) {
                        continue;
                    }
                    // Push the child items in reverse
                    const childLevel = item.level + 1;
                    const childItems = (yield __await(external_fs_.promises.readdir(item.path))).map(x => new SearchState(external_path_.join(item.path, x), childLevel));
                    stack.push(...childItems.reverse());
                }
                // File
                else if (match & MatchKind.File) {
                    yield yield __await(item.path);
                }
            }
        });
    }
    /**
     * Constructs a DefaultGlobber
     */
    static create(patterns, options) {
        return internal_globber_awaiter(this, void 0, void 0, function* () {
            const result = new DefaultGlobber(options);
            if (internal_globber_IS_WINDOWS) {
                patterns = patterns.replace(/\r\n/g, '\n');
                patterns = patterns.replace(/\r/g, '\n');
            }
            const lines = patterns.split('\n').map(x => x.trim());
            for (const line of lines) {
                // Empty or comment
                if (!line || line.startsWith('#')) {
                    continue;
                }
                // Pattern
                else {
                    result.patterns.push(new Pattern(line));
                }
            }
            result.searchPaths.push(...getSearchPaths(result.patterns));
            return result;
        });
    }
    static stat(item, options, traversalChain) {
        return internal_globber_awaiter(this, void 0, void 0, function* () {
            // Note:
            // `stat` returns info about the target of a symlink (or symlink chain)
            // `lstat` returns info about a symlink itself
            let stats;
            if (options.followSymbolicLinks) {
                try {
                    // Use `stat` (following symlinks)
                    stats = yield external_fs_.promises.stat(item.path);
                }
                catch (err) {
                    if (err.code === 'ENOENT') {
                        if (options.omitBrokenSymbolicLinks) {
                            core_debug(`Broken symlink '${item.path}'`);
                            return undefined;
                        }
                        throw new Error(`No information found for the path '${item.path}'. This may indicate a broken symbolic link.`);
                    }
                    throw err;
                }
            }
            else {
                // Use `lstat` (not following symlinks)
                stats = yield external_fs_.promises.lstat(item.path);
            }
            // Note, isDirectory() returns false for the lstat of a symlink
            if (stats.isDirectory() && options.followSymbolicLinks) {
                // Get the realpath
                const realPath = yield external_fs_.promises.realpath(item.path);
                // Fixup the traversal chain to match the item level
                while (traversalChain.length >= item.level) {
                    traversalChain.pop();
                }
                // Test for a cycle
                if (traversalChain.some((x) => x === realPath)) {
                    core_debug(`Symlink cycle detected for path '${item.path}' and realpath '${realPath}'`);
                    return undefined;
                }
                // Update the traversal chain
                traversalChain.push(realPath);
            }
            return stats;
        });
    }
}
//# sourceMappingURL=internal-globber.js.map
// EXTERNAL MODULE: external "util"
var external_util_ = __nccwpck_require__(9023);
;// CONCATENATED MODULE: ./node_modules/@actions/glob/lib/internal-hash-files.js
var internal_hash_files_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var internal_hash_files_asyncValues = (undefined && undefined.__asyncValues) || function (o) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var m = o[Symbol.asyncIterator], i;
    return m ? m.call(o) : (o = typeof __values === "function" ? __values(o) : o[Symbol.iterator](), i = {}, verb("next"), verb("throw"), verb("return"), i[Symbol.asyncIterator] = function () { return this; }, i);
    function verb(n) { i[n] = o[n] && function (v) { return new Promise(function (resolve, reject) { v = o[n](v), settle(resolve, reject, v.done, v.value); }); }; }
    function settle(resolve, reject, d, v) { Promise.resolve(v).then(function(v) { resolve({ value: v, done: d }); }, reject); }
};






function hashFiles(globber_1, currentWorkspace_1) {
    return internal_hash_files_awaiter(this, arguments, void 0, function* (globber, currentWorkspace, verbose = false) {
        var _a, e_1, _b, _c;
        var _d;
        const writeDelegate = verbose ? core.info : core.debug;
        let hasMatch = false;
        const githubWorkspace = currentWorkspace
            ? currentWorkspace
            : ((_d = process.env['GITHUB_WORKSPACE']) !== null && _d !== void 0 ? _d : process.cwd());
        const result = crypto.createHash('sha256');
        let count = 0;
        try {
            for (var _e = true, _f = internal_hash_files_asyncValues(globber.globGenerator()), _g; _g = yield _f.next(), _a = _g.done, !_a; _e = true) {
                _c = _g.value;
                _e = false;
                const file = _c;
                writeDelegate(file);
                if (!file.startsWith(`${githubWorkspace}${path.sep}`)) {
                    writeDelegate(`Ignore '${file}' since it is not under GITHUB_WORKSPACE.`);
                    continue;
                }
                if (fs.statSync(file).isDirectory()) {
                    writeDelegate(`Skip directory '${file}'.`);
                    continue;
                }
                const hash = crypto.createHash('sha256');
                const pipeline = util.promisify(stream.pipeline);
                yield pipeline(fs.createReadStream(file), hash);
                result.write(hash.digest());
                count++;
                if (!hasMatch) {
                    hasMatch = true;
                }
            }
        }
        catch (e_1_1) { e_1 = { error: e_1_1 }; }
        finally {
            try {
                if (!_e && !_a && (_b = _f.return)) yield _b.call(_f);
            }
            finally { if (e_1) throw e_1.error; }
        }
        result.end();
        if (hasMatch) {
            writeDelegate(`Found ${count} files to hash.`);
            return result.digest('hex');
        }
        else {
            writeDelegate(`No matches found for glob`);
            return '';
        }
    });
}
//# sourceMappingURL=internal-hash-files.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/glob/lib/glob.js
var glob_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};


/**
 * Constructs a globber
 *
 * @param patterns  Patterns separated by newlines
 * @param options   Glob options
 */
function create(patterns, options) {
    return glob_awaiter(this, void 0, void 0, function* () {
        return yield DefaultGlobber.create(patterns, options);
    });
}
/**
 * Computes the sha256 hash of a glob
 *
 * @param patterns  Patterns separated by newlines
 * @param currentWorkspace  Workspace used when matching files
 * @param options   Glob options
 * @param verbose   Enables verbose logging
 */
function glob_hashFiles(patterns_1) {
    return glob_awaiter(this, arguments, void 0, function* (patterns, currentWorkspace = '', options, verbose = false) {
        let followSymbolicLinks = true;
        if (options && typeof options.followSymbolicLinks === 'boolean') {
            followSymbolicLinks = options.followSymbolicLinks;
        }
        const globber = yield create(patterns, { followSymbolicLinks });
        return _hashFiles(globber, currentWorkspace, verbose);
    });
}
//# sourceMappingURL=glob.js.map
;// CONCATENATED MODULE: ./src/shared/search.ts






const stats = (0,external_util_.promisify)(external_fs_.stat);
function getDefaultGlobOptions(includeHiddenFiles) {
    return {
        followSymbolicLinks: true,
        implicitDescendants: true,
        omitBrokenSymbolicLinks: true,
        excludeHiddenFiles: !includeHiddenFiles
    };
}
/**
 * If multiple paths are specific, the least common ancestor (LCA) of the search paths is used as
 * the delimiter to control the directory structure for the artifact. This function returns the LCA
 * when given an array of search paths
 *
 * Example 1: The patterns `/foo/` and `/bar/` returns `/`
 *
 * Example 2: The patterns `~/foo/bar/*` and `~/foo/voo/two/*` and `~/foo/mo/` returns `~/foo`
 */
function getMultiPathLCA(searchPaths) {
    if (searchPaths.length < 2) {
        throw new Error('At least two search paths must be provided');
    }
    const commonPaths = new Array();
    const splitPaths = new Array();
    let smallestPathLength = Number.MAX_SAFE_INTEGER;
    // split each of the search paths using the platform specific separator
    for (const searchPath of searchPaths) {
        core_debug(`Using search path ${searchPath}`);
        const splitSearchPath = external_path_.normalize(searchPath).split(external_path_.sep);
        // keep track of the smallest path length so that we don't accidentally later go out of bounds
        smallestPathLength = Math.min(smallestPathLength, splitSearchPath.length);
        splitPaths.push(splitSearchPath);
    }
    // on Unix-like file systems, the file separator exists at the beginning of the file path, make sure to preserve it
    if (searchPaths[0].startsWith(external_path_.sep)) {
        commonPaths.push(external_path_.sep);
    }
    let splitIndex = 0;
    // function to check if the paths are the same at a specific index
    function isPathTheSame() {
        const compare = splitPaths[0][splitIndex];
        for (let i = 1; i < splitPaths.length; i++) {
            if (compare !== splitPaths[i][splitIndex]) {
                // a non-common index has been reached
                return false;
            }
        }
        return true;
    }
    // loop over all the search paths until there is a non-common ancestor or we go out of bounds
    while (splitIndex < smallestPathLength) {
        if (!isPathTheSame()) {
            break;
        }
        // if all are the same, add to the end result & increment the index
        commonPaths.push(splitPaths[0][splitIndex]);
        splitIndex++;
    }
    return external_path_.join(...commonPaths);
}
async function findFilesToUpload(searchPath, includeHiddenFiles) {
    const searchResults = [];
    const globber = await create(searchPath, getDefaultGlobOptions(includeHiddenFiles || false));
    const rawSearchResults = await globber.glob();
    /*
      Files are saved with case insensitivity. Uploading both a.txt and A.txt will files to be overwritten
      Detect any files that could be overwritten for user awareness
    */
    const set = new Set();
    /*
      Directories will be rejected if attempted to be uploaded. This includes just empty
      directories so filter any directories out from the raw search results
    */
    for (const searchResult of rawSearchResults) {
        const fileStats = await stats(searchResult);
        // isDirectory() returns false for symlinks if using fs.lstat(), make sure to use fs.stat() instead
        if (!fileStats.isDirectory()) {
            core_debug(`File:${searchResult} was found using the provided searchPath`);
            searchResults.push(searchResult);
            // detect any files that would be overwritten because of case insensitivity
            if (set.has(searchResult.toLowerCase())) {
                info(`Uploads are case insensitive: ${searchResult} was detected that it will be overwritten by another file with the same path`);
            }
            else {
                set.add(searchResult.toLowerCase());
            }
        }
        else {
            core_debug(`Removing ${searchResult} from rawSearchResults because it is a directory`);
        }
    }
    // Calculate the root directory for the artifact using the search paths that were utilized
    const searchPaths = globber.getSearchPaths();
    if (searchPaths.length > 1) {
        info(`Multiple search paths detected. Calculating the least common ancestor of all paths`);
        const lcaSearchPath = getMultiPathLCA(searchPaths);
        info(`The least common ancestor is ${lcaSearchPath}. This will be the root directory of the artifact`);
        return {
            filesToUpload: searchResults,
            rootDirectory: lcaSearchPath
        };
    }
    /*
      Special case for a single file artifact that is uploaded without a directory or wildcard pattern. The directory structure is
      not preserved and the root directory will be the single files parent directory
    */
    if (searchResults.length === 1 && searchPaths[0] === searchResults[0]) {
        return {
            filesToUpload: searchResults,
            rootDirectory: (0,external_path_.dirname)(searchResults[0])
        };
    }
    return {
        filesToUpload: searchResults,
        rootDirectory: searchPaths[0]
    };
}

;// CONCATENATED MODULE: ./src/upload/constants.ts
/* eslint-disable no-unused-vars */
var Inputs;
(function (Inputs) {
    Inputs["Name"] = "name";
    Inputs["Path"] = "path";
    Inputs["IfNoFilesFound"] = "if-no-files-found";
    Inputs["RetentionDays"] = "retention-days";
    Inputs["CompressionLevel"] = "compression-level";
    Inputs["Overwrite"] = "overwrite";
    Inputs["IncludeHiddenFiles"] = "include-hidden-files";
    Inputs["Archive"] = "archive";
})(Inputs || (Inputs = {}));
var NoFileOptions;
(function (NoFileOptions) {
    /**
     * Default. Output a warning but do not fail the action
     */
    NoFileOptions["warn"] = "warn";
    /**
     * Fail the action with an error message
     */
    NoFileOptions["error"] = "error";
    /**
     * Do not output any warnings or errors, the action does not fail
     */
    NoFileOptions["ignore"] = "ignore";
})(NoFileOptions || (NoFileOptions = {}));

;// CONCATENATED MODULE: ./src/upload/input-helper.ts


/**
 * Helper to get all the inputs for the action
 */
function getInputs() {
    const name = getInput(Inputs.Name);
    const path = getInput(Inputs.Path, { required: true });
    const overwrite = getBooleanInput(Inputs.Overwrite);
    const includeHiddenFiles = getBooleanInput(Inputs.IncludeHiddenFiles);
    const archive = getBooleanInput(Inputs.Archive);
    const ifNoFilesFound = getInput(Inputs.IfNoFilesFound);
    const noFileBehavior = NoFileOptions[ifNoFilesFound];
    if (!noFileBehavior) {
        setFailed(`Unrecognized ${Inputs.IfNoFilesFound} input. Provided: ${ifNoFilesFound}. Available options: ${Object.keys(NoFileOptions)}`);
    }
    const inputs = {
        artifactName: name,
        searchPath: path,
        ifNoFilesFound: noFileBehavior,
        overwrite: overwrite,
        includeHiddenFiles: includeHiddenFiles,
        archive: archive
    };
    const retentionDaysStr = getInput(Inputs.RetentionDays);
    if (retentionDaysStr) {
        inputs.retentionDays = parseInt(retentionDaysStr);
        if (isNaN(inputs.retentionDays)) {
            setFailed('Invalid retention-days');
        }
    }
    const compressionLevelStr = getInput(Inputs.CompressionLevel);
    if (compressionLevelStr) {
        inputs.compressionLevel = parseInt(compressionLevelStr);
        if (isNaN(inputs.compressionLevel)) {
            setFailed('Invalid compression-level');
        }
        if (inputs.compressionLevel < 0 || inputs.compressionLevel > 9) {
            setFailed('Invalid compression-level. Valid values are 0-9');
        }
    }
    return inputs;
}

;// CONCATENATED MODULE: ./src/shared/upload-artifact.ts



async function upload_artifact_uploadArtifact(artifactName, filesToUpload, rootDirectory, options) {
    const uploadResponse = await artifact.uploadArtifact(artifactName, filesToUpload, rootDirectory, options);
    info(`Artifact ${artifactName} has been successfully uploaded! Final size is ${uploadResponse.size} bytes. Artifact ID is ${uploadResponse.id}`);
    setOutput('artifact-id', uploadResponse.id);
    setOutput('artifact-digest', uploadResponse.digest);
    const repository = github_context.repo;
    const artifactURL = `${github_context.serverUrl}/${repository.owner}/${repository.repo}/actions/runs/${github_context.runId}/artifacts/${uploadResponse.id}`;
    info(`Artifact download URL: ${artifactURL}`);
    setOutput('artifact-url', artifactURL);
}

;// CONCATENATED MODULE: ./src/upload/upload-artifact.ts






async function deleteArtifactIfExists(artifactName) {
    try {
        await artifact.deleteArtifact(artifactName);
    }
    catch (error) {
        if (error instanceof ArtifactNotFoundError) {
            core_debug(`Skipping deletion of '${artifactName}', it does not exist`);
            return;
        }
        // Best effort, we don't want to fail the action if this fails
        core_debug(`Unable to delete artifact: ${error.message}`);
    }
}
async function run() {
    const inputs = getInputs();
    const searchResult = await findFilesToUpload(inputs.searchPath, inputs.includeHiddenFiles);
    if (searchResult.filesToUpload.length === 0) {
        // No files were found, different use cases warrant different types of behavior if nothing is found
        switch (inputs.ifNoFilesFound) {
            case NoFileOptions.warn: {
                warning(`No files were found with the provided path: ${inputs.searchPath}. No artifacts will be uploaded.`);
                break;
            }
            case NoFileOptions.error: {
                setFailed(`No files were found with the provided path: ${inputs.searchPath}. No artifacts will be uploaded.`);
                break;
            }
            case NoFileOptions.ignore: {
                info(`No files were found with the provided path: ${inputs.searchPath}. No artifacts will be uploaded.`);
                break;
            }
        }
    }
    else {
        const s = searchResult.filesToUpload.length === 1 ? '' : 's';
        info(`With the provided path, there will be ${searchResult.filesToUpload.length} file${s} uploaded`);
        core_debug(`Root artifact directory is ${searchResult.rootDirectory}`);
        // Validate that only a single file is uploaded when archive is false
        if (!inputs.archive && searchResult.filesToUpload.length > 1) {
            setFailed(`When 'archive' is set to false, only a single file can be uploaded. Found ${searchResult.filesToUpload.length} files to upload.`);
            return;
        }
        if (inputs.overwrite) {
            await deleteArtifactIfExists(inputs.artifactName);
        }
        const options = {};
        if (inputs.retentionDays) {
            options.retentionDays = inputs.retentionDays;
        }
        if (typeof inputs.compressionLevel !== 'undefined') {
            options.compressionLevel = inputs.compressionLevel;
        }
        if (!inputs.archive) {
            options.skipArchive = true;
        }
        await upload_artifact_uploadArtifact(inputs.artifactName, searchResult.filesToUpload, searchResult.rootDirectory, options);
    }
}

;// CONCATENATED MODULE: ./src/upload/index.ts


run().catch(error => {
    setFailed(error.message);
});

