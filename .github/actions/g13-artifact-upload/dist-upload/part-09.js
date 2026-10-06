            headersMapper: ContainerRestoreExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        restype2,
        comp8,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        deletedContainerName,
        deletedContainerVersion,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const renameOperationSpec = {
    path: "/{containerName}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: ContainerRenameHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerRenameExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        restype2,
        comp9,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        sourceContainerName,
        sourceLeaseId,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const container_submitBatchOperationSpec = {
    path: "/{containerName}",
    httpMethod: "POST",
    responses: {
        202: {
            bodyMapper: {
                type: { name: "Stream" },
                serializedName: "parsedResponse",
            },
            headersMapper: ContainerSubmitBatchHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerSubmitBatchExceptionHeaders,
        },
    },
    requestBody: body,
    queryParameters: [
        timeoutInSeconds,
        comp4,
        restype2,
    ],
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
    serializer: container_xmlSerializer,
};
const container_filterBlobsOperationSpec = {
    path: "/{containerName}",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: FilterBlobSegment,
            headersMapper: ContainerFilterBlobsHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerFilterBlobsExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        marker,
        maxPageSize,
        comp5,
        where,
        restype2,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const acquireLeaseOperationSpec = {
    path: "/{containerName}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: ContainerAcquireLeaseHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerAcquireLeaseExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        restype2,
        comp10,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        action,
        duration,
        proposedLeaseId,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const releaseLeaseOperationSpec = {
    path: "/{containerName}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: ContainerReleaseLeaseHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerReleaseLeaseExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        restype2,
        comp10,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        action1,
        leaseId1,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const renewLeaseOperationSpec = {
    path: "/{containerName}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: ContainerRenewLeaseHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerRenewLeaseExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        restype2,
        comp10,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        leaseId1,
        action2,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const breakLeaseOperationSpec = {
    path: "/{containerName}",
    httpMethod: "PUT",
    responses: {
        202: {
            headersMapper: ContainerBreakLeaseHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerBreakLeaseExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        restype2,
        comp10,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        action3,
        breakPeriod,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const changeLeaseOperationSpec = {
    path: "/{containerName}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: ContainerChangeLeaseHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerChangeLeaseExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        restype2,
        comp10,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        leaseId1,
        action4,
        proposedLeaseId1,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const listBlobFlatSegmentOperationSpec = {
    path: "/{containerName}",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: ListBlobsFlatSegmentResponse,
            headersMapper: ContainerListBlobFlatSegmentHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerListBlobFlatSegmentExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        comp2,
        prefix,
        marker,
        maxPageSize,
        restype2,
        include1,
        startFrom,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const listBlobHierarchySegmentOperationSpec = {
    path: "/{containerName}",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: ListBlobsHierarchySegmentResponse,
            headersMapper: ContainerListBlobHierarchySegmentHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerListBlobHierarchySegmentExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        comp2,
        prefix,
        marker,
        maxPageSize,
        restype2,
        include1,
        startFrom,
        delimiter,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
    ],
    isXML: true,
    serializer: container_xmlSerializer,
};
const container_getAccountInfoOperationSpec = {
    path: "/{containerName}",
    httpMethod: "GET",
    responses: {
        200: {
            headersMapper: ContainerGetAccountInfoHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: ContainerGetAccountInfoExceptionHeaders,
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
    serializer: container_xmlSerializer,
};
//# sourceMappingURL=container.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/operations/blob.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */



/** Class containing Blob operations. */
class BlobImpl {
    client;
    /**
     * Initialize a new instance of the class Blob class.
     * @param client Reference to the service client
     */
    constructor(client) {
        this.client = client;
    }
    /**
     * The Download operation reads or downloads a blob from the system, including its metadata and
     * properties. You can also call Download to read a snapshot.
     * @param options The options parameters.
     */
    download(options) {
        return this.client.sendOperationRequest({ options }, downloadOperationSpec);
    }
    /**
     * The Get Properties operation returns all user-defined metadata, standard HTTP properties, and system
     * properties for the blob. It does not return the content of the blob.
     * @param options The options parameters.
     */
    getProperties(options) {
        return this.client.sendOperationRequest({ options }, blob_getPropertiesOperationSpec);
    }
    /**
     * If the storage account's soft delete feature is disabled then, when a blob is deleted, it is
     * permanently removed from the storage account. If the storage account's soft delete feature is
     * enabled, then, when a blob is deleted, it is marked for deletion and becomes inaccessible
     * immediately. However, the blob service retains the blob or snapshot for the number of days specified
     * by the DeleteRetentionPolicy section of [Storage service properties]
     * (Set-Blob-Service-Properties.md). After the specified number of days has passed, the blob's data is
     * permanently removed from the storage account. Note that you continue to be charged for the
     * soft-deleted blob's storage until it is permanently removed. Use the List Blobs API and specify the
     * "include=deleted" query parameter to discover which blobs and snapshots have been soft deleted. You
     * can then use the Undelete Blob API to restore a soft-deleted blob. All other operations on a
     * soft-deleted blob or snapshot causes the service to return an HTTP status code of 404
     * (ResourceNotFound).
     * @param options The options parameters.
     */
    delete(options) {
        return this.client.sendOperationRequest({ options }, blob_deleteOperationSpec);
    }
    /**
     * Undelete a blob that was previously soft deleted
     * @param options The options parameters.
     */
    undelete(options) {
        return this.client.sendOperationRequest({ options }, undeleteOperationSpec);
    }
    /**
     * Sets the time a blob will expire and be deleted.
     * @param expiryOptions Required. Indicates mode of the expiry time
     * @param options The options parameters.
     */
    setExpiry(expiryOptions, options) {
        return this.client.sendOperationRequest({ expiryOptions, options }, setExpiryOperationSpec);
    }
    /**
     * The Set HTTP Headers operation sets system properties on the blob
     * @param options The options parameters.
     */
    setHttpHeaders(options) {
        return this.client.sendOperationRequest({ options }, setHttpHeadersOperationSpec);
    }
    /**
     * The Set Immutability Policy operation sets the immutability policy on the blob
     * @param options The options parameters.
     */
    setImmutabilityPolicy(options) {
        return this.client.sendOperationRequest({ options }, setImmutabilityPolicyOperationSpec);
    }
    /**
     * The Delete Immutability Policy operation deletes the immutability policy on the blob
     * @param options The options parameters.
     */
    deleteImmutabilityPolicy(options) {
        return this.client.sendOperationRequest({ options }, deleteImmutabilityPolicyOperationSpec);
    }
    /**
     * The Set Legal Hold operation sets a legal hold on the blob.
     * @param legalHold Specified if a legal hold should be set on the blob.
     * @param options The options parameters.
     */
    setLegalHold(legalHold, options) {
        return this.client.sendOperationRequest({ legalHold, options }, setLegalHoldOperationSpec);
    }
    /**
     * The Set Blob Metadata operation sets user-defined metadata for the specified blob as one or more
     * name-value pairs
     * @param options The options parameters.
     */
    setMetadata(options) {
        return this.client.sendOperationRequest({ options }, blob_setMetadataOperationSpec);
    }
    /**
     * [Update] The Lease Blob operation establishes and manages a lock on a blob for write and delete
     * operations
     * @param options The options parameters.
     */
    acquireLease(options) {
        return this.client.sendOperationRequest({ options }, blob_acquireLeaseOperationSpec);
    }
    /**
     * [Update] The Lease Blob operation establishes and manages a lock on a blob for write and delete
     * operations
     * @param leaseId Specifies the current lease ID on the resource.
     * @param options The options parameters.
     */
    releaseLease(leaseId, options) {
        return this.client.sendOperationRequest({ leaseId, options }, blob_releaseLeaseOperationSpec);
    }
    /**
     * [Update] The Lease Blob operation establishes and manages a lock on a blob for write and delete
     * operations
     * @param leaseId Specifies the current lease ID on the resource.
     * @param options The options parameters.
     */
    renewLease(leaseId, options) {
        return this.client.sendOperationRequest({ leaseId, options }, blob_renewLeaseOperationSpec);
    }
    /**
     * [Update] The Lease Blob operation establishes and manages a lock on a blob for write and delete
     * operations
     * @param leaseId Specifies the current lease ID on the resource.
     * @param proposedLeaseId Proposed lease ID, in a GUID string format. The Blob service returns 400
     *                        (Invalid request) if the proposed lease ID is not in the correct format. See Guid Constructor
     *                        (String) for a list of valid GUID string formats.
     * @param options The options parameters.
     */
    changeLease(leaseId, proposedLeaseId, options) {
        return this.client.sendOperationRequest({ leaseId, proposedLeaseId, options }, blob_changeLeaseOperationSpec);
    }
    /**
     * [Update] The Lease Blob operation establishes and manages a lock on a blob for write and delete
     * operations
     * @param options The options parameters.
     */
    breakLease(options) {
        return this.client.sendOperationRequest({ options }, blob_breakLeaseOperationSpec);
    }
    /**
     * The Create Snapshot operation creates a read-only snapshot of a blob
     * @param options The options parameters.
     */
    createSnapshot(options) {
        return this.client.sendOperationRequest({ options }, createSnapshotOperationSpec);
    }
    /**
     * The Start Copy From URL operation copies a blob or an internet resource to a new blob.
     * @param copySource Specifies the name of the source page blob snapshot. This value is a URL of up to
     *                   2 KB in length that specifies a page blob snapshot. The value should be URL-encoded as it would
     *                   appear in a request URI. The source blob must either be public or must be authenticated via a shared
     *                   access signature.
     * @param options The options parameters.
     */
    startCopyFromURL(copySource, options) {
        return this.client.sendOperationRequest({ copySource, options }, startCopyFromURLOperationSpec);
    }
    /**
     * The Copy From URL operation copies a blob or an internet resource to a new blob. It will not return
     * a response until the copy is complete.
     * @param copySource Specifies the name of the source page blob snapshot. This value is a URL of up to
     *                   2 KB in length that specifies a page blob snapshot. The value should be URL-encoded as it would
     *                   appear in a request URI. The source blob must either be public or must be authenticated via a shared
     *                   access signature.
     * @param options The options parameters.
     */
    copyFromURL(copySource, options) {
        return this.client.sendOperationRequest({ copySource, options }, copyFromURLOperationSpec);
    }
    /**
     * The Abort Copy From URL operation aborts a pending Copy From URL operation, and leaves a destination
     * blob with zero length and full metadata.
     * @param copyId The copy identifier provided in the x-ms-copy-id header of the original Copy Blob
     *               operation.
     * @param options The options parameters.
     */
    abortCopyFromURL(copyId, options) {
        return this.client.sendOperationRequest({ copyId, options }, abortCopyFromURLOperationSpec);
    }
    /**
     * The Set Tier operation sets the tier on a blob. The operation is allowed on a page blob in a premium
     * storage account and on a block blob in a blob storage account (locally redundant storage only). A
     * premium page blob's tier determines the allowed size, IOPS, and bandwidth of the blob. A block
     * blob's tier determines Hot/Cool/Archive storage type. This operation does not update the blob's
     * ETag.
     * @param tier Indicates the tier to be set on the blob.
     * @param options The options parameters.
     */
    setTier(tier, options) {
        return this.client.sendOperationRequest({ tier, options }, setTierOperationSpec);
    }
    /**
     * Returns the sku name and account kind
     * @param options The options parameters.
     */
    getAccountInfo(options) {
        return this.client.sendOperationRequest({ options }, blob_getAccountInfoOperationSpec);
    }
    /**
     * The Query operation enables users to select/project on blob data by providing simple query
     * expressions.
     * @param options The options parameters.
     */
    query(options) {
        return this.client.sendOperationRequest({ options }, queryOperationSpec);
    }
    /**
     * The Get Tags operation enables users to get the tags associated with a blob.
     * @param options The options parameters.
     */
    getTags(options) {
        return this.client.sendOperationRequest({ options }, getTagsOperationSpec);
    }
    /**
     * The Set Tags operation enables users to set tags on a blob.
     * @param options The options parameters.
     */
    setTags(options) {
        return this.client.sendOperationRequest({ options }, setTagsOperationSpec);
    }
}
// Operation Specifications
const blob_xmlSerializer = createSerializer(mappers_namespaceObject, /* isXml */ true);
const downloadOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: {
                type: { name: "Stream" },
                serializedName: "parsedResponse",
            },
            headersMapper: BlobDownloadHeaders,
        },
        206: {
            bodyMapper: {
                type: { name: "Stream" },
                serializedName: "parsedResponse",
            },
            headersMapper: BlobDownloadHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobDownloadExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        snapshot,
        versionId,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        range,
        rangeGetContentMD5,
        rangeGetContentCRC64,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const blob_getPropertiesOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "HEAD",
    responses: {
        200: {
            headersMapper: BlobGetPropertiesHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobGetPropertiesExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        snapshot,
        versionId,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const blob_deleteOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "DELETE",
    responses: {
        202: {
            headersMapper: BlobDeleteHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobDeleteExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        snapshot,
        versionId,
        blobDeleteType,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        ifMatch,
        ifNoneMatch,
        ifTags,
        deleteSnapshots,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const undeleteOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: BlobUndeleteHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobUndeleteExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp8],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const setExpiryOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: BlobSetExpiryHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobSetExpiryExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp11],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        expiryOptions,
        expiresOn,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const setHttpHeadersOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: BlobSetHttpHeadersHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobSetHttpHeadersExceptionHeaders,
        },
    },
    queryParameters: [comp, timeoutInSeconds],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        ifMatch,
        ifNoneMatch,
        ifTags,
        blobCacheControl,
        blobContentType,
        blobContentMD5,
        blobContentEncoding,
        blobContentLanguage,
        blobContentDisposition,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const setImmutabilityPolicyOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: BlobSetImmutabilityPolicyHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobSetImmutabilityPolicyExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        snapshot,
        versionId,
        comp12,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifUnmodifiedSince,
        immutabilityPolicyExpiry,
        immutabilityPolicyMode,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const deleteImmutabilityPolicyOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "DELETE",
    responses: {
        200: {
            headersMapper: BlobDeleteImmutabilityPolicyHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobDeleteImmutabilityPolicyExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        snapshot,
        versionId,
        comp12,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const setLegalHoldOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: BlobSetLegalHoldHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobSetLegalHoldExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        snapshot,
        versionId,
        comp13,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        legalHold,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const blob_setMetadataOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: BlobSetMetadataHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobSetMetadataExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp6],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        metadata,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        encryptionScope,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const blob_acquireLeaseOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: BlobAcquireLeaseHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobAcquireLeaseExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp10],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        action,
        duration,
        proposedLeaseId,
        ifMatch,
        ifNoneMatch,
        ifTags,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const blob_releaseLeaseOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: BlobReleaseLeaseHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobReleaseLeaseExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp10],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        action1,
        leaseId1,
        ifMatch,
        ifNoneMatch,
        ifTags,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const blob_renewLeaseOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: BlobRenewLeaseHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobRenewLeaseExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp10],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        leaseId1,
        action2,
        ifMatch,
        ifNoneMatch,
        ifTags,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const blob_changeLeaseOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: BlobChangeLeaseHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobChangeLeaseExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp10],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        leaseId1,
        action4,
        proposedLeaseId1,
        ifMatch,
        ifNoneMatch,
        ifTags,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const blob_breakLeaseOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        202: {
            headersMapper: BlobBreakLeaseHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobBreakLeaseExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp10],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        action3,
        breakPeriod,
        ifMatch,
        ifNoneMatch,
        ifTags,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const createSnapshotOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: BlobCreateSnapshotHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobCreateSnapshotExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp14],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        metadata,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        encryptionScope,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const startCopyFromURLOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        202: {
            headersMapper: BlobStartCopyFromURLHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobStartCopyFromURLExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        metadata,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        ifMatch,
        ifNoneMatch,
        ifTags,
        immutabilityPolicyExpiry,
        immutabilityPolicyMode,
        tier,
        rehydratePriority,
        sourceIfModifiedSince,
        sourceIfUnmodifiedSince,
        sourceIfMatch,
        sourceIfNoneMatch,
        sourceIfTags,
        copySource,
        blobTagsString,
        sealBlob,
        legalHold1,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const copyFromURLOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        202: {
            headersMapper: BlobCopyFromURLHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobCopyFromURLExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        metadata,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        ifMatch,
        ifNoneMatch,
        ifTags,
        immutabilityPolicyExpiry,
        immutabilityPolicyMode,
        encryptionScope,
        tier,
        sourceIfModifiedSince,
        sourceIfUnmodifiedSince,
        sourceIfMatch,
        sourceIfNoneMatch,
        copySource,
        blobTagsString,
        legalHold1,
        xMsRequiresSync,
        sourceContentMD5,
        copySourceAuthorization,
        copySourceTags,
        fileRequestIntent,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const abortCopyFromURLOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        204: {
            headersMapper: BlobAbortCopyFromURLHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobAbortCopyFromURLExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        comp15,
        copyId,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        copyActionAbortConstant,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const setTierOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: BlobSetTierHeaders,
        },
        202: {
            headersMapper: BlobSetTierHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobSetTierExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        snapshot,
        versionId,
        comp16,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifTags,
        rehydratePriority,
        tier1,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const blob_getAccountInfoOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "GET",
    responses: {
        200: {
            headersMapper: BlobGetAccountInfoHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobGetAccountInfoExceptionHeaders,
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
    serializer: blob_xmlSerializer,
};
const queryOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "POST",
    responses: {
        200: {
            bodyMapper: {
                type: { name: "Stream" },
                serializedName: "parsedResponse",
            },
            headersMapper: BlobQueryHeaders,
        },
        206: {
            bodyMapper: {
                type: { name: "Stream" },
                serializedName: "parsedResponse",
            },
            headersMapper: BlobQueryHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobQueryExceptionHeaders,
        },
    },
    requestBody: queryRequest,
    queryParameters: [
        timeoutInSeconds,
        snapshot,
        comp17,
    ],
    urlParameters: [url],
    headerParameters: [
        contentType,
        accept,
        version,
        requestId,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "xml",
    serializer: blob_xmlSerializer,
};
const getTagsOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: BlobTags,
            headersMapper: BlobGetTagsHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobGetTagsExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        snapshot,
        versionId,
        comp18,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifTags,
        ifModifiedSince1,
        ifUnmodifiedSince1,
        ifMatch1,
        ifNoneMatch1,
    ],
    isXML: true,
    serializer: blob_xmlSerializer,
};
const setTagsOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        204: {
            headersMapper: BlobSetTagsHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlobSetTagsExceptionHeaders,
        },
    },
    requestBody: tags,
    queryParameters: [
        timeoutInSeconds,
        versionId,
        comp18,
    ],
    urlParameters: [url],
    headerParameters: [
        contentType,
        accept,
        version,
        requestId,
        leaseId,
        ifTags,
        ifModifiedSince1,
        ifUnmodifiedSince1,
        ifMatch1,
        ifNoneMatch1,
        transactionalContentMD5,
        transactionalContentCrc64,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "xml",
    serializer: blob_xmlSerializer,
};
//# sourceMappingURL=blob.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/operations/pageBlob.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */



/** Class containing PageBlob operations. */
class PageBlobImpl {
    client;
    /**
     * Initialize a new instance of the class PageBlob class.
     * @param client Reference to the service client
     */
    constructor(client) {
        this.client = client;
    }
    /**
     * The Create operation creates a new page blob.
     * @param contentLength The length of the request.
     * @param blobContentLength This header specifies the maximum size for the page blob, up to 1 TB. The
     *                          page blob size must be aligned to a 512-byte boundary.
     * @param options The options parameters.
     */
    create(contentLength, blobContentLength, options) {
        return this.client.sendOperationRequest({ contentLength, blobContentLength, options }, pageBlob_createOperationSpec);
    }
    /**
     * The Upload Pages operation writes a range of pages to a page blob
     * @param contentLength The length of the request.
     * @param body Initial data
     * @param options The options parameters.
     */
    uploadPages(contentLength, body, options) {
        return this.client.sendOperationRequest({ contentLength, body, options }, uploadPagesOperationSpec);
    }
    /**
     * The Clear Pages operation clears a set of pages from a page blob
     * @param contentLength The length of the request.
     * @param options The options parameters.
     */
    clearPages(contentLength, options) {
        return this.client.sendOperationRequest({ contentLength, options }, clearPagesOperationSpec);
    }
    /**
     * The Upload Pages operation writes a range of pages to a page blob where the contents are read from a
     * URL
     * @param sourceUrl Specify a URL to the copy source.
     * @param sourceRange Bytes of source data in the specified range. The length of this range should
     *                    match the ContentLength header and x-ms-range/Range destination range header.
     * @param contentLength The length of the request.
     * @param range The range of bytes to which the source range would be written. The range should be 512
     *              aligned and range-end is required.
     * @param options The options parameters.
     */
    uploadPagesFromURL(sourceUrl, sourceRange, contentLength, range, options) {
        return this.client.sendOperationRequest({ sourceUrl, sourceRange, contentLength, range, options }, uploadPagesFromURLOperationSpec);
    }
    /**
     * The Get Page Ranges operation returns the list of valid page ranges for a page blob or snapshot of a
     * page blob
     * @param options The options parameters.
     */
    getPageRanges(options) {
        return this.client.sendOperationRequest({ options }, getPageRangesOperationSpec);
    }
    /**
     * The Get Page Ranges Diff operation returns the list of valid page ranges for a page blob that were
     * changed between target blob and previous snapshot.
     * @param options The options parameters.
     */
    getPageRangesDiff(options) {
        return this.client.sendOperationRequest({ options }, getPageRangesDiffOperationSpec);
    }
    /**
     * Resize the Blob
     * @param blobContentLength This header specifies the maximum size for the page blob, up to 1 TB. The
     *                          page blob size must be aligned to a 512-byte boundary.
     * @param options The options parameters.
     */
    resize(blobContentLength, options) {
        return this.client.sendOperationRequest({ blobContentLength, options }, resizeOperationSpec);
    }
    /**
     * Update the sequence number of the blob
     * @param sequenceNumberAction Required if the x-ms-blob-sequence-number header is set for the request.
     *                             This property applies to page blobs only. This property indicates how the service should modify the
     *                             blob's sequence number
     * @param options The options parameters.
     */
    updateSequenceNumber(sequenceNumberAction, options) {
        return this.client.sendOperationRequest({ sequenceNumberAction, options }, updateSequenceNumberOperationSpec);
    }
    /**
     * The Copy Incremental operation copies a snapshot of the source page blob to a destination page blob.
     * The snapshot is copied such that only the differential changes between the previously copied
     * snapshot are transferred to the destination. The copied snapshots are complete copies of the
     * original snapshot and can be read or copied from as usual. This API is supported since REST version
     * 2016-05-31.
     * @param copySource Specifies the name of the source page blob snapshot. This value is a URL of up to
     *                   2 KB in length that specifies a page blob snapshot. The value should be URL-encoded as it would
     *                   appear in a request URI. The source blob must either be public or must be authenticated via a shared
     *                   access signature.
     * @param options The options parameters.
     */
    copyIncremental(copySource, options) {
        return this.client.sendOperationRequest({ copySource, options }, copyIncrementalOperationSpec);
    }
}
// Operation Specifications
const pageBlob_xmlSerializer = createSerializer(mappers_namespaceObject, /* isXml */ true);
const pageBlob_createOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: PageBlobCreateHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: PageBlobCreateExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        contentLength,
        metadata,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        blobCacheControl,
        blobContentType,
        blobContentMD5,
        blobContentEncoding,
        blobContentLanguage,
        blobContentDisposition,
        immutabilityPolicyExpiry,
        immutabilityPolicyMode,
        encryptionScope,
        tier,
        blobTagsString,
        legalHold1,
        blobType,
        blobContentLength,
        blobSequenceNumber,
    ],
    isXML: true,
    serializer: pageBlob_xmlSerializer,
};
const uploadPagesOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: PageBlobUploadPagesHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: PageBlobUploadPagesExceptionHeaders,
        },
    },
    requestBody: body1,
    queryParameters: [timeoutInSeconds, comp19],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        contentLength,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        range,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        encryptionScope,
        transactionalContentMD5,
        transactionalContentCrc64,
        contentType1,
        accept2,
        pageWrite,
        ifSequenceNumberLessThanOrEqualTo,
        ifSequenceNumberLessThan,
        ifSequenceNumberEqualTo,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "binary",
    serializer: pageBlob_xmlSerializer,
};
const clearPagesOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: PageBlobClearPagesHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: PageBlobClearPagesExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp19],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        contentLength,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        range,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        encryptionScope,
        ifSequenceNumberLessThanOrEqualTo,
        ifSequenceNumberLessThan,
        ifSequenceNumberEqualTo,
        pageWrite1,
    ],
    isXML: true,
    serializer: pageBlob_xmlSerializer,
};
const uploadPagesFromURLOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: PageBlobUploadPagesFromURLHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: PageBlobUploadPagesFromURLExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp19],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        contentLength,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        encryptionScope,
        sourceIfModifiedSince,
        sourceIfUnmodifiedSince,
        sourceIfMatch,
        sourceIfNoneMatch,
        sourceContentMD5,
        copySourceAuthorization,
        fileRequestIntent,
        pageWrite,
        ifSequenceNumberLessThanOrEqualTo,
        ifSequenceNumberLessThan,
        ifSequenceNumberEqualTo,
        sourceUrl,
        sourceRange,
        sourceContentCrc64,
        range1,
    ],
    isXML: true,
    serializer: pageBlob_xmlSerializer,
};
const getPageRangesOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: PageList,
            headersMapper: PageBlobGetPageRangesHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: PageBlobGetPageRangesExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        marker,
        maxPageSize,
        snapshot,
        comp20,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        range,
        ifMatch,
        ifNoneMatch,
        ifTags,
    ],
    isXML: true,
    serializer: pageBlob_xmlSerializer,
};
const getPageRangesDiffOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: PageList,
            headersMapper: PageBlobGetPageRangesDiffHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: PageBlobGetPageRangesDiffExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        marker,
        maxPageSize,
        snapshot,
        comp20,
        prevsnapshot,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        range,
        ifMatch,
        ifNoneMatch,
        ifTags,
        prevSnapshotUrl,
    ],
    isXML: true,
    serializer: pageBlob_xmlSerializer,
};
const resizeOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: PageBlobResizeHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: PageBlobResizeExceptionHeaders,
        },
    },
    queryParameters: [comp, timeoutInSeconds],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        encryptionScope,
        blobContentLength,
    ],
    isXML: true,
    serializer: pageBlob_xmlSerializer,
};
const updateSequenceNumberOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: PageBlobUpdateSequenceNumberHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: PageBlobUpdateSequenceNumberExceptionHeaders,
        },
    },
    queryParameters: [comp, timeoutInSeconds],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        ifMatch,
        ifNoneMatch,
        ifTags,
        blobSequenceNumber,
        sequenceNumberAction,
    ],
    isXML: true,
    serializer: pageBlob_xmlSerializer,
};
const copyIncrementalOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        202: {
            headersMapper: PageBlobCopyIncrementalHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: PageBlobCopyIncrementalExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp21],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        ifModifiedSince,
        ifUnmodifiedSince,
        ifMatch,
        ifNoneMatch,
        ifTags,
        copySource,
    ],
    isXML: true,
    serializer: pageBlob_xmlSerializer,
};
//# sourceMappingURL=pageBlob.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/operations/appendBlob.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */



/** Class containing AppendBlob operations. */
class AppendBlobImpl {
    client;
    /**
     * Initialize a new instance of the class AppendBlob class.
     * @param client Reference to the service client
     */
    constructor(client) {
        this.client = client;
    }
    /**
     * The Create Append Blob operation creates a new append blob.
     * @param contentLength The length of the request.
     * @param options The options parameters.
     */
    create(contentLength, options) {
        return this.client.sendOperationRequest({ contentLength, options }, appendBlob_createOperationSpec);
    }
    /**
     * The Append Block operation commits a new block of data to the end of an existing append blob. The
     * Append Block operation is permitted only if the blob was created with x-ms-blob-type set to
     * AppendBlob. Append Block is supported only on version 2015-02-21 version or later.
     * @param contentLength The length of the request.
     * @param body Initial data
     * @param options The options parameters.
     */
    appendBlock(contentLength, body, options) {
        return this.client.sendOperationRequest({ contentLength, body, options }, appendBlockOperationSpec);
    }
    /**
     * The Append Block operation commits a new block of data to the end of an existing append blob where
     * the contents are read from a source url. The Append Block operation is permitted only if the blob
     * was created with x-ms-blob-type set to AppendBlob. Append Block is supported only on version
     * 2015-02-21 version or later.
     * @param sourceUrl Specify a URL to the copy source.
     * @param contentLength The length of the request.
     * @param options The options parameters.
     */
    appendBlockFromUrl(sourceUrl, contentLength, options) {
        return this.client.sendOperationRequest({ sourceUrl, contentLength, options }, appendBlockFromUrlOperationSpec);
    }
    /**
     * The Seal operation seals the Append Blob to make it read-only. Seal is supported only on version
     * 2019-12-12 version or later.
     * @param options The options parameters.
     */
    seal(options) {
        return this.client.sendOperationRequest({ options }, sealOperationSpec);
    }
}
// Operation Specifications
const appendBlob_xmlSerializer = createSerializer(mappers_namespaceObject, /* isXml */ true);
const appendBlob_createOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: AppendBlobCreateHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: AppendBlobCreateExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        contentLength,
        metadata,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        blobCacheControl,
        blobContentType,
        blobContentMD5,
        blobContentEncoding,
        blobContentLanguage,
        blobContentDisposition,
        immutabilityPolicyExpiry,
        immutabilityPolicyMode,
        encryptionScope,
        blobTagsString,
        legalHold1,
        blobType1,
    ],
    isXML: true,
    serializer: appendBlob_xmlSerializer,
};
const appendBlockOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: AppendBlobAppendBlockHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: AppendBlobAppendBlockExceptionHeaders,
        },
    },
    requestBody: body1,
    queryParameters: [timeoutInSeconds, comp22],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        contentLength,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        encryptionScope,
        transactionalContentMD5,
        transactionalContentCrc64,
        contentType1,
        accept2,
        maxSize,
        appendPosition,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "binary",
    serializer: appendBlob_xmlSerializer,
};
const appendBlockFromUrlOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: AppendBlobAppendBlockFromUrlHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: AppendBlobAppendBlockFromUrlExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp22],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        contentLength,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        encryptionScope,
        sourceIfModifiedSince,
        sourceIfUnmodifiedSince,
        sourceIfMatch,
        sourceIfNoneMatch,
        sourceContentMD5,
        copySourceAuthorization,
        fileRequestIntent,
        transactionalContentMD5,
        sourceUrl,
        sourceContentCrc64,
        maxSize,
        appendPosition,
        sourceRange1,
    ],
    isXML: true,
    serializer: appendBlob_xmlSerializer,
};
const sealOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        200: {
            headersMapper: AppendBlobSealHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: AppendBlobSealExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds, comp23],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        ifMatch,
        ifNoneMatch,
        appendPosition,
    ],
    isXML: true,
    serializer: appendBlob_xmlSerializer,
};
//# sourceMappingURL=appendBlob.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/operations/blockBlob.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */



/** Class containing BlockBlob operations. */
class BlockBlobImpl {
    client;
    /**
     * Initialize a new instance of the class BlockBlob class.
     * @param client Reference to the service client
     */
    constructor(client) {
        this.client = client;
    }
    /**
     * The Upload Block Blob operation updates the content of an existing block blob. Updating an existing
     * block blob overwrites any existing metadata on the blob. Partial updates are not supported with Put
     * Blob; the content of the existing blob is overwritten with the content of the new blob. To perform a
     * partial update of the content of a block blob, use the Put Block List operation.
     * @param contentLength The length of the request.
     * @param body Initial data
     * @param options The options parameters.
     */
    upload(contentLength, body, options) {
        return this.client.sendOperationRequest({ contentLength, body, options }, uploadOperationSpec);
    }
    /**
     * The Put Blob from URL operation creates a new Block Blob where the contents of the blob are read
     * from a given URL.  This API is supported beginning with the 2020-04-08 version. Partial updates are
     * not supported with Put Blob from URL; the content of an existing blob is overwritten with the
     * content of the new blob.  To perform partial updates to a block blob’s contents using a source URL,
     * use the Put Block from URL API in conjunction with Put Block List.
     * @param contentLength The length of the request.
     * @param copySource Specifies the name of the source page blob snapshot. This value is a URL of up to
     *                   2 KB in length that specifies a page blob snapshot. The value should be URL-encoded as it would
     *                   appear in a request URI. The source blob must either be public or must be authenticated via a shared
     *                   access signature.
     * @param options The options parameters.
     */
    putBlobFromUrl(contentLength, copySource, options) {
        return this.client.sendOperationRequest({ contentLength, copySource, options }, putBlobFromUrlOperationSpec);
    }
    /**
     * The Stage Block operation creates a new block to be committed as part of a blob
     * @param blockId A valid Base64 string value that identifies the block. Prior to encoding, the string
     *                must be less than or equal to 64 bytes in size. For a given blob, the length of the value specified
     *                for the blockid parameter must be the same size for each block.
     * @param contentLength The length of the request.
     * @param body Initial data
     * @param options The options parameters.
     */
    stageBlock(blockId, contentLength, body, options) {
        return this.client.sendOperationRequest({ blockId, contentLength, body, options }, stageBlockOperationSpec);
    }
    /**
     * The Stage Block operation creates a new block to be committed as part of a blob where the contents
     * are read from a URL.
     * @param blockId A valid Base64 string value that identifies the block. Prior to encoding, the string
     *                must be less than or equal to 64 bytes in size. For a given blob, the length of the value specified
     *                for the blockid parameter must be the same size for each block.
     * @param contentLength The length of the request.
     * @param sourceUrl Specify a URL to the copy source.
     * @param options The options parameters.
     */
    stageBlockFromURL(blockId, contentLength, sourceUrl, options) {
        return this.client.sendOperationRequest({ blockId, contentLength, sourceUrl, options }, stageBlockFromURLOperationSpec);
    }
    /**
     * The Commit Block List operation writes a blob by specifying the list of block IDs that make up the
     * blob. In order to be written as part of a blob, a block must have been successfully written to the
     * server in a prior Put Block operation. You can call Put Block List to update a blob by uploading
     * only those blocks that have changed, then committing the new and existing blocks together. You can
     * do this by specifying whether to commit a block from the committed block list or from the
     * uncommitted block list, or to commit the most recently uploaded version of the block, whichever list
     * it may belong to.
     * @param blocks Blob Blocks.
     * @param options The options parameters.
     */
    commitBlockList(blocks, options) {
        return this.client.sendOperationRequest({ blocks, options }, commitBlockListOperationSpec);
    }
    /**
     * The Get Block List operation retrieves the list of blocks that have been uploaded as part of a block
     * blob
     * @param listType Specifies whether to return the list of committed blocks, the list of uncommitted
     *                 blocks, or both lists together.
     * @param options The options parameters.
     */
    getBlockList(listType, options) {
        return this.client.sendOperationRequest({ listType, options }, getBlockListOperationSpec);
    }
}
// Operation Specifications
const blockBlob_xmlSerializer = createSerializer(mappers_namespaceObject, /* isXml */ true);
const uploadOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: BlockBlobUploadHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlockBlobUploadExceptionHeaders,
        },
    },
    requestBody: body1,
    queryParameters: [timeoutInSeconds],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        contentLength,
        metadata,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        blobCacheControl,
        blobContentType,
        blobContentMD5,
        blobContentEncoding,
        blobContentLanguage,
        blobContentDisposition,
        immutabilityPolicyExpiry,
        immutabilityPolicyMode,
        encryptionScope,
        tier,
        blobTagsString,
        legalHold1,
        transactionalContentMD5,
        transactionalContentCrc64,
        contentType1,
        accept2,
        blobType2,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "binary",
    serializer: blockBlob_xmlSerializer,
};
const putBlobFromUrlOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: BlockBlobPutBlobFromUrlHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlockBlobPutBlobFromUrlExceptionHeaders,
        },
    },
    queryParameters: [timeoutInSeconds],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        contentLength,
        metadata,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        blobCacheControl,
        blobContentType,
        blobContentMD5,
        blobContentEncoding,
        blobContentLanguage,
        blobContentDisposition,
        encryptionScope,
        tier,
        sourceIfModifiedSince,
        sourceIfUnmodifiedSince,
        sourceIfMatch,
        sourceIfNoneMatch,
        sourceIfTags,
        copySource,
        blobTagsString,
        sourceContentMD5,
        copySourceAuthorization,
        copySourceTags,
        fileRequestIntent,
        transactionalContentMD5,
        blobType2,
        copySourceBlobProperties,
    ],
    isXML: true,
    serializer: blockBlob_xmlSerializer,
};
const stageBlockOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: BlockBlobStageBlockHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlockBlobStageBlockExceptionHeaders,
        },
    },
    requestBody: body1,
    queryParameters: [
        timeoutInSeconds,
        comp24,
        blockId,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        contentLength,
        leaseId,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        encryptionScope,
        transactionalContentMD5,
        transactionalContentCrc64,
        contentType1,
        accept2,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "binary",
    serializer: blockBlob_xmlSerializer,
};
const stageBlockFromURLOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: BlockBlobStageBlockFromURLHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlockBlobStageBlockFromURLExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        comp24,
        blockId,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        contentLength,
        leaseId,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        encryptionScope,
        sourceIfModifiedSince,
        sourceIfUnmodifiedSince,
        sourceIfMatch,
        sourceIfNoneMatch,
        sourceContentMD5,
        copySourceAuthorization,
        fileRequestIntent,
        sourceUrl,
        sourceContentCrc64,
        sourceRange1,
    ],
    isXML: true,
    serializer: blockBlob_xmlSerializer,
};
const commitBlockListOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "PUT",
    responses: {
        201: {
            headersMapper: BlockBlobCommitBlockListHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlockBlobCommitBlockListExceptionHeaders,
        },
    },
    requestBody: blocks,
    queryParameters: [timeoutInSeconds, comp25],
    urlParameters: [url],
    headerParameters: [
        contentType,
        accept,
        version,
        requestId,
        metadata,
        leaseId,
        ifModifiedSince,
        ifUnmodifiedSince,
        encryptionKey,
        encryptionKeySha256,
        encryptionAlgorithm,
        ifMatch,
        ifNoneMatch,
        ifTags,
        blobCacheControl,
        blobContentType,
        blobContentMD5,
        blobContentEncoding,
        blobContentLanguage,
        blobContentDisposition,
        immutabilityPolicyExpiry,
        immutabilityPolicyMode,
        encryptionScope,
        tier,
        blobTagsString,
        legalHold1,
        transactionalContentMD5,
        transactionalContentCrc64,
    ],
    isXML: true,
    contentType: "application/xml; charset=utf-8",
    mediaType: "xml",
    serializer: blockBlob_xmlSerializer,
};
const getBlockListOperationSpec = {
    path: "/{containerName}/{blob}",
    httpMethod: "GET",
    responses: {
        200: {
            bodyMapper: BlockList,
            headersMapper: BlockBlobGetBlockListHeaders,
        },
        default: {
            bodyMapper: StorageError,
            headersMapper: BlockBlobGetBlockListExceptionHeaders,
        },
    },
    queryParameters: [
        timeoutInSeconds,
        snapshot,
        comp25,
        listType,
    ],
    urlParameters: [url],
    headerParameters: [
        version,
        requestId,
        accept1,
        leaseId,
        ifTags,
    ],
    isXML: true,
    serializer: blockBlob_xmlSerializer,
};
//# sourceMappingURL=blockBlob.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/operations/index.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */






//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/storageClient.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */


class StorageClient extends ExtendedServiceClient {
    url;
    version;
    /**
     * Initializes a new instance of the StorageClient class.
     * @param url The URL of the service account, container, or blob that is the target of the desired
     *            operation.
     * @param options The parameter options
     */
    constructor(url, options) {
        if (url === undefined) {
            throw new Error("'url' cannot be null");
        }
        // Initializing default values for options
        if (!options) {
            options = {};
        }
        const defaults = {
            requestContentType: "application/json; charset=utf-8",
        };
        const packageDetails = `azsdk-js-azure-storage-blob/12.30.0`;
        const userAgentPrefix = options.userAgentOptions && options.userAgentOptions.userAgentPrefix
            ? `${options.userAgentOptions.userAgentPrefix} ${packageDetails}`
            : `${packageDetails}`;
        const optionsWithDefaults = {
            ...defaults,
            ...options,
            userAgentOptions: {
                userAgentPrefix,
            },
            endpoint: options.endpoint ?? options.baseUri ?? "{url}",
        };
        super(optionsWithDefaults);
        // Parameter assignments
        this.url = url;
        // Assigning values to Constant parameters
        this.version = options.version || "2026-02-06";
        this.service = new ServiceImpl(this);
        this.container = new ContainerImpl(this);
        this.blob = new BlobImpl(this);
        this.pageBlob = new PageBlobImpl(this);
        this.appendBlob = new AppendBlobImpl(this);
        this.blockBlob = new BlockBlobImpl(this);
    }
    service;
    container;
    blob;
    pageBlob;
    appendBlob;
    blockBlob;
}
//# sourceMappingURL=storageClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/generated/src/index.js
/*
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT License.
 *
 * Code generated by Microsoft (R) AutoRest Code Generator.
 * Changes may cause incorrect behavior and will be lost if the code is regenerated.
 */



//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/StorageContextClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * @internal
 */
class StorageContextClient extends StorageClient {
    async sendOperationRequest(operationArguments, operationSpec) {
        const operationSpecToSend = { ...operationSpec };
        if (operationSpecToSend.path === "/{containerName}" ||
            operationSpecToSend.path === "/{containerName}/{blob}") {
            operationSpecToSend.path = "";
        }
        return super.sendOperationRequest(operationArguments, operationSpecToSend);
    }
}
//# sourceMappingURL=StorageContextClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/utils/utils.common.js
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
function utils_common_escapeURLPath(url) {
    const urlParsed = new URL(url);
    let path = urlParsed.pathname;
    path = path || "/";
    path = utils_utils_common_escape(path);
    urlParsed.pathname = path;
    return urlParsed.toString();
}
function utils_common_getProxyUriFromDevConnString(connectionString) {
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
function utils_common_getValueInConnString(connectionString, argument) {
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
function utils_common_extractConnectionStringParts(connectionString) {
    let proxyUri = "";
    if (connectionString.startsWith("UseDevelopmentStorage=true")) {
        // Development connection string
        proxyUri = utils_common_getProxyUriFromDevConnString(connectionString);
        connectionString = utils_constants_DevelopmentConnectionString;
    }
    // Matching BlobEndpoint in the Account connection string
    let blobEndpoint = utils_common_getValueInConnString(connectionString, "BlobEndpoint");
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
        accountName = utils_common_getValueInConnString(connectionString, "AccountName");
        accountKey = Buffer.from(utils_common_getValueInConnString(connectionString, "AccountKey"), "base64");
        if (!blobEndpoint) {
            // BlobEndpoint is not present in the Account connection string
            // Can be obtained from `${defaultEndpointsProtocol}://${accountName}.blob.${endpointSuffix}`
            defaultEndpointsProtocol = utils_common_getValueInConnString(connectionString, "DefaultEndpointsProtocol");
            const protocol = defaultEndpointsProtocol.toLowerCase();
            if (protocol !== "https" && protocol !== "http") {
                throw new Error("Invalid DefaultEndpointsProtocol in the provided Connection String. Expecting 'https' or 'http'");
            }
            endpointSuffix = utils_common_getValueInConnString(connectionString, "EndpointSuffix");
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
        let accountSas = utils_common_getValueInConnString(connectionString, "SharedAccessSignature");
        let accountName = utils_common_getValueInConnString(connectionString, "AccountName");
        // if accountName is empty, try to read it from BlobEndpoint
        if (!accountName) {
            accountName = utils_common_getAccountNameFromUrl(blobEndpoint);
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
function utils_utils_common_escape(text) {
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
function utils_common_appendToURLPath(url, name) {
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
function utils_common_setURLParameter(url, name, value) {
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
function utils_common_getURLParameter(url, name) {
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
function utils_common_setURLHost(url, host) {
    const urlParsed = new URL(url);
    urlParsed.hostname = host;
    return urlParsed.toString();
}
/**
 * Get URL path from an URL string.
 *
 * @param url - Source URL string
 */
function utils_common_getURLPath(url) {
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
function utils_common_getURLScheme(url) {
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
function utils_common_getURLPathAndQuery(url) {
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
function utils_common_getURLQueries(url) {
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
function utils_common_appendToURLQuery(url, queryParts) {
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
function utils_common_truncatedISO8061Date(date, withMilliseconds = true) {
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
function utils_common_base64encode(content) {
    return !esm_isNodeLike ? btoa(content) : Buffer.from(content).toString("base64");
}
/**
 * Base64 decode.
 *
 * @param encodedString -
 */
function utils_common_base64decode(encodedString) {
    return !isNodeLike ? atob(encodedString) : Buffer.from(encodedString, "base64").toString();
}
/**
 * Generate a 64 bytes base64 block ID string.
 *
 * @param blockIndex -
 */
function utils_common_generateBlockID(blockIDPrefix, blockIndex) {
    // To generate a 64 bytes base64 string, source string should be 48
    const maxSourceStringLength = 48;
    // A blob can have a maximum of 100,000 uncommitted blocks at any given time
    const maxBlockIndexLength = 6;
    const maxAllowedBlockIDPrefixLength = maxSourceStringLength - maxBlockIndexLength;
    if (blockIDPrefix.length > maxAllowedBlockIDPrefixLength) {
        blockIDPrefix = blockIDPrefix.slice(0, maxAllowedBlockIDPrefixLength);
    }
    const res = blockIDPrefix +
        utils_common_padStart(blockIndex.toString(), maxSourceStringLength - blockIDPrefix.length, "0");
    return utils_common_base64encode(res);
}
/**
 * Delay specified time interval.
 *
 * @param timeInMs -
 * @param aborter -
 * @param abortError -
 */
async function utils_utils_common_delay(timeInMs, aborter, abortError) {
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
function utils_common_padStart(currentString, targetLength, padString = " ") {
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
function utils_common_sanitizeURL(url) {
    let safeURL = url;
    if (utils_common_getURLParameter(safeURL, URLConstants.Parameters.SIGNATURE)) {
        safeURL = utils_common_setURLParameter(safeURL, URLConstants.Parameters.SIGNATURE, "*****");
    }
    return safeURL;
}
function utils_common_sanitizeHeaders(originalHeader) {
    const headers = createHttpHeaders();
    for (const [name, value] of originalHeader) {
        if (name.toLowerCase() === HeaderConstants.AUTHORIZATION.toLowerCase()) {
            headers.set(name, "*****");
        }
        else if (name.toLowerCase() === HeaderConstants.X_MS_COPY_SOURCE) {
            headers.set(name, utils_common_sanitizeURL(value));
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
function utils_common_iEqual(str1, str2) {
    return str1.toLocaleLowerCase() === str2.toLocaleLowerCase();
}
/**
 * Extracts account name from the url
 * @param url - url to extract the account name from
 * @returns with the account name
 */
function utils_common_getAccountNameFromUrl(url) {
    const parsedUrl = new URL(url);
    let accountName;
    try {
        if (parsedUrl.hostname.split(".")[1] === "blob") {
            // `${defaultEndpointsProtocol}://${accountName}.blob.${endpointSuffix}`;
            accountName = parsedUrl.hostname.split(".")[0];
        }
        else if (utils_common_isIpEndpointStyle(parsedUrl)) {
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
function utils_common_isIpEndpointStyle(parsedUrl) {
    const host = parsedUrl.host;
    // Case 1: Ipv6, use a broad regex to find out candidates whose host contains two ':'.
    // Case 2: localhost(:port) or host.docker.internal, use broad regex to match port part.
    // Case 3: Ipv4, use broad regex which just check if host contains Ipv4.
    // For valid host please refer to https://man7.org/linux/man-pages/man7/hostname.7.html.
    return (/^.*:.*:.*$|^(localhost|host.docker.internal)(:[0-9]+)?$|^(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])(\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])){3}(:[0-9]+)?$/.test(host) ||
        (Boolean(parsedUrl.port) && utils_constants_PathStylePorts.includes(parsedUrl.port)));
}
/**
 * Convert Tags to encoded string.
 *
 * @param tags -
 */
function toBlobTagsString(tags) {
    if (tags === undefined) {
        return undefined;
    }
    const tagPairs = [];
    for (const key in tags) {
        if (Object.prototype.hasOwnProperty.call(tags, key)) {
            const value = tags[key];
            tagPairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
        }
    }
    return tagPairs.join("&");
}
/**
 * Convert Tags type to BlobTags.
 *
 * @param tags -
 */
function toBlobTags(tags) {
    if (tags === undefined) {
        return undefined;
    }
    const res = {
        blobTagSet: [],
    };
    for (const key in tags) {
        if (Object.prototype.hasOwnProperty.call(tags, key)) {
            const value = tags[key];
            res.blobTagSet.push({
                key,
                value,
            });
        }
    }
    return res;
}
/**
 * Covert BlobTags to Tags type.
 *
 * @param tags -
 */
function toTags(tags) {
    if (tags === undefined) {
        return undefined;
    }
    const res = {};
    for (const blobTag of tags.blobTagSet) {
        res[blobTag.key] = blobTag.value;
    }
    return res;
}
/**
 * Convert BlobQueryTextConfiguration to QuerySerialization type.
 *
 * @param textConfiguration -
 */
function toQuerySerialization(textConfiguration) {
    if (textConfiguration === undefined) {
        return undefined;
    }
    switch (textConfiguration.kind) {
        case "csv":
            return {
                format: {
                    type: "delimited",
                    delimitedTextConfiguration: {
                        columnSeparator: textConfiguration.columnSeparator || ",",
                        fieldQuote: textConfiguration.fieldQuote || "",
                        recordSeparator: textConfiguration.recordSeparator,
                        escapeChar: textConfiguration.escapeCharacter || "",
                        headersPresent: textConfiguration.hasHeaders || false,
                    },
                },
            };
        case "json":
            return {
                format: {
                    type: "json",
                    jsonTextConfiguration: {
                        recordSeparator: textConfiguration.recordSeparator,
                    },
                },
            };
        case "arrow":
            return {
                format: {
                    type: "arrow",
                    arrowConfiguration: {
                        schema: textConfiguration.schema,
                    },
                },
            };
        case "parquet":
            return {
                format: {
                    type: "parquet",
                },
            };
        default:
            throw Error("Invalid BlobQueryTextConfiguration.");
    }
}
function parseObjectReplicationRecord(objectReplicationRecord) {
    if (!objectReplicationRecord) {
        return undefined;
    }
    if ("policy-id" in objectReplicationRecord) {
        // If the dictionary contains a key with policy id, we are not required to do any parsing since
        // the policy id should already be stored in the ObjectReplicationDestinationPolicyId.
        return undefined;
    }
    const orProperties = [];
    for (const key in objectReplicationRecord) {
        const ids = key.split("_");
        const policyPrefix = "or-";
        if (ids[0].startsWith(policyPrefix)) {
            ids[0] = ids[0].substring(policyPrefix.length);
        }
        const rule = {
            ruleId: ids[1],
            replicationStatus: objectReplicationRecord[key],
        };
        const policyIndex = orProperties.findIndex((policy) => policy.policyId === ids[0]);
        if (policyIndex > -1) {
            orProperties[policyIndex].rules.push(rule);
        }
        else {
            orProperties.push({
                policyId: ids[0],
                rules: [rule],
            });
        }
    }
    return orProperties;
}
/**
 * Attach a TokenCredential to an object.
 *
 * @param thing -
 * @param credential -
 */
function utils_common_attachCredential(thing, credential) {
    thing.credential = credential;
    return thing;
}
function utils_common_httpAuthorizationToString(httpAuthorization) {
    return httpAuthorization ? httpAuthorization.scheme + " " + httpAuthorization.value : undefined;
}
function BlobNameToString(name) {
    if (name.encoded) {
        return decodeURIComponent(name.content);
    }
    else {
        return name.content;
    }
}
function ConvertInternalResponseOfListBlobFlat(internalResponse) {
    return {
        ...internalResponse,
        segment: {
            blobItems: internalResponse.segment.blobItems.map((blobItemInteral) => {
                const blobItem = {
                    ...blobItemInteral,
                    name: BlobNameToString(blobItemInteral.name),
                };
                return blobItem;
            }),
        },
    };
}
function ConvertInternalResponseOfListBlobHierarchy(internalResponse) {
    return {
        ...internalResponse,
        segment: {
            blobPrefixes: internalResponse.segment.blobPrefixes?.map((blobPrefixInternal) => {
                const blobPrefix = {
                    ...blobPrefixInternal,
                    name: BlobNameToString(blobPrefixInternal.name),
                };
                return blobPrefix;
            }),
            blobItems: internalResponse.segment.blobItems.map((blobItemInteral) => {
                const blobItem = {
                    ...blobItemInteral,
                    name: BlobNameToString(blobItemInteral.name),
                };
                return blobItem;
            }),
        },
    };
}
function* ExtractPageRangeInfoItems(getPageRangesSegment) {
    let pageRange = [];
    let clearRange = [];
    if (getPageRangesSegment.pageRange)
        pageRange = getPageRangesSegment.pageRange;
    if (getPageRangesSegment.clearRange)
        clearRange = getPageRangesSegment.clearRange;
    let pageRangeIndex = 0;
    let clearRangeIndex = 0;
    while (pageRangeIndex < pageRange.length && clearRangeIndex < clearRange.length) {
        if (pageRange[pageRangeIndex].start < clearRange[clearRangeIndex].start) {
            yield {
                start: pageRange[pageRangeIndex].start,
                end: pageRange[pageRangeIndex].end,
                isClear: false,
            };
            ++pageRangeIndex;
        }
        else {
            yield {
                start: clearRange[clearRangeIndex].start,
                end: clearRange[clearRangeIndex].end,
                isClear: true,
            };
            ++clearRangeIndex;
        }
    }
    for (; pageRangeIndex < pageRange.length; ++pageRangeIndex) {
        yield {
            start: pageRange[pageRangeIndex].start,
            end: pageRange[pageRangeIndex].end,
            isClear: false,
        };
    }
    for (; clearRangeIndex < clearRange.length; ++clearRangeIndex) {
        yield {
            start: clearRange[clearRangeIndex].start,
            end: clearRange[clearRangeIndex].end,
            isClear: true,
        };
    }
}
/**
 * Escape the blobName but keep path separator ('/').
 */
function utils_common_EscapePath(blobName) {
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
function utils_common_assertResponse(response) {
    if (`_response` in response) {
        return response;
    }
    throw new TypeError(`Unexpected response object ${response}`);
}
//# sourceMappingURL=utils.common.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/StorageClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * A StorageClient represents a based URL class for {@link BlobServiceClient}, {@link ContainerClient}
 * and etc.
 */
class StorageClient_StorageClient {
    /**
     * Encoded URL string value.
     */
    url;
    accountName;
    /**
     * Request policy pipeline.
     *
     * @internal
     */
    pipeline;
    /**
     * Such as AnonymousCredential, StorageSharedKeyCredential or any credential from the `@azure/identity` package to authenticate requests to the service. You can also provide an object that implements the TokenCredential interface. If not specified, AnonymousCredential is used.
     */
    credential;
    /**
     * StorageClient is a reference to protocol layer operations entry, which is
     * generated by AutoRest generator.
     */
    storageClientContext;
    /**
     */
    isHttps;
    /**
     * Creates an instance of StorageClient.
     * @param url - url to resource
     * @param pipeline - request policy pipeline.
     */
    constructor(url, pipeline) {
        // URL should be encoded and only once, protocol layer shouldn't encode URL again
        this.url = utils_common_escapeURLPath(url);
        this.accountName = utils_common_getAccountNameFromUrl(url);
        this.pipeline = pipeline;
        this.storageClientContext = new StorageContextClient(this.url, getCoreClientOptions(pipeline));
        this.isHttps = utils_common_iEqual(utils_common_getURLScheme(this.url) || "", "https");
        this.credential = getCredentialFromPipeline(pipeline);
        // Override protocol layer's default content-type
        const storageClientContext = this.storageClientContext;
        storageClientContext.requestContentType = undefined;
    }
}
//# sourceMappingURL=StorageClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/utils/tracing.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * Creates a span using the global tracer.
 * @internal
 */
const tracingClient = createTracingClient({
    packageName: "@azure/storage-blob",
    packageVersion: esm_utils_constants_SDK_VERSION,
    namespace: "Microsoft.Storage",
});
//# sourceMappingURL=tracing.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/sas/BlobSASPermissions.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * This is a helper class to construct a string representing the permissions granted by a ServiceSAS to a blob. Setting
 * a value to true means that any SAS which uses these permissions will grant permissions for that operation. Once all
 * the values are set, this should be serialized with toString and set as the permissions field on a
 * {@link BlobSASSignatureValues} object. It is possible to construct the permissions string without this class, but
 * the order of the permissions is particular and this class guarantees correctness.
 */
class BlobSASPermissions {
    /**
     * Creates a {@link BlobSASPermissions} from the specified permissions string. This method will throw an
     * Error if it encounters a character that does not correspond to a valid permission.
     *
     * @param permissions -
     */
    static parse(permissions) {
        const blobSASPermissions = new BlobSASPermissions();
        for (const char of permissions) {
            switch (char) {
                case "r":
                    blobSASPermissions.read = true;
                    break;
                case "a":
                    blobSASPermissions.add = true;
                    break;
                case "c":
                    blobSASPermissions.create = true;
                    break;
                case "w":
                    blobSASPermissions.write = true;
                    break;
                case "d":
                    blobSASPermissions.delete = true;
                    break;
                case "x":
                    blobSASPermissions.deleteVersion = true;
                    break;
                case "t":
                    blobSASPermissions.tag = true;
                    break;
                case "m":
                    blobSASPermissions.move = true;
                    break;
                case "e":
                    blobSASPermissions.execute = true;
                    break;
                case "i":
                    blobSASPermissions.setImmutabilityPolicy = true;
                    break;
                case "y":
                    blobSASPermissions.permanentDelete = true;
                    break;
                default:
                    throw new RangeError(`Invalid permission: ${char}`);
            }
        }
        return blobSASPermissions;
    }
    /**
     * Creates a {@link BlobSASPermissions} from a raw object which contains same keys as it
     * and boolean values for them.
     *
     * @param permissionLike -
     */
    static from(permissionLike) {
        const blobSASPermissions = new BlobSASPermissions();
        if (permissionLike.read) {
            blobSASPermissions.read = true;
        }
        if (permissionLike.add) {
            blobSASPermissions.add = true;
        }
        if (permissionLike.create) {
            blobSASPermissions.create = true;
        }
        if (permissionLike.write) {
            blobSASPermissions.write = true;
        }
        if (permissionLike.delete) {
            blobSASPermissions.delete = true;
        }
        if (permissionLike.deleteVersion) {
            blobSASPermissions.deleteVersion = true;
        }
        if (permissionLike.tag) {
            blobSASPermissions.tag = true;
        }
        if (permissionLike.move) {
            blobSASPermissions.move = true;
        }
        if (permissionLike.execute) {
            blobSASPermissions.execute = true;
        }
        if (permissionLike.setImmutabilityPolicy) {
            blobSASPermissions.setImmutabilityPolicy = true;
        }
        if (permissionLike.permanentDelete) {
            blobSASPermissions.permanentDelete = true;
        }
        return blobSASPermissions;
    }
    /**
     * Specifies Read access granted.
     */
    read = false;
    /**
     * Specifies Add access granted.
     */
    add = false;
    /**
     * Specifies Create access granted.
     */
    create = false;
    /**
     * Specifies Write access granted.
     */
    write = false;
    /**
     * Specifies Delete access granted.
     */
    delete = false;
    /**
     * Specifies Delete version access granted.
     */
    deleteVersion = false;
    /**
     * Specfies Tag access granted.
     */
    tag = false;
    /**
     * Specifies Move access granted.
     */
    move = false;
    /**
     * Specifies Execute access granted.
     */
    execute = false;
    /**
     * Specifies SetImmutabilityPolicy access granted.
     */
    setImmutabilityPolicy = false;
    /**
     * Specifies that Permanent Delete is permitted.
     */
    permanentDelete = false;
    /**
     * Converts the given permissions to a string. Using this method will guarantee the permissions are in an
     * order accepted by the service.
     *
     * @returns A string which represents the BlobSASPermissions
     */
    toString() {
        const permissions = [];
        if (this.read) {
            permissions.push("r");
        }
        if (this.add) {
            permissions.push("a");
        }
        if (this.create) {
            permissions.push("c");
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
        if (this.tag) {
            permissions.push("t");
        }
        if (this.move) {
            permissions.push("m");
        }
        if (this.execute) {
            permissions.push("e");
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
//# sourceMappingURL=BlobSASPermissions.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/sas/ContainerSASPermissions.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * This is a helper class to construct a string representing the permissions granted by a ServiceSAS to a container.
 * Setting a value to true means that any SAS which uses these permissions will grant permissions for that operation.
 * Once all the values are set, this should be serialized with toString and set as the permissions field on a
 * {@link BlobSASSignatureValues} object. It is possible to construct the permissions string without this class, but
 * the order of the permissions is particular and this class guarantees correctness.
 */
class ContainerSASPermissions {
    /**
     * Creates an {@link ContainerSASPermissions} from the specified permissions string. This method will throw an
     * Error if it encounters a character that does not correspond to a valid permission.
     *
     * @param permissions -
     */
    static parse(permissions) {
        const containerSASPermissions = new ContainerSASPermissions();
        for (const char of permissions) {
            switch (char) {
                case "r":
                    containerSASPermissions.read = true;
                    break;
                case "a":
                    containerSASPermissions.add = true;
                    break;
                case "c":
                    containerSASPermissions.create = true;
                    break;
                case "w":
                    containerSASPermissions.write = true;
                    break;
                case "d":
                    containerSASPermissions.delete = true;
                    break;
                case "l":
                    containerSASPermissions.list = true;
                    break;
                case "t":
                    containerSASPermissions.tag = true;
                    break;
                case "x":
                    containerSASPermissions.deleteVersion = true;
                    break;
                case "m":
                    containerSASPermissions.move = true;
                    break;
                case "e":
                    containerSASPermissions.execute = true;
                    break;
                case "i":
                    containerSASPermissions.setImmutabilityPolicy = true;
                    break;
                case "y":
                    containerSASPermissions.permanentDelete = true;
                    break;
                case "f":
                    containerSASPermissions.filterByTags = true;
                    break;
                default:
                    throw new RangeError(`Invalid permission ${char}`);
            }
        }
        return containerSASPermissions;
    }
    /**
     * Creates a {@link ContainerSASPermissions} from a raw object which contains same keys as it
     * and boolean values for them.
     *
     * @param permissionLike -
     */
    static from(permissionLike) {
        const containerSASPermissions = new ContainerSASPermissions();
        if (permissionLike.read) {
            containerSASPermissions.read = true;
        }
        if (permissionLike.add) {
            containerSASPermissions.add = true;
        }
        if (permissionLike.create) {
            containerSASPermissions.create = true;
        }
        if (permissionLike.write) {
            containerSASPermissions.write = true;
        }
        if (permissionLike.delete) {
            containerSASPermissions.delete = true;
        }
        if (permissionLike.list) {
            containerSASPermissions.list = true;
        }
        if (permissionLike.deleteVersion) {
            containerSASPermissions.deleteVersion = true;
        }
        if (permissionLike.tag) {
            containerSASPermissions.tag = true;
        }
        if (permissionLike.move) {
            containerSASPermissions.move = true;
        }
        if (permissionLike.execute) {
            containerSASPermissions.execute = true;
        }
        if (permissionLike.setImmutabilityPolicy) {
            containerSASPermissions.setImmutabilityPolicy = true;
        }
        if (permissionLike.permanentDelete) {
            containerSASPermissions.permanentDelete = true;
        }
        if (permissionLike.filterByTags) {
            containerSASPermissions.filterByTags = true;
        }
        return containerSASPermissions;
    }
    /**
     * Specifies Read access granted.
     */
    read = false;
    /**
     * Specifies Add access granted.
     */
    add = false;
    /**
     * Specifies Create access granted.
     */
    create = false;
    /**
     * Specifies Write access granted.
     */
    write = false;
    /**
     * Specifies Delete access granted.
     */
    delete = false;
    /**
     * Specifies Delete version access granted.
     */
    deleteVersion = false;
    /**
     * Specifies List access granted.
     */
    list = false;
    /**
     * Specfies Tag access granted.
     */
    tag = false;
    /**
     * Specifies Move access granted.
     */
    move = false;
    /**
     * Specifies Execute access granted.
     */
    execute = false;
    /**
     * Specifies SetImmutabilityPolicy access granted.
     */
    setImmutabilityPolicy = false;
    /**
     * Specifies that Permanent Delete is permitted.
     */
    permanentDelete = false;
    /**
     * Specifies that Filter Blobs by Tags is permitted.
     */
    filterByTags = false;
    /**
     * Converts the given permissions to a string. Using this method will guarantee the permissions are in an
     * order accepted by the service.
     *
     * The order of the characters should be as specified here to ensure correctness.
     * @see https://learn.microsoft.com/rest/api/storageservices/constructing-a-service-sas
     *
     */
    toString() {
        const permissions = [];
        if (this.read) {
            permissions.push("r");
        }
        if (this.add) {
            permissions.push("a");
        }
        if (this.create) {
            permissions.push("c");
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
        if (this.list) {
            permissions.push("l");
        }
        if (this.tag) {
            permissions.push("t");
        }
        if (this.move) {
            permissions.push("m");
        }
        if (this.execute) {
            permissions.push("e");
        }
        if (this.setImmutabilityPolicy) {
            permissions.push("i");
        }
        if (this.permanentDelete) {
            permissions.push("y");
        }
        if (this.filterByTags) {
            permissions.push("f");
        }
        return permissions.join("");
    }
}
//# sourceMappingURL=ContainerSASPermissions.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/sas/SasIPRange.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Generate SasIPRange format string. For example:
 *
 * "8.8.8.8" or "1.1.1.1-255.255.255.255"
 *
 * @param ipRange -
 */
function ipRangeToString(ipRange) {
    return ipRange.end ? `${ipRange.start}-${ipRange.end}` : ipRange.start;
}
//# sourceMappingURL=SasIPRange.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/sas/SASQueryParameters.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * Protocols for generated SAS.
 */
var SASProtocol;
(function (SASProtocol) {
    /**
     * Protocol that allows HTTPS only
     */
    SASProtocol["Https"] = "https";
    /**
     * Protocol that allows both HTTPS and HTTP
     */
    SASProtocol["HttpsAndHttp"] = "https,http";
})(SASProtocol || (SASProtocol = {}));
/**
 * Represents the components that make up an Azure Storage SAS' query parameters. This type is not constructed directly
 * by the user; it is only generated by the {@link AccountSASSignatureValues} and {@link BlobSASSignatureValues}
 * types. Once generated, it can be encoded into a {@link String} and appended to a URL directly (though caution should
 * be taken here in case there are existing query parameters, which might affect the appropriate means of appending
 * these query parameters).
 *
 * NOTE: Instances of this class are immutable.
 */
class SASQueryParameters {
    /**
     * The storage API version.
     */
    version;
    /**
     * Optional. The allowed HTTP protocol(s).
     */
    protocol;
    /**
     * Optional. The start time for this SAS token.
     */
    startsOn;
    /**
     * Optional only when identifier is provided. The expiry time for this SAS token.
     */
    expiresOn;
    /**
     * Optional only when identifier is provided.
     * Please refer to {@link AccountSASPermissions}, {@link BlobSASPermissions}, or {@link ContainerSASPermissions} for
     * more details.
     */
    permissions;
    /**
     * Optional. The storage services being accessed (only for Account SAS). Please refer to {@link AccountSASServices}
     * for more details.
     */
    services;
    /**
     * Optional. The storage resource types being accessed (only for Account SAS). Please refer to
     * {@link AccountSASResourceTypes} for more details.
     */
    resourceTypes;
    /**
     * Optional. The signed identifier (only for {@link BlobSASSignatureValues}).
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/establishing-a-stored-access-policy
     */
    identifier;
    /**
     * Optional. Beginning in version 2025-07-05, this value specifies the Entra ID of the user would is authorized to
     * use the resulting SAS URL.  The resulting SAS URL must be used in conjunction with an Entra ID token that has been
     * issued to the user specified in this value.
     */
    delegatedUserObjectId;
    /**
     * Optional. Encryption scope to use when sending requests authorized with this SAS URI.
     */
    encryptionScope;
    /**
     * Optional. Specifies which resources are accessible via the SAS (only for {@link BlobSASSignatureValues}).
     * @see https://learn.microsoft.com/rest/api/storageservices/create-service-sas#specifying-the-signed-resource-blob-service-only
     */
    resource;
    /**
     * The signature for the SAS token.
     */
    signature;
    /**
     * Value for cache-control header in Blob/File Service SAS.
     */
    cacheControl;
    /**
     * Value for content-disposition header in Blob/File Service SAS.
     */
    contentDisposition;
    /**
     * Value for content-encoding header in Blob/File Service SAS.
     */
    contentEncoding;
    /**
     * Value for content-length header in Blob/File Service SAS.
     */
    contentLanguage;
    /**
     * Value for content-type header in Blob/File Service SAS.
     */
    contentType;
    /**
     * Inner value of getter ipRange.
     */
    ipRangeInner;
    /**
     * The Azure Active Directory object ID in GUID format.
     * Property of user delegation key.
     */
    signedOid;
    /**
     * The Azure Active Directory tenant ID in GUID format.
     * Property of user delegation key.
     */
    signedTenantId;
    /**
     * The date-time the key is active.
     * Property of user delegation key.
     */
    signedStartsOn;
    /**
     * The date-time the key expires.
     * Property of user delegation key.
     */
    signedExpiresOn;
    /**
     * Abbreviation of the Azure Storage service that accepts the user delegation key.
     * Property of user delegation key.
     */
    signedService;
    /**
     * The service version that created the user delegation key.
     * Property of user delegation key.
     */
    signedVersion;
    /**
     * Authorized AAD Object ID in GUID format. The AAD Object ID of a user authorized by the owner of the User Delegation Key
     * to perform the action granted by the SAS. The Azure Storage service will ensure that the owner of the user delegation key
     * has the required permissions before granting access but no additional permission check for the user specified in
     * this value will be performed. This is only used for User Delegation SAS.
     */
    preauthorizedAgentObjectId;
    /**
     * A GUID value that will be logged in the storage diagnostic logs and can be used to correlate SAS generation with storage resource access.
     * This is only used for User Delegation SAS.
     */
    correlationId;
    /**
     * Optional. IP range allowed for this SAS.
     *
     * @readonly
     */
    get ipRange() {
        if (this.ipRangeInner) {
            return {
                end: this.ipRangeInner.end,
                start: this.ipRangeInner.start,
            };
        }
        return undefined;
    }
    constructor(version, signature, permissionsOrOptions, services, resourceTypes, protocol, startsOn, expiresOn, ipRange, identifier, resource, cacheControl, contentDisposition, contentEncoding, contentLanguage, contentType, userDelegationKey, preauthorizedAgentObjectId, correlationId, encryptionScope, delegatedUserObjectId) {
        this.version = version;
        this.signature = signature;
        if (permissionsOrOptions !== undefined && typeof permissionsOrOptions !== "string") {
            // SASQueryParametersOptions
            this.permissions = permissionsOrOptions.permissions;
            this.services = permissionsOrOptions.services;
            this.resourceTypes = permissionsOrOptions.resourceTypes;
            this.protocol = permissionsOrOptions.protocol;
            this.startsOn = permissionsOrOptions.startsOn;
            this.expiresOn = permissionsOrOptions.expiresOn;
            this.ipRangeInner = permissionsOrOptions.ipRange;
            this.identifier = permissionsOrOptions.identifier;
            this.delegatedUserObjectId = permissionsOrOptions.delegatedUserObjectId;
            this.encryptionScope = permissionsOrOptions.encryptionScope;
            this.resource = permissionsOrOptions.resource;
            this.cacheControl = permissionsOrOptions.cacheControl;
            this.contentDisposition = permissionsOrOptions.contentDisposition;
            this.contentEncoding = permissionsOrOptions.contentEncoding;
            this.contentLanguage = permissionsOrOptions.contentLanguage;
            this.contentType = permissionsOrOptions.contentType;
            if (permissionsOrOptions.userDelegationKey) {
                this.signedOid = permissionsOrOptions.userDelegationKey.signedObjectId;
                this.signedTenantId = permissionsOrOptions.userDelegationKey.signedTenantId;
                this.signedStartsOn = permissionsOrOptions.userDelegationKey.signedStartsOn;
                this.signedExpiresOn = permissionsOrOptions.userDelegationKey.signedExpiresOn;
                this.signedService = permissionsOrOptions.userDelegationKey.signedService;
                this.signedVersion = permissionsOrOptions.userDelegationKey.signedVersion;
                this.preauthorizedAgentObjectId = permissionsOrOptions.preauthorizedAgentObjectId;
                this.correlationId = permissionsOrOptions.correlationId;
            }
        }
        else {
            this.services = services;
            this.resourceTypes = resourceTypes;
            this.expiresOn = expiresOn;
            this.permissions = permissionsOrOptions;
            this.protocol = protocol;
            this.startsOn = startsOn;
            this.ipRangeInner = ipRange;
            this.delegatedUserObjectId = delegatedUserObjectId;
            this.encryptionScope = encryptionScope;
            this.identifier = identifier;
            this.resource = resource;
            this.cacheControl = cacheControl;
            this.contentDisposition = contentDisposition;
            this.contentEncoding = contentEncoding;
            this.contentLanguage = contentLanguage;
            this.contentType = contentType;
            if (userDelegationKey) {
                this.signedOid = userDelegationKey.signedObjectId;
                this.signedTenantId = userDelegationKey.signedTenantId;
                this.signedStartsOn = userDelegationKey.signedStartsOn;
                this.signedExpiresOn = userDelegationKey.signedExpiresOn;
                this.signedService = userDelegationKey.signedService;
                this.signedVersion = userDelegationKey.signedVersion;
                this.preauthorizedAgentObjectId = preauthorizedAgentObjectId;
                this.correlationId = correlationId;
            }
        }
    }
    /**
     * Encodes all SAS query parameters into a string that can be appended to a URL.
     *
     */
    toString() {
        const params = [
            "sv",
            "ss",
            "srt",
            "spr",
            "st",
            "se",
            "sip",
            "si",
            "ses",
            "skoid", // Signed object ID
            "sktid", // Signed tenant ID
            "skt", // Signed key start time
            "ske", // Signed key expiry time
            "sks", // Signed key service
            "skv", // Signed key version
            "sr",
            "sp",
            "sig",
            "rscc",
            "rscd",
            "rsce",
            "rscl",
            "rsct",
            "saoid",
            "scid",
            "sduoid", // Signed key user delegation object ID
        ];
        const queries = [];
        for (const param of params) {
            switch (param) {
                case "sv":
                    this.tryAppendQueryParameter(queries, param, this.version);
                    break;
                case "ss":
                    this.tryAppendQueryParameter(queries, param, this.services);
                    break;
                case "srt":
                    this.tryAppendQueryParameter(queries, param, this.resourceTypes);
                    break;
                case "spr":
                    this.tryAppendQueryParameter(queries, param, this.protocol);
                    break;
                case "st":
                    this.tryAppendQueryParameter(queries, param, this.startsOn ? utils_common_truncatedISO8061Date(this.startsOn, false) : undefined);
                    break;
                case "se":
                    this.tryAppendQueryParameter(queries, param, this.expiresOn ? utils_common_truncatedISO8061Date(this.expiresOn, false) : undefined);
                    break;
                case "sip":
                    this.tryAppendQueryParameter(queries, param, this.ipRange ? ipRangeToString(this.ipRange) : undefined);
                    break;
                case "si":
                    this.tryAppendQueryParameter(queries, param, this.identifier);
                    break;
                case "ses":
                    this.tryAppendQueryParameter(queries, param, this.encryptionScope);
                    break;
                case "skoid": // Signed object ID
                    this.tryAppendQueryParameter(queries, param, this.signedOid);
                    break;
                case "sktid": // Signed tenant ID
                    this.tryAppendQueryParameter(queries, param, this.signedTenantId);
                    break;
                case "skt": // Signed key start time
                    this.tryAppendQueryParameter(queries, param, this.signedStartsOn ? utils_common_truncatedISO8061Date(this.signedStartsOn, false) : undefined);
                    break;
                case "ske": // Signed key expiry time
                    this.tryAppendQueryParameter(queries, param, this.signedExpiresOn ? utils_common_truncatedISO8061Date(this.signedExpiresOn, false) : undefined);
                    break;
                case "sks": // Signed key service
                    this.tryAppendQueryParameter(queries, param, this.signedService);
                    break;
                case "skv": // Signed key version
                    this.tryAppendQueryParameter(queries, param, this.signedVersion);
                    break;
                case "sr":
                    this.tryAppendQueryParameter(queries, param, this.resource);
                    break;
                case "sp":
                    this.tryAppendQueryParameter(queries, param, this.permissions);
                    break;
                case "sig":
                    this.tryAppendQueryParameter(queries, param, this.signature);
                    break;
                case "rscc":
                    this.tryAppendQueryParameter(queries, param, this.cacheControl);
                    break;
                case "rscd":
                    this.tryAppendQueryParameter(queries, param, this.contentDisposition);
                    break;
                case "rsce":
                    this.tryAppendQueryParameter(queries, param, this.contentEncoding);
                    break;
                case "rscl":
                    this.tryAppendQueryParameter(queries, param, this.contentLanguage);
                    break;
                case "rsct":
                    this.tryAppendQueryParameter(queries, param, this.contentType);
                    break;
                case "saoid":
                    this.tryAppendQueryParameter(queries, param, this.preauthorizedAgentObjectId);
                    break;
                case "scid":
                    this.tryAppendQueryParameter(queries, param, this.correlationId);
                    break;
                case "sduoid":
                    this.tryAppendQueryParameter(queries, param, this.delegatedUserObjectId);
                    break;
            }
        }
        return queries.join("&");
    }
    /**
     * A private helper method used to filter and append query key/value pairs into an array.
     *
     * @param queries -
     * @param key -
     * @param value -
     */
    tryAppendQueryParameter(queries, key, value) {
        if (!value) {
            return;
        }
        key = encodeURIComponent(key);
        value = encodeURIComponent(value);
        if (key.length > 0 && value.length > 0) {
            queries.push(`${key}=${value}`);
        }
    }
}
//# sourceMappingURL=SASQueryParameters.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/sas/BlobSASSignatureValues.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.








function generateBlobSASQueryParameters(blobSASSignatureValues, sharedKeyCredentialOrUserDelegationKey, accountName) {
    return generateBlobSASQueryParametersInternal(blobSASSignatureValues, sharedKeyCredentialOrUserDelegationKey, accountName).sasQueryParameters;
}
function generateBlobSASQueryParametersInternal(blobSASSignatureValues, sharedKeyCredentialOrUserDelegationKey, accountName) {
    const version = blobSASSignatureValues.version ? blobSASSignatureValues.version : SERVICE_VERSION;
    const sharedKeyCredential = sharedKeyCredentialOrUserDelegationKey instanceof StorageSharedKeyCredential
        ? sharedKeyCredentialOrUserDelegationKey
        : undefined;
    let userDelegationKeyCredential;
    if (sharedKeyCredential === undefined && accountName !== undefined) {
        userDelegationKeyCredential = new UserDelegationKeyCredential(accountName, sharedKeyCredentialOrUserDelegationKey);
    }
    if (sharedKeyCredential === undefined && userDelegationKeyCredential === undefined) {
        throw TypeError("Invalid sharedKeyCredential, userDelegationKey or accountName.");
    }
    // Version 2020-12-06 adds support for encryptionscope in SAS.
    if (version >= "2020-12-06") {
        if (sharedKeyCredential !== undefined) {
            return generateBlobSASQueryParameters20201206(blobSASSignatureValues, sharedKeyCredential);
        }
        else {
            if (version >= "2025-07-05") {
                return generateBlobSASQueryParametersUDK20250705(blobSASSignatureValues, userDelegationKeyCredential);
            }
            else {
                return generateBlobSASQueryParametersUDK20201206(blobSASSignatureValues, userDelegationKeyCredential);
            }
        }
    }
    // Version 2019-12-12 adds support for the blob tags permission.
    // Version 2018-11-09 adds support for the signed resource and signed blob snapshot time fields.
    // https://learn.microsoft.com/rest/api/storageservices/constructing-a-service-sas#constructing-the-signature-string
    if (version >= "2018-11-09") {
        if (sharedKeyCredential !== undefined) {
            return generateBlobSASQueryParameters20181109(blobSASSignatureValues, sharedKeyCredential);
        }
        else {
            // Version 2020-02-10 delegation SAS signature construction includes preauthorizedAgentObjectId, agentObjectId, correlationId.
            if (version >= "2020-02-10") {
                return generateBlobSASQueryParametersUDK20200210(blobSASSignatureValues, userDelegationKeyCredential);
            }
            else {
                return generateBlobSASQueryParametersUDK20181109(blobSASSignatureValues, userDelegationKeyCredential);
            }
        }
    }
    if (version >= "2015-04-05") {
        if (sharedKeyCredential !== undefined) {
            return generateBlobSASQueryParameters20150405(blobSASSignatureValues, sharedKeyCredential);
        }
        else {
            throw new RangeError("'version' must be >= '2018-11-09' when generating user delegation SAS using user delegation key.");
        }
    }
    throw new RangeError("'version' must be >= '2015-04-05'.");
}
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 * IMPLEMENTATION FOR API VERSION FROM 2015-04-05 AND BEFORE 2018-11-09.
 *
 * Creates an instance of SASQueryParameters.
 *
 * Only accepts required settings needed to create a SAS. For optional settings please
 * set corresponding properties directly, such as permissions, startsOn and identifier.
 *
 * WARNING: When identifier is not provided, permissions and expiresOn are required.
 * You MUST assign value to identifier or expiresOn & permissions manually if you initial with
 * this constructor.
 *
 * @param blobSASSignatureValues -
 * @param sharedKeyCredential -
 */
function generateBlobSASQueryParameters20150405(blobSASSignatureValues, sharedKeyCredential) {
    blobSASSignatureValues = SASSignatureValuesSanityCheckAndAutofill(blobSASSignatureValues);
    if (!blobSASSignatureValues.identifier &&
        !(blobSASSignatureValues.permissions && blobSASSignatureValues.expiresOn)) {
        throw new RangeError("Must provide 'permissions' and 'expiresOn' for Blob SAS generation when 'identifier' is not provided.");
    }
    let resource = "c";
    if (blobSASSignatureValues.blobName) {
        resource = "b";
    }
    // Calling parse and toString guarantees the proper ordering and throws on invalid characters.
    let verifiedPermissions;
    if (blobSASSignatureValues.permissions) {
        if (blobSASSignatureValues.blobName) {
            verifiedPermissions = BlobSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
        else {
            verifiedPermissions = ContainerSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
    }
    // Signature is generated on the un-url-encoded values.
    const stringToSign = [
        verifiedPermissions ? verifiedPermissions : "",
        blobSASSignatureValues.startsOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.startsOn, false)
            : "",
        blobSASSignatureValues.expiresOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.expiresOn, false)
            : "",
        getCanonicalName(sharedKeyCredential.accountName, blobSASSignatureValues.containerName, blobSASSignatureValues.blobName),
        blobSASSignatureValues.identifier,
        blobSASSignatureValues.ipRange ? ipRangeToString(blobSASSignatureValues.ipRange) : "",
        blobSASSignatureValues.protocol ? blobSASSignatureValues.protocol : "",
        blobSASSignatureValues.version,
        blobSASSignatureValues.cacheControl ? blobSASSignatureValues.cacheControl : "",
        blobSASSignatureValues.contentDisposition ? blobSASSignatureValues.contentDisposition : "",
        blobSASSignatureValues.contentEncoding ? blobSASSignatureValues.contentEncoding : "",
        blobSASSignatureValues.contentLanguage ? blobSASSignatureValues.contentLanguage : "",
        blobSASSignatureValues.contentType ? blobSASSignatureValues.contentType : "",
    ].join("\n");
    const signature = sharedKeyCredential.computeHMACSHA256(stringToSign);
    return {
        sasQueryParameters: new SASQueryParameters(blobSASSignatureValues.version, signature, verifiedPermissions, undefined, undefined, blobSASSignatureValues.protocol, blobSASSignatureValues.startsOn, blobSASSignatureValues.expiresOn, blobSASSignatureValues.ipRange, blobSASSignatureValues.identifier, resource, blobSASSignatureValues.cacheControl, blobSASSignatureValues.contentDisposition, blobSASSignatureValues.contentEncoding, blobSASSignatureValues.contentLanguage, blobSASSignatureValues.contentType),
        stringToSign: stringToSign,
    };
}
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 * IMPLEMENTATION FOR API VERSION FROM 2018-11-09.
 *
 * Creates an instance of SASQueryParameters.
 *
 * Only accepts required settings needed to create a SAS. For optional settings please
 * set corresponding properties directly, such as permissions, startsOn and identifier.
 *
 * WARNING: When identifier is not provided, permissions and expiresOn are required.
 * You MUST assign value to identifier or expiresOn & permissions manually if you initial with
 * this constructor.
 *
 * @param blobSASSignatureValues -
 * @param sharedKeyCredential -
 */
function generateBlobSASQueryParameters20181109(blobSASSignatureValues, sharedKeyCredential) {
    blobSASSignatureValues = SASSignatureValuesSanityCheckAndAutofill(blobSASSignatureValues);
    if (!blobSASSignatureValues.identifier &&
        !(blobSASSignatureValues.permissions && blobSASSignatureValues.expiresOn)) {
        throw new RangeError("Must provide 'permissions' and 'expiresOn' for Blob SAS generation when 'identifier' is not provided.");
    }
    let resource = "c";
    let timestamp = blobSASSignatureValues.snapshotTime;
    if (blobSASSignatureValues.blobName) {
        resource = "b";
        if (blobSASSignatureValues.snapshotTime) {
            resource = "bs";
        }
        else if (blobSASSignatureValues.versionId) {
            resource = "bv";
            timestamp = blobSASSignatureValues.versionId;
        }
    }
    // Calling parse and toString guarantees the proper ordering and throws on invalid characters.
    let verifiedPermissions;
    if (blobSASSignatureValues.permissions) {
        if (blobSASSignatureValues.blobName) {
            verifiedPermissions = BlobSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
        else {
            verifiedPermissions = ContainerSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
    }
    // Signature is generated on the un-url-encoded values.
    const stringToSign = [
        verifiedPermissions ? verifiedPermissions : "",
        blobSASSignatureValues.startsOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.startsOn, false)
            : "",
        blobSASSignatureValues.expiresOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.expiresOn, false)
            : "",
        getCanonicalName(sharedKeyCredential.accountName, blobSASSignatureValues.containerName, blobSASSignatureValues.blobName),
        blobSASSignatureValues.identifier,
        blobSASSignatureValues.ipRange ? ipRangeToString(blobSASSignatureValues.ipRange) : "",
        blobSASSignatureValues.protocol ? blobSASSignatureValues.protocol : "",
        blobSASSignatureValues.version,
        resource,
        timestamp,
        blobSASSignatureValues.cacheControl ? blobSASSignatureValues.cacheControl : "",
        blobSASSignatureValues.contentDisposition ? blobSASSignatureValues.contentDisposition : "",
        blobSASSignatureValues.contentEncoding ? blobSASSignatureValues.contentEncoding : "",
        blobSASSignatureValues.contentLanguage ? blobSASSignatureValues.contentLanguage : "",
        blobSASSignatureValues.contentType ? blobSASSignatureValues.contentType : "",
    ].join("\n");
    const signature = sharedKeyCredential.computeHMACSHA256(stringToSign);
    return {
        sasQueryParameters: new SASQueryParameters(blobSASSignatureValues.version, signature, verifiedPermissions, undefined, undefined, blobSASSignatureValues.protocol, blobSASSignatureValues.startsOn, blobSASSignatureValues.expiresOn, blobSASSignatureValues.ipRange, blobSASSignatureValues.identifier, resource, blobSASSignatureValues.cacheControl, blobSASSignatureValues.contentDisposition, blobSASSignatureValues.contentEncoding, blobSASSignatureValues.contentLanguage, blobSASSignatureValues.contentType),
        stringToSign: stringToSign,
    };
}
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 * IMPLEMENTATION FOR API VERSION FROM 2020-12-06.
 *
 * Creates an instance of SASQueryParameters.
 *
 * Only accepts required settings needed to create a SAS. For optional settings please
 * set corresponding properties directly, such as permissions, startsOn and identifier.
 *
 * WARNING: When identifier is not provided, permissions and expiresOn are required.
 * You MUST assign value to identifier or expiresOn & permissions manually if you initial with
 * this constructor.
 *
 * @param blobSASSignatureValues -
 * @param sharedKeyCredential -
 */
function generateBlobSASQueryParameters20201206(blobSASSignatureValues, sharedKeyCredential) {
    blobSASSignatureValues = SASSignatureValuesSanityCheckAndAutofill(blobSASSignatureValues);
    if (!blobSASSignatureValues.identifier &&
        !(blobSASSignatureValues.permissions && blobSASSignatureValues.expiresOn)) {
        throw new RangeError("Must provide 'permissions' and 'expiresOn' for Blob SAS generation when 'identifier' is not provided.");
    }
    let resource = "c";
    let timestamp = blobSASSignatureValues.snapshotTime;
    if (blobSASSignatureValues.blobName) {
        resource = "b";
        if (blobSASSignatureValues.snapshotTime) {
            resource = "bs";
        }
        else if (blobSASSignatureValues.versionId) {
            resource = "bv";
            timestamp = blobSASSignatureValues.versionId;
        }
    }
    // Calling parse and toString guarantees the proper ordering and throws on invalid characters.
    let verifiedPermissions;
    if (blobSASSignatureValues.permissions) {
        if (blobSASSignatureValues.blobName) {
            verifiedPermissions = BlobSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
        else {
            verifiedPermissions = ContainerSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
    }
    // Signature is generated on the un-url-encoded values.
    const stringToSign = [
        verifiedPermissions ? verifiedPermissions : "",
        blobSASSignatureValues.startsOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.startsOn, false)
            : "",
        blobSASSignatureValues.expiresOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.expiresOn, false)
            : "",
        getCanonicalName(sharedKeyCredential.accountName, blobSASSignatureValues.containerName, blobSASSignatureValues.blobName),
        blobSASSignatureValues.identifier,
        blobSASSignatureValues.ipRange ? ipRangeToString(blobSASSignatureValues.ipRange) : "",
        blobSASSignatureValues.protocol ? blobSASSignatureValues.protocol : "",
        blobSASSignatureValues.version,
        resource,
        timestamp,
        blobSASSignatureValues.encryptionScope,
        blobSASSignatureValues.cacheControl ? blobSASSignatureValues.cacheControl : "",
        blobSASSignatureValues.contentDisposition ? blobSASSignatureValues.contentDisposition : "",
        blobSASSignatureValues.contentEncoding ? blobSASSignatureValues.contentEncoding : "",
        blobSASSignatureValues.contentLanguage ? blobSASSignatureValues.contentLanguage : "",
        blobSASSignatureValues.contentType ? blobSASSignatureValues.contentType : "",
    ].join("\n");
    const signature = sharedKeyCredential.computeHMACSHA256(stringToSign);
    return {
        sasQueryParameters: new SASQueryParameters(blobSASSignatureValues.version, signature, verifiedPermissions, undefined, undefined, blobSASSignatureValues.protocol, blobSASSignatureValues.startsOn, blobSASSignatureValues.expiresOn, blobSASSignatureValues.ipRange, blobSASSignatureValues.identifier, resource, blobSASSignatureValues.cacheControl, blobSASSignatureValues.contentDisposition, blobSASSignatureValues.contentEncoding, blobSASSignatureValues.contentLanguage, blobSASSignatureValues.contentType, undefined, undefined, undefined, blobSASSignatureValues.encryptionScope),
        stringToSign: stringToSign,
    };
}
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 * IMPLEMENTATION FOR API VERSION FROM 2018-11-09.
 *
 * Creates an instance of SASQueryParameters.
 *
 * Only accepts required settings needed to create a SAS. For optional settings please
 * set corresponding properties directly, such as permissions, startsOn.
 *
 * WARNING: identifier will be ignored, permissions and expiresOn are required.
 *
 * @param blobSASSignatureValues -
 * @param userDelegationKeyCredential -
 */
function generateBlobSASQueryParametersUDK20181109(blobSASSignatureValues, userDelegationKeyCredential) {
    blobSASSignatureValues = SASSignatureValuesSanityCheckAndAutofill(blobSASSignatureValues);
    // Stored access policies are not supported for a user delegation SAS.
    if (!blobSASSignatureValues.permissions || !blobSASSignatureValues.expiresOn) {
        throw new RangeError("Must provide 'permissions' and 'expiresOn' for Blob SAS generation when generating user delegation SAS.");
    }
    let resource = "c";
    let timestamp = blobSASSignatureValues.snapshotTime;
    if (blobSASSignatureValues.blobName) {
        resource = "b";
        if (blobSASSignatureValues.snapshotTime) {
            resource = "bs";
        }
        else if (blobSASSignatureValues.versionId) {
            resource = "bv";
            timestamp = blobSASSignatureValues.versionId;
        }
    }
    // Calling parse and toString guarantees the proper ordering and throws on invalid characters.
    let verifiedPermissions;
    if (blobSASSignatureValues.permissions) {
        if (blobSASSignatureValues.blobName) {
            verifiedPermissions = BlobSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
        else {
            verifiedPermissions = ContainerSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
    }
    // Signature is generated on the un-url-encoded values.
    const stringToSign = [
        verifiedPermissions ? verifiedPermissions : "",
        blobSASSignatureValues.startsOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.startsOn, false)
            : "",
        blobSASSignatureValues.expiresOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.expiresOn, false)
            : "",
        getCanonicalName(userDelegationKeyCredential.accountName, blobSASSignatureValues.containerName, blobSASSignatureValues.blobName),
        userDelegationKeyCredential.userDelegationKey.signedObjectId,
        userDelegationKeyCredential.userDelegationKey.signedTenantId,
        userDelegationKeyCredential.userDelegationKey.signedStartsOn
            ? utils_common_truncatedISO8061Date(userDelegationKeyCredential.userDelegationKey.signedStartsOn, false)
            : "",
        userDelegationKeyCredential.userDelegationKey.signedExpiresOn
            ? utils_common_truncatedISO8061Date(userDelegationKeyCredential.userDelegationKey.signedExpiresOn, false)
            : "",
        userDelegationKeyCredential.userDelegationKey.signedService,
        userDelegationKeyCredential.userDelegationKey.signedVersion,
        blobSASSignatureValues.ipRange ? ipRangeToString(blobSASSignatureValues.ipRange) : "",
        blobSASSignatureValues.protocol ? blobSASSignatureValues.protocol : "",
        blobSASSignatureValues.version,
        resource,
        timestamp,
        blobSASSignatureValues.cacheControl,
        blobSASSignatureValues.contentDisposition,
        blobSASSignatureValues.contentEncoding,
        blobSASSignatureValues.contentLanguage,
        blobSASSignatureValues.contentType,
    ].join("\n");
    const signature = userDelegationKeyCredential.computeHMACSHA256(stringToSign);
    return {
        sasQueryParameters: new SASQueryParameters(blobSASSignatureValues.version, signature, verifiedPermissions, undefined, undefined, blobSASSignatureValues.protocol, blobSASSignatureValues.startsOn, blobSASSignatureValues.expiresOn, blobSASSignatureValues.ipRange, blobSASSignatureValues.identifier, resource, blobSASSignatureValues.cacheControl, blobSASSignatureValues.contentDisposition, blobSASSignatureValues.contentEncoding, blobSASSignatureValues.contentLanguage, blobSASSignatureValues.contentType, userDelegationKeyCredential.userDelegationKey),
        stringToSign: stringToSign,
    };
}
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 * IMPLEMENTATION FOR API VERSION FROM 2020-02-10.
 *
 * Creates an instance of SASQueryParameters.
 *
 * Only accepts required settings needed to create a SAS. For optional settings please
 * set corresponding properties directly, such as permissions, startsOn.
 *
 * WARNING: identifier will be ignored, permissions and expiresOn are required.
 *
 * @param blobSASSignatureValues -
 * @param userDelegationKeyCredential -
 */
function generateBlobSASQueryParametersUDK20200210(blobSASSignatureValues, userDelegationKeyCredential) {
    blobSASSignatureValues = SASSignatureValuesSanityCheckAndAutofill(blobSASSignatureValues);
    // Stored access policies are not supported for a user delegation SAS.
    if (!blobSASSignatureValues.permissions || !blobSASSignatureValues.expiresOn) {
        throw new RangeError("Must provide 'permissions' and 'expiresOn' for Blob SAS generation when generating user delegation SAS.");
    }
    let resource = "c";
    let timestamp = blobSASSignatureValues.snapshotTime;
    if (blobSASSignatureValues.blobName) {
        resource = "b";
        if (blobSASSignatureValues.snapshotTime) {
            resource = "bs";
        }
        else if (blobSASSignatureValues.versionId) {
            resource = "bv";
            timestamp = blobSASSignatureValues.versionId;
        }
    }
    // Calling parse and toString guarantees the proper ordering and throws on invalid characters.
    let verifiedPermissions;
    if (blobSASSignatureValues.permissions) {
        if (blobSASSignatureValues.blobName) {
            verifiedPermissions = BlobSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
        else {
            verifiedPermissions = ContainerSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
    }
    // Signature is generated on the un-url-encoded values.
    const stringToSign = [
        verifiedPermissions ? verifiedPermissions : "",
        blobSASSignatureValues.startsOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.startsOn, false)
            : "",
        blobSASSignatureValues.expiresOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.expiresOn, false)
            : "",
        getCanonicalName(userDelegationKeyCredential.accountName, blobSASSignatureValues.containerName, blobSASSignatureValues.blobName),
        userDelegationKeyCredential.userDelegationKey.signedObjectId,
        userDelegationKeyCredential.userDelegationKey.signedTenantId,
        userDelegationKeyCredential.userDelegationKey.signedStartsOn
            ? utils_common_truncatedISO8061Date(userDelegationKeyCredential.userDelegationKey.signedStartsOn, false)
            : "",
        userDelegationKeyCredential.userDelegationKey.signedExpiresOn
            ? utils_common_truncatedISO8061Date(userDelegationKeyCredential.userDelegationKey.signedExpiresOn, false)
            : "",
        userDelegationKeyCredential.userDelegationKey.signedService,
        userDelegationKeyCredential.userDelegationKey.signedVersion,
        blobSASSignatureValues.preauthorizedAgentObjectId,
        undefined, // agentObjectId
        blobSASSignatureValues.correlationId,
        blobSASSignatureValues.ipRange ? ipRangeToString(blobSASSignatureValues.ipRange) : "",
        blobSASSignatureValues.protocol ? blobSASSignatureValues.protocol : "",
        blobSASSignatureValues.version,
        resource,
        timestamp,
        blobSASSignatureValues.cacheControl,
        blobSASSignatureValues.contentDisposition,
        blobSASSignatureValues.contentEncoding,
        blobSASSignatureValues.contentLanguage,
        blobSASSignatureValues.contentType,
    ].join("\n");
    const signature = userDelegationKeyCredential.computeHMACSHA256(stringToSign);
    return {
        sasQueryParameters: new SASQueryParameters(blobSASSignatureValues.version, signature, verifiedPermissions, undefined, undefined, blobSASSignatureValues.protocol, blobSASSignatureValues.startsOn, blobSASSignatureValues.expiresOn, blobSASSignatureValues.ipRange, blobSASSignatureValues.identifier, resource, blobSASSignatureValues.cacheControl, blobSASSignatureValues.contentDisposition, blobSASSignatureValues.contentEncoding, blobSASSignatureValues.contentLanguage, blobSASSignatureValues.contentType, userDelegationKeyCredential.userDelegationKey, blobSASSignatureValues.preauthorizedAgentObjectId, blobSASSignatureValues.correlationId),
        stringToSign: stringToSign,
    };
}
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 * IMPLEMENTATION FOR API VERSION FROM 2020-12-06.
 *
 * Creates an instance of SASQueryParameters.
 *
 * Only accepts required settings needed to create a SAS. For optional settings please
 * set corresponding properties directly, such as permissions, startsOn.
 *
 * WARNING: identifier will be ignored, permissions and expiresOn are required.
 *
 * @param blobSASSignatureValues -
 * @param userDelegationKeyCredential -
 */
function generateBlobSASQueryParametersUDK20201206(blobSASSignatureValues, userDelegationKeyCredential) {
    blobSASSignatureValues = SASSignatureValuesSanityCheckAndAutofill(blobSASSignatureValues);
    // Stored access policies are not supported for a user delegation SAS.
    if (!blobSASSignatureValues.permissions || !blobSASSignatureValues.expiresOn) {
        throw new RangeError("Must provide 'permissions' and 'expiresOn' for Blob SAS generation when generating user delegation SAS.");
    }
    let resource = "c";
    let timestamp = blobSASSignatureValues.snapshotTime;
    if (blobSASSignatureValues.blobName) {
        resource = "b";
        if (blobSASSignatureValues.snapshotTime) {
            resource = "bs";
        }
        else if (blobSASSignatureValues.versionId) {
            resource = "bv";
            timestamp = blobSASSignatureValues.versionId;
        }
    }
    // Calling parse and toString guarantees the proper ordering and throws on invalid characters.
    let verifiedPermissions;
    if (blobSASSignatureValues.permissions) {
        if (blobSASSignatureValues.blobName) {
            verifiedPermissions = BlobSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
        else {
            verifiedPermissions = ContainerSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
    }
    // Signature is generated on the un-url-encoded values.
    const stringToSign = [
        verifiedPermissions ? verifiedPermissions : "",
        blobSASSignatureValues.startsOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.startsOn, false)
            : "",
        blobSASSignatureValues.expiresOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.expiresOn, false)
            : "",
        getCanonicalName(userDelegationKeyCredential.accountName, blobSASSignatureValues.containerName, blobSASSignatureValues.blobName),
        userDelegationKeyCredential.userDelegationKey.signedObjectId,
        userDelegationKeyCredential.userDelegationKey.signedTenantId,
        userDelegationKeyCredential.userDelegationKey.signedStartsOn
            ? utils_common_truncatedISO8061Date(userDelegationKeyCredential.userDelegationKey.signedStartsOn, false)
            : "",
        userDelegationKeyCredential.userDelegationKey.signedExpiresOn
            ? utils_common_truncatedISO8061Date(userDelegationKeyCredential.userDelegationKey.signedExpiresOn, false)
            : "",
        userDelegationKeyCredential.userDelegationKey.signedService,
        userDelegationKeyCredential.userDelegationKey.signedVersion,
        blobSASSignatureValues.preauthorizedAgentObjectId,
        undefined, // agentObjectId
        blobSASSignatureValues.correlationId,
        blobSASSignatureValues.ipRange ? ipRangeToString(blobSASSignatureValues.ipRange) : "",
        blobSASSignatureValues.protocol ? blobSASSignatureValues.protocol : "",
        blobSASSignatureValues.version,
        resource,
        timestamp,
        blobSASSignatureValues.encryptionScope,
        blobSASSignatureValues.cacheControl,
        blobSASSignatureValues.contentDisposition,
        blobSASSignatureValues.contentEncoding,
        blobSASSignatureValues.contentLanguage,
        blobSASSignatureValues.contentType,
    ].join("\n");
    const signature = userDelegationKeyCredential.computeHMACSHA256(stringToSign);
    return {
        sasQueryParameters: new SASQueryParameters(blobSASSignatureValues.version, signature, verifiedPermissions, undefined, undefined, blobSASSignatureValues.protocol, blobSASSignatureValues.startsOn, blobSASSignatureValues.expiresOn, blobSASSignatureValues.ipRange, blobSASSignatureValues.identifier, resource, blobSASSignatureValues.cacheControl, blobSASSignatureValues.contentDisposition, blobSASSignatureValues.contentEncoding, blobSASSignatureValues.contentLanguage, blobSASSignatureValues.contentType, userDelegationKeyCredential.userDelegationKey, blobSASSignatureValues.preauthorizedAgentObjectId, blobSASSignatureValues.correlationId, blobSASSignatureValues.encryptionScope),
        stringToSign: stringToSign,
    };
}
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 * IMPLEMENTATION FOR API VERSION FROM 2020-12-06.
 *
 * Creates an instance of SASQueryParameters.
 *
 * Only accepts required settings needed to create a SAS. For optional settings please
 * set corresponding properties directly, such as permissions, startsOn.
 *
 * WARNING: identifier will be ignored, permissions and expiresOn are required.
 *
 * @param blobSASSignatureValues -
 * @param userDelegationKeyCredential -
 */
function generateBlobSASQueryParametersUDK20250705(blobSASSignatureValues, userDelegationKeyCredential) {
    blobSASSignatureValues = SASSignatureValuesSanityCheckAndAutofill(blobSASSignatureValues);
    // Stored access policies are not supported for a user delegation SAS.
    if (!blobSASSignatureValues.permissions || !blobSASSignatureValues.expiresOn) {
        throw new RangeError("Must provide 'permissions' and 'expiresOn' for Blob SAS generation when generating user delegation SAS.");
    }
    let resource = "c";
    let timestamp = blobSASSignatureValues.snapshotTime;
    if (blobSASSignatureValues.blobName) {
        resource = "b";
        if (blobSASSignatureValues.snapshotTime) {
            resource = "bs";
        }
        else if (blobSASSignatureValues.versionId) {
            resource = "bv";
            timestamp = blobSASSignatureValues.versionId;
        }
    }
    // Calling parse and toString guarantees the proper ordering and throws on invalid characters.
    let verifiedPermissions;
    if (blobSASSignatureValues.permissions) {
        if (blobSASSignatureValues.blobName) {
            verifiedPermissions = BlobSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
        else {
            verifiedPermissions = ContainerSASPermissions.parse(blobSASSignatureValues.permissions.toString()).toString();
        }
    }
    // Signature is generated on the un-url-encoded values.
    const stringToSign = [
        verifiedPermissions ? verifiedPermissions : "",
        blobSASSignatureValues.startsOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.startsOn, false)
            : "",
        blobSASSignatureValues.expiresOn
            ? utils_common_truncatedISO8061Date(blobSASSignatureValues.expiresOn, false)
            : "",
        getCanonicalName(userDelegationKeyCredential.accountName, blobSASSignatureValues.containerName, blobSASSignatureValues.blobName),
        userDelegationKeyCredential.userDelegationKey.signedObjectId,
        userDelegationKeyCredential.userDelegationKey.signedTenantId,
        userDelegationKeyCredential.userDelegationKey.signedStartsOn
            ? utils_common_truncatedISO8061Date(userDelegationKeyCredential.userDelegationKey.signedStartsOn, false)
            : "",
        userDelegationKeyCredential.userDelegationKey.signedExpiresOn
            ? utils_common_truncatedISO8061Date(userDelegationKeyCredential.userDelegationKey.signedExpiresOn, false)
            : "",
        userDelegationKeyCredential.userDelegationKey.signedService,
        userDelegationKeyCredential.userDelegationKey.signedVersion,
        blobSASSignatureValues.preauthorizedAgentObjectId,
        undefined, // agentObjectId
        blobSASSignatureValues.correlationId,
        undefined, // SignedKeyDelegatedUserTenantId, will be added in a future release.
        blobSASSignatureValues.delegatedUserObjectId,
        blobSASSignatureValues.ipRange ? ipRangeToString(blobSASSignatureValues.ipRange) : "",
        blobSASSignatureValues.protocol ? blobSASSignatureValues.protocol : "",
        blobSASSignatureValues.version,
        resource,
        timestamp,
        blobSASSignatureValues.encryptionScope,
        blobSASSignatureValues.cacheControl,
        blobSASSignatureValues.contentDisposition,
        blobSASSignatureValues.contentEncoding,
        blobSASSignatureValues.contentLanguage,
        blobSASSignatureValues.contentType,
    ].join("\n");
    const signature = userDelegationKeyCredential.computeHMACSHA256(stringToSign);
    return {
        sasQueryParameters: new SASQueryParameters(blobSASSignatureValues.version, signature, verifiedPermissions, undefined, undefined, blobSASSignatureValues.protocol, blobSASSignatureValues.startsOn, blobSASSignatureValues.expiresOn, blobSASSignatureValues.ipRange, blobSASSignatureValues.identifier, resource, blobSASSignatureValues.cacheControl, blobSASSignatureValues.contentDisposition, blobSASSignatureValues.contentEncoding, blobSASSignatureValues.contentLanguage, blobSASSignatureValues.contentType, userDelegationKeyCredential.userDelegationKey, blobSASSignatureValues.preauthorizedAgentObjectId, blobSASSignatureValues.correlationId, blobSASSignatureValues.encryptionScope, blobSASSignatureValues.delegatedUserObjectId),
        stringToSign: stringToSign,
    };
}
function getCanonicalName(accountName, containerName, blobName) {
    // Container: "/blob/account/containerName"
    // Blob:      "/blob/account/containerName/blobName"
    const elements = [`/blob/${accountName}/${containerName}`];
    if (blobName) {
        elements.push(`/${blobName}`);
    }
    return elements.join("");
}
function SASSignatureValuesSanityCheckAndAutofill(blobSASSignatureValues) {
    const version = blobSASSignatureValues.version ? blobSASSignatureValues.version : SERVICE_VERSION;
    if (blobSASSignatureValues.snapshotTime && version < "2018-11-09") {
        throw RangeError("'version' must be >= '2018-11-09' when providing 'snapshotTime'.");
    }
    if (blobSASSignatureValues.blobName === undefined && blobSASSignatureValues.snapshotTime) {
        throw RangeError("Must provide 'blobName' when providing 'snapshotTime'.");
    }
    if (blobSASSignatureValues.versionId && version < "2019-10-10") {
        throw RangeError("'version' must be >= '2019-10-10' when providing 'versionId'.");
    }
    if (blobSASSignatureValues.blobName === undefined && blobSASSignatureValues.versionId) {
        throw RangeError("Must provide 'blobName' when providing 'versionId'.");
    }
    if (blobSASSignatureValues.permissions &&
        blobSASSignatureValues.permissions.setImmutabilityPolicy &&
        version < "2020-08-04") {
        throw RangeError("'version' must be >= '2020-08-04' when provided 'i' permission.");
    }
    if (blobSASSignatureValues.permissions &&
        blobSASSignatureValues.permissions.deleteVersion &&
        version < "2019-10-10") {
        throw RangeError("'version' must be >= '2019-10-10' when providing 'x' permission.");
    }
    if (blobSASSignatureValues.permissions &&
        blobSASSignatureValues.permissions.permanentDelete &&
        version < "2019-10-10") {
        throw RangeError("'version' must be >= '2019-10-10' when providing 'y' permission.");
    }
    if (blobSASSignatureValues.permissions &&
        blobSASSignatureValues.permissions.tag &&
        version < "2019-12-12") {
        throw RangeError("'version' must be >= '2019-12-12' when providing 't' permission.");
    }
    if (version < "2020-02-10" &&
        blobSASSignatureValues.permissions &&
        (blobSASSignatureValues.permissions.move || blobSASSignatureValues.permissions.execute)) {
        throw RangeError("'version' must be >= '2020-02-10' when providing the 'm' or 'e' permission.");
    }
    if (version < "2021-04-10" &&
        blobSASSignatureValues.permissions &&
        blobSASSignatureValues.permissions.filterByTags) {
        throw RangeError("'version' must be >= '2021-04-10' when providing the 'f' permission.");
    }
    if (version < "2020-02-10" &&
        (blobSASSignatureValues.preauthorizedAgentObjectId || blobSASSignatureValues.correlationId)) {
        throw RangeError("'version' must be >= '2020-02-10' when providing 'preauthorizedAgentObjectId' or 'correlationId'.");
    }
    if (blobSASSignatureValues.encryptionScope && version < "2020-12-06") {
        throw RangeError("'version' must be >= '2020-12-06' when provided 'encryptionScope' in SAS.");
    }
    blobSASSignatureValues.version = version;
    return blobSASSignatureValues;
}
//# sourceMappingURL=BlobSASSignatureValues.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/BlobLeaseClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




/**
 * A client that manages leases for a {@link ContainerClient} or a {@link BlobClient}.
 */
class BlobLeaseClient {
    _leaseId;
    _url;
    _containerOrBlobOperation;
    _isContainer;
    /**
     * Gets the lease Id.
     *
     * @readonly
     */
    get leaseId() {
        return this._leaseId;
    }
    /**
     * Gets the url.
     *
     * @readonly
     */
    get url() {
        return this._url;
    }
    /**
     * Creates an instance of BlobLeaseClient.
     * @param client - The client to make the lease operation requests.
     * @param leaseId - Initial proposed lease id.
     */
    constructor(client, leaseId) {
        const clientContext = client.storageClientContext;
        this._url = client.url;
        if (client.name === undefined) {
            this._isContainer = true;
            this._containerOrBlobOperation = clientContext.container;
        }
        else {
            this._isContainer = false;
            this._containerOrBlobOperation = clientContext.blob;
        }
        if (!leaseId) {
            leaseId = esm_randomUUID();
        }
        this._leaseId = leaseId;
    }
    /**
     * Establishes and manages a lock on a container for delete operations, or on a blob
     * for write and delete operations.
     * The lock duration can be 15 to 60 seconds, or can be infinite.
     * @see https://learn.microsoft.com/rest/api/storageservices/lease-container
     * and
     * @see https://learn.microsoft.com/rest/api/storageservices/lease-blob
     *
     * @param duration - Must be between 15 to 60 seconds, or infinite (-1)
     * @param options - option to configure lease management operations.
     * @returns Response data for acquire lease operation.
     */
    async acquireLease(duration, options = {}) {
        if (this._isContainer &&
            ((options.conditions?.ifMatch && options.conditions?.ifMatch !== ETagNone) ||
                (options.conditions?.ifNoneMatch && options.conditions?.ifNoneMatch !== ETagNone) ||
                options.conditions?.tagConditions)) {
            throw new RangeError("The IfMatch, IfNoneMatch and tags access conditions are ignored by the service. Values other than undefined or their default values are not acceptable.");
        }
        return tracingClient.withSpan("BlobLeaseClient-acquireLease", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this._containerOrBlobOperation.acquireLease({
                abortSignal: options.abortSignal,
                duration,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                proposedLeaseId: this._leaseId,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * To change the ID of the lease.
     * @see https://learn.microsoft.com/rest/api/storageservices/lease-container
     * and
     * @see https://learn.microsoft.com/rest/api/storageservices/lease-blob
     *
     * @param proposedLeaseId - the proposed new lease Id.
     * @param options - option to configure lease management operations.
     * @returns Response data for change lease operation.
     */
    async changeLease(proposedLeaseId, options = {}) {
        if (this._isContainer &&
            ((options.conditions?.ifMatch && options.conditions?.ifMatch !== ETagNone) ||
                (options.conditions?.ifNoneMatch && options.conditions?.ifNoneMatch !== ETagNone) ||
                options.conditions?.tagConditions)) {
            throw new RangeError("The IfMatch, IfNoneMatch and tags access conditions are ignored by the service. Values other than undefined or their default values are not acceptable.");
        }
        return tracingClient.withSpan("BlobLeaseClient-changeLease", options, async (updatedOptions) => {
            const response = utils_common_assertResponse(await this._containerOrBlobOperation.changeLease(this._leaseId, proposedLeaseId, {
                abortSignal: options.abortSignal,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                tracingOptions: updatedOptions.tracingOptions,
            }));
            this._leaseId = proposedLeaseId;
            return response;
        });
    }
    /**
     * To free the lease if it is no longer needed so that another client may
     * immediately acquire a lease against the container or the blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/lease-container
     * and
     * @see https://learn.microsoft.com/rest/api/storageservices/lease-blob
     *
     * @param options - option to configure lease management operations.
     * @returns Response data for release lease operation.
     */
    async releaseLease(options = {}) {
        if (this._isContainer &&
            ((options.conditions?.ifMatch && options.conditions?.ifMatch !== ETagNone) ||
                (options.conditions?.ifNoneMatch && options.conditions?.ifNoneMatch !== ETagNone) ||
                options.conditions?.tagConditions)) {
            throw new RangeError("The IfMatch, IfNoneMatch and tags access conditions are ignored by the service. Values other than undefined or their default values are not acceptable.");
        }
        return tracingClient.withSpan("BlobLeaseClient-releaseLease", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this._containerOrBlobOperation.releaseLease(this._leaseId, {
                abortSignal: options.abortSignal,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * To renew the lease.
     * @see https://learn.microsoft.com/rest/api/storageservices/lease-container
     * and
     * @see https://learn.microsoft.com/rest/api/storageservices/lease-blob
     *
     * @param options - Optional option to configure lease management operations.
     * @returns Response data for renew lease operation.
     */
    async renewLease(options = {}) {
        if (this._isContainer &&
            ((options.conditions?.ifMatch && options.conditions?.ifMatch !== ETagNone) ||
                (options.conditions?.ifNoneMatch && options.conditions?.ifNoneMatch !== ETagNone) ||
                options.conditions?.tagConditions)) {
            throw new RangeError("The IfMatch, IfNoneMatch and tags access conditions are ignored by the service. Values other than undefined or their default values are not acceptable.");
        }
        return tracingClient.withSpan("BlobLeaseClient-renewLease", options, async (updatedOptions) => {
            return this._containerOrBlobOperation.renewLease(this._leaseId, {
                abortSignal: options.abortSignal,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                tracingOptions: updatedOptions.tracingOptions,
            });
        });
    }
    /**
     * To end the lease but ensure that another client cannot acquire a new lease
     * until the current lease period has expired.
     * @see https://learn.microsoft.com/rest/api/storageservices/lease-container
     * and
     * @see https://learn.microsoft.com/rest/api/storageservices/lease-blob
     *
     * @param breakPeriod - Break period
     * @param options - Optional options to configure lease management operations.
     * @returns Response data for break lease operation.
     */
    async breakLease(breakPeriod, options = {}) {
        if (this._isContainer &&
            ((options.conditions?.ifMatch && options.conditions?.ifMatch !== ETagNone) ||
                (options.conditions?.ifNoneMatch && options.conditions?.ifNoneMatch !== ETagNone) ||
                options.conditions?.tagConditions)) {
            throw new RangeError("The IfMatch, IfNoneMatch and tags access conditions are ignored by the service. Values other than undefined or their default values are not acceptable.");
        }
        return tracingClient.withSpan("BlobLeaseClient-breakLease", options, async (updatedOptions) => {
            const operationOptions = {
                abortSignal: options.abortSignal,
                breakPeriod,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                tracingOptions: updatedOptions.tracingOptions,
            };
            return utils_common_assertResponse(await this._containerOrBlobOperation.breakLease(operationOptions));
        });
    }
}
//# sourceMappingURL=BlobLeaseClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/utils/RetriableReadableStream.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * A Node.js ReadableStream will internally retry when internal ReadableStream unexpected ends.
 */
class RetriableReadableStream extends external_node_stream_.Readable {
    start;
    offset;
    end;
    getter;
    source;
    retries = 0;
    maxRetryRequests;
    onProgress;
    options;
    /**
     * Creates an instance of RetriableReadableStream.
     *
     * @param source - The current ReadableStream returned from getter
     * @param getter - A method calling downloading request returning
     *                                      a new ReadableStream from specified offset
     * @param offset - Offset position in original data source to read
     * @param count - How much data in original data source to read
     * @param options -
     */
    constructor(source, getter, offset, count, options = {}) {
        super({ highWaterMark: options.highWaterMark });
        this.getter = getter;
        this.source = source;
        this.start = offset;
        this.offset = offset;
        this.end = offset + count - 1;
        this.maxRetryRequests =
            options.maxRetryRequests && options.maxRetryRequests >= 0 ? options.maxRetryRequests : 0;
        this.onProgress = options.onProgress;
        this.options = options;
        this.setSourceEventHandlers();
    }
    _read() {
        this.source.resume();
    }
    setSourceEventHandlers() {
        this.source.on("data", this.sourceDataHandler);
        this.source.on("end", this.sourceErrorOrEndHandler);
        this.source.on("error", this.sourceErrorOrEndHandler);
        // needed for Node14
        this.source.on("aborted", this.sourceAbortedHandler);
    }
    removeSourceEventHandlers() {
        this.source.removeListener("data", this.sourceDataHandler);
        this.source.removeListener("end", this.sourceErrorOrEndHandler);
        this.source.removeListener("error", this.sourceErrorOrEndHandler);
        this.source.removeListener("aborted", this.sourceAbortedHandler);
    }
    sourceDataHandler = (data) => {
        if (this.options.doInjectErrorOnce) {
            this.options.doInjectErrorOnce = undefined;
            this.source.pause();
            this.sourceErrorOrEndHandler();
            this.source.destroy();
            return;
        }
        // console.log(
        //   `Offset: ${this.offset}, Received ${data.length} from internal stream`
        // );
        this.offset += data.length;
        if (this.onProgress) {
            this.onProgress({ loadedBytes: this.offset - this.start });
        }
        if (!this.push(data)) {
            this.source.pause();
        }
    };
    sourceAbortedHandler = () => {
        const abortError = new AbortError_AbortError("The operation was aborted.");
        this.destroy(abortError);
    };
    sourceErrorOrEndHandler = (err) => {
        if (err && err.name === "AbortError") {
            this.destroy(err);
            return;
        }
        // console.log(
        //   `Source stream emits end or error, offset: ${
        //     this.offset
        //   }, dest end : ${this.end}`
        // );
        this.removeSourceEventHandlers();
        if (this.offset - 1 === this.end) {
            this.push(null);
        }
        else if (this.offset <= this.end) {
            // console.log(
            //   `retries: ${this.retries}, max retries: ${this.maxRetries}`
            // );
            if (this.retries < this.maxRetryRequests) {
                this.retries += 1;
                this.getter(this.offset)
                    .then((newSource) => {
                    this.source = newSource;
                    this.setSourceEventHandlers();
                    return;
                })
                    .catch((error) => {
                    this.destroy(error);
                });
            }
            else {
                this.destroy(new Error(`Data corruption failure: received less data than required and reached maxRetires limitation. Received data offset: ${this.offset - 1}, data needed offset: ${this.end}, retries: ${this.retries}, max retries: ${this.maxRetryRequests}`));
            }
        }
        else {
            this.destroy(new Error(`Data corruption failure: Received more data than original request, data needed offset is ${this.end}, received offset: ${this.offset - 1}`));
        }
    };
    _destroy(error, callback) {
        // remove listener from source and release source
        this.removeSourceEventHandlers();
        this.source.destroy();
        callback(error === null ? undefined : error);
    }
}
//# sourceMappingURL=RetriableReadableStream.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/BlobDownloadResponse.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * BlobDownloadResponse implements BlobDownloadResponseParsed interface, and in Node.js runtime it will
 * automatically retry when internal read stream unexpected ends. (This kind of unexpected ends cannot
 * trigger retries defined in pipeline retry policy.)
 *
 * The {@link readableStreamBody} stream will retry underlayer, you can just use it as a normal Node.js
 * Readable stream.
 */
class BlobDownloadResponse {
    /**
     * Indicates that the service supports
     * requests for partial file content.
     *
     * @readonly
     */
    get acceptRanges() {
        return this.originalResponse.acceptRanges;
    }
    /**
     * Returns if it was previously specified
     * for the file.
     *
     * @readonly
     */
    get cacheControl() {
        return this.originalResponse.cacheControl;
    }
    /**
     * Returns the value that was specified
     * for the 'x-ms-content-disposition' header and specifies how to process the
     * response.
     *
     * @readonly
     */
    get contentDisposition() {
        return this.originalResponse.contentDisposition;
    }
    /**
     * Returns the value that was specified
     * for the Content-Encoding request header.
     *
     * @readonly
     */
    get contentEncoding() {
        return this.originalResponse.contentEncoding;
    }
    /**
     * Returns the value that was specified
     * for the Content-Language request header.
     *
     * @readonly
     */
    get contentLanguage() {
        return this.originalResponse.contentLanguage;
    }
    /**
     * The current sequence number for a
     * page blob. This header is not returned for block blobs or append blobs.
     *
     * @readonly
     */
    get blobSequenceNumber() {
        return this.originalResponse.blobSequenceNumber;
    }
    /**
     * The blob's type. Possible values include:
     * 'BlockBlob', 'PageBlob', 'AppendBlob'.
     *
     * @readonly
     */
    get blobType() {
        return this.originalResponse.blobType;
    }
    /**
     * The number of bytes present in the
     * response body.
     *
     * @readonly
     */
    get contentLength() {
        return this.originalResponse.contentLength;
    }
    /**
     * If the file has an MD5 hash and the
     * request is to read the full file, this response header is returned so that
     * the client can check for message content integrity. If the request is to
     * read a specified range and the 'x-ms-range-get-content-md5' is set to
     * true, then the request returns an MD5 hash for the range, as long as the
     * range size is less than or equal to 4 MB. If neither of these sets of
     * conditions is true, then no value is returned for the 'Content-MD5'
     * header.
     *
     * @readonly
     */
    get contentMD5() {
        return this.originalResponse.contentMD5;
    }
    /**
     * Indicates the range of bytes returned if
     * the client requested a subset of the file by setting the Range request
     * header.
     *
     * @readonly
     */
    get contentRange() {
        return this.originalResponse.contentRange;
    }
    /**
     * The content type specified for the file.
     * The default content type is 'application/octet-stream'
     *
     * @readonly
     */
    get contentType() {
        return this.originalResponse.contentType;
    }
    /**
     * Conclusion time of the last attempted
     * Copy File operation where this file was the destination file. This value
     * can specify the time of a completed, aborted, or failed copy attempt.
     *
     * @readonly
     */
    get copyCompletedOn() {
        return this.originalResponse.copyCompletedOn;
    }
    /**
     * String identifier for the last attempted Copy
     * File operation where this file was the destination file.
     *
     * @readonly
     */
    get copyId() {
        return this.originalResponse.copyId;
    }
    /**
     * Contains the number of bytes copied and
     * the total bytes in the source in the last attempted Copy File operation
     * where this file was the destination file. Can show between 0 and
     * Content-Length bytes copied.
     *
     * @readonly
     */
    get copyProgress() {
        return this.originalResponse.copyProgress;
    }
    /**
     * URL up to 2KB in length that specifies the
     * source file used in the last attempted Copy File operation where this file
     * was the destination file.
     *
     * @readonly
     */
    get copySource() {
        return this.originalResponse.copySource;
    }
    /**
     * State of the copy operation
     * identified by 'x-ms-copy-id'. Possible values include: 'pending',
     * 'success', 'aborted', 'failed'
     *
     * @readonly
     */
    get copyStatus() {
        return this.originalResponse.copyStatus;
    }
    /**
     * Only appears when
     * x-ms-copy-status is failed or pending. Describes cause of fatal or
     * non-fatal copy operation failure.
     *
     * @readonly
     */
    get copyStatusDescription() {
        return this.originalResponse.copyStatusDescription;
    }
    /**
     * When a blob is leased,
     * specifies whether the lease is of infinite or fixed duration. Possible
     * values include: 'infinite', 'fixed'.
     *
     * @readonly
     */
    get leaseDuration() {
        return this.originalResponse.leaseDuration;
    }
    /**
     * Lease state of the blob. Possible
     * values include: 'available', 'leased', 'expired', 'breaking', 'broken'.
     *
     * @readonly
     */
    get leaseState() {
        return this.originalResponse.leaseState;
    }
    /**
     * The current lease status of the
     * blob. Possible values include: 'locked', 'unlocked'.
     *
     * @readonly
     */
    get leaseStatus() {
        return this.originalResponse.leaseStatus;
    }
    /**
     * A UTC date/time value generated by the service that
     * indicates the time at which the response was initiated.
     *
     * @readonly
     */
    get date() {
        return this.originalResponse.date;
    }
    /**
     * The number of committed blocks
     * present in the blob. This header is returned only for append blobs.
     *
     * @readonly
     */
    get blobCommittedBlockCount() {
        return this.originalResponse.blobCommittedBlockCount;
    }
    /**
     * The ETag contains a value that you can use to
     * perform operations conditionally, in quotes.
     *
     * @readonly
     */
    get etag() {
        return this.originalResponse.etag;
    }
    /**
     * The number of tags associated with the blob
     *
     * @readonly
     */
    get tagCount() {
        return this.originalResponse.tagCount;
    }
    /**
     * The error code.
     *
     * @readonly
     */
    get errorCode() {
        return this.originalResponse.errorCode;
    }
    /**
     * The value of this header is set to
     * true if the file data and application metadata are completely encrypted
     * using the specified algorithm. Otherwise, the value is set to false (when
     * the file is unencrypted, or if only parts of the file/application metadata
     * are encrypted).
     *
     * @readonly
     */
    get isServerEncrypted() {
        return this.originalResponse.isServerEncrypted;
    }
    /**
     * If the blob has a MD5 hash, and if
     * request contains range header (Range or x-ms-range), this response header
     * is returned with the value of the whole blob's MD5 value. This value may
     * or may not be equal to the value returned in Content-MD5 header, with the
     * latter calculated from the requested range.
     *
     * @readonly
     */
    get blobContentMD5() {
        return this.originalResponse.blobContentMD5;
    }
    /**
     * Returns the date and time the file was last
     * modified. Any operation that modifies the file or its properties updates
     * the last modified time.
     *
     * @readonly
     */
    get lastModified() {
        return this.originalResponse.lastModified;
    }
    /**
     * Returns the UTC date and time generated by the service that indicates the time at which the blob was
     * last read or written to.
     *
     * @readonly
     */
    get lastAccessed() {
        return this.originalResponse.lastAccessed;
    }
    /**
     * Returns the date and time the blob was created.
     *
     * @readonly
     */
    get createdOn() {
        return this.originalResponse.createdOn;
    }
    /**
     * A name-value pair
     * to associate with a file storage object.
     *
     * @readonly
     */
    get metadata() {
        return this.originalResponse.metadata;
    }
    /**
     * This header uniquely identifies the request
     * that was made and can be used for troubleshooting the request.
     *
     * @readonly
     */
    get requestId() {
        return this.originalResponse.requestId;
    }
    /**
     * If a client request id header is sent in the request, this header will be present in the
     * response with the same value.
     *
     * @readonly
     */
    get clientRequestId() {
        return this.originalResponse.clientRequestId;
    }
    /**
     * Indicates the version of the Blob service used
     * to execute the request.
     *
     * @readonly
     */
    get version() {
        return this.originalResponse.version;
    }
    /**
     * Indicates the versionId of the downloaded blob version.
     *
     * @readonly
     */
    get versionId() {
        return this.originalResponse.versionId;
    }
    /**
     * Indicates whether version of this blob is a current version.
     *
     * @readonly
     */
    get isCurrentVersion() {
        return this.originalResponse.isCurrentVersion;
    }
    /**
     * The SHA-256 hash of the encryption key used to encrypt the blob. This value is only returned
     * when the blob was encrypted with a customer-provided key.
     *
     * @readonly
     */
    get encryptionKeySha256() {
        return this.originalResponse.encryptionKeySha256;
    }
    /**
     * If the request is to read a specified range and the x-ms-range-get-content-crc64 is set to
     * true, then the request returns a crc64 for the range, as long as the range size is less than
     * or equal to 4 MB. If both x-ms-range-get-content-crc64 & x-ms-range-get-content-md5 is
     * specified in the same request, it will fail with 400(Bad Request)
     */
    get contentCrc64() {
        return this.originalResponse.contentCrc64;
    }
    /**
     * Object Replication Policy Id of the destination blob.
     *
     * @readonly
     */
    get objectReplicationDestinationPolicyId() {
        return this.originalResponse.objectReplicationDestinationPolicyId;
    }
    /**
     * Parsed Object Replication Policy Id, Rule Id(s) and status of the source blob.
     *
     * @readonly
     */
    get objectReplicationSourceProperties() {
        return this.originalResponse.objectReplicationSourceProperties;
    }
    /**
     * If this blob has been sealed.
     *
     * @readonly
     */
    get isSealed() {
        return this.originalResponse.isSealed;
    }
    /**
     * UTC date/time value generated by the service that indicates the time at which the blob immutability policy will expire.
     *
     * @readonly
     */
    get immutabilityPolicyExpiresOn() {
        return this.originalResponse.immutabilityPolicyExpiresOn;
    }
    /**
     * Indicates immutability policy mode.
     *
     * @readonly
     */
    get immutabilityPolicyMode() {
        return this.originalResponse.immutabilityPolicyMode;
    }
    /**
     * Indicates if a legal hold is present on the blob.
     *
     * @readonly
     */
    get legalHold() {
        return this.originalResponse.legalHold;
    }
    /**
     * The response body as a browser Blob.
     * Always undefined in node.js.
     *
     * @readonly
     */
    get contentAsBlob() {
        return this.originalResponse.blobBody;
    }
    /**
     * The response body as a node.js Readable stream.
     * Always undefined in the browser.
     *
     * It will automatically retry when internal read stream unexpected ends.
     *
     * @readonly
     */
    get readableStreamBody() {
        return esm_isNodeLike ? this.blobDownloadStream : undefined;
    }
    /**
     * The HTTP response.
     */
    get _response() {
        return this.originalResponse._response;
    }
    originalResponse;
    blobDownloadStream;
    /**
     * Creates an instance of BlobDownloadResponse.
     *
     * @param originalResponse -
     * @param getter -
     * @param offset -
     * @param count -
     * @param options -
     */
    constructor(originalResponse, getter, offset, count, options = {}) {
        this.originalResponse = originalResponse;
        this.blobDownloadStream = new RetriableReadableStream(this.originalResponse.readableStreamBody, getter, offset, count, options);
    }
}
//# sourceMappingURL=BlobDownloadResponse.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/internal-avro/AvroConstants.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
const AVRO_SYNC_MARKER_SIZE = 16;
const AVRO_INIT_BYTES = new Uint8Array([79, 98, 106, 1]);
const AVRO_CODEC_KEY = "avro.codec";
const AVRO_SCHEMA_KEY = "avro.schema";
//# sourceMappingURL=AvroConstants.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/internal-avro/AvroParser.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
class AvroParser {
    /**
     * Reads a fixed number of bytes from the stream.
     *
     * @param stream -
     * @param length -
     * @param options -
     */
    static async readFixedBytes(stream, length, options = {}) {
        const bytes = await stream.read(length, { abortSignal: options.abortSignal });
        if (bytes.length !== length) {
            throw new Error("Hit stream end.");
        }
        return bytes;
    }
    /**
     * Reads a single byte from the stream.
     *
     * @param stream -
     * @param options -
     */
    static async readByte(stream, options = {}) {
        const buf = await AvroParser.readFixedBytes(stream, 1, options);
        return buf[0];
    }
    // int and long are stored in variable-length zig-zag coding.
    // variable-length: https://lucene.apache.org/core/3_5_0/fileformats.html#VInt
    // zig-zag: https://developers.google.com/protocol-buffers/docs/encoding?csw=1#types
    static async readZigZagLong(stream, options = {}) {
        let zigZagEncoded = 0;
        let significanceInBit = 0;
        let byte, haveMoreByte, significanceInFloat;
        do {
            byte = await AvroParser.readByte(stream, options);
            haveMoreByte = byte & 0x80;
            zigZagEncoded |= (byte & 0x7f) << significanceInBit;
            significanceInBit += 7;
        } while (haveMoreByte && significanceInBit < 28); // bitwise operation only works for 32-bit integers
        if (haveMoreByte) {
            // Switch to float arithmetic
            // eslint-disable-next-line no-self-assign
            zigZagEncoded = zigZagEncoded;
            significanceInFloat = 268435456; // 2 ** 28.
            do {
                byte = await AvroParser.readByte(stream, options);
                zigZagEncoded += (byte & 0x7f) * significanceInFloat;
                significanceInFloat *= 128; // 2 ** 7
            } while (byte & 0x80);
            const res = (zigZagEncoded % 2 ? -(zigZagEncoded + 1) : zigZagEncoded) / 2;
            if (res < Number.MIN_SAFE_INTEGER || res > Number.MAX_SAFE_INTEGER) {
                throw new Error("Integer overflow.");
            }
            return res;
        }
        return (zigZagEncoded >> 1) ^ -(zigZagEncoded & 1);
    }
    static async readLong(stream, options = {}) {
        return AvroParser.readZigZagLong(stream, options);
    }
    static async readInt(stream, options = {}) {
        return AvroParser.readZigZagLong(stream, options);
    }
    static async readNull() {
        return null;
    }
    static async readBoolean(stream, options = {}) {
        const b = await AvroParser.readByte(stream, options);
        if (b === 1) {
            return true;
        }
        else if (b === 0) {
            return false;
        }
        else {
            throw new Error("Byte was not a boolean.");
        }
    }
    static async readFloat(stream, options = {}) {
        const u8arr = await AvroParser.readFixedBytes(stream, 4, options);
        const view = new DataView(u8arr.buffer, u8arr.byteOffset, u8arr.byteLength);
        return view.getFloat32(0, true); // littleEndian = true
    }
    static async readDouble(stream, options = {}) {
        const u8arr = await AvroParser.readFixedBytes(stream, 8, options);
        const view = new DataView(u8arr.buffer, u8arr.byteOffset, u8arr.byteLength);
        return view.getFloat64(0, true); // littleEndian = true
    }
    static async readBytes(stream, options = {}) {
        const size = await AvroParser.readLong(stream, options);
        if (size < 0) {
            throw new Error("Bytes size was negative.");
        }
        return stream.read(size, { abortSignal: options.abortSignal });
    }
    static async readString(stream, options = {}) {
        const u8arr = await AvroParser.readBytes(stream, options);
        const utf8decoder = new TextDecoder();
        return utf8decoder.decode(u8arr);
    }
    static async readMapPair(stream, readItemMethod, options = {}) {
        const key = await AvroParser.readString(stream, options);
        // FUTURE: this won't work with readFixed (currently not supported) which needs a length as the parameter.
        const value = await readItemMethod(stream, options);
        return { key, value };
    }
    static async readMap(stream, readItemMethod, options = {}) {
        const readPairMethod = (s, opts = {}) => {
            return AvroParser.readMapPair(s, readItemMethod, opts);
        };
        const pairs = await AvroParser.readArray(stream, readPairMethod, options);
        const dict = {};
        for (const pair of pairs) {
            dict[pair.key] = pair.value;
        }
        return dict;
    }
    static async readArray(stream, readItemMethod, options = {}) {
        const items = [];
        for (let count = await AvroParser.readLong(stream, options); count !== 0; count = await AvroParser.readLong(stream, options)) {
            if (count < 0) {
                // Ignore block sizes
                await AvroParser.readLong(stream, options);
                count = -count;
            }
            while (count--) {
                const item = await readItemMethod(stream, options);
                items.push(item);
            }
        }
        return items;
    }
}
var AvroComplex;
(function (AvroComplex) {
    AvroComplex["RECORD"] = "record";
    AvroComplex["ENUM"] = "enum";
    AvroComplex["ARRAY"] = "array";
    AvroComplex["MAP"] = "map";
    AvroComplex["UNION"] = "union";
    AvroComplex["FIXED"] = "fixed";
})(AvroComplex || (AvroComplex = {}));
var AvroPrimitive;
(function (AvroPrimitive) {
    AvroPrimitive["NULL"] = "null";
    AvroPrimitive["BOOLEAN"] = "boolean";
    AvroPrimitive["INT"] = "int";
    AvroPrimitive["LONG"] = "long";
    AvroPrimitive["FLOAT"] = "float";
    AvroPrimitive["DOUBLE"] = "double";
    AvroPrimitive["BYTES"] = "bytes";
    AvroPrimitive["STRING"] = "string";
})(AvroPrimitive || (AvroPrimitive = {}));
class AvroType {
    /**
     * Determines the AvroType from the Avro Schema.
     */
    // eslint-disable-next-line @typescript-eslint/no-wrapper-object-types
    static fromSchema(schema) {
        if (typeof schema === "string") {
            return AvroType.fromStringSchema(schema);
        }
        else if (Array.isArray(schema)) {
            return AvroType.fromArraySchema(schema);
        }
        else {
            return AvroType.fromObjectSchema(schema);
        }
    }
    static fromStringSchema(schema) {
        switch (schema) {
            case AvroPrimitive.NULL:
            case AvroPrimitive.BOOLEAN:
            case AvroPrimitive.INT:
            case AvroPrimitive.LONG:
            case AvroPrimitive.FLOAT:
            case AvroPrimitive.DOUBLE:
            case AvroPrimitive.BYTES:
            case AvroPrimitive.STRING:
                return new AvroPrimitiveType(schema);
            default:
                throw new Error(`Unexpected Avro type ${schema}`);
        }
    }
    static fromArraySchema(schema) {
        return new AvroUnionType(schema.map(AvroType.fromSchema));
    }
    static fromObjectSchema(schema) {
        const type = schema.type;
        // Primitives can be defined as strings or objects
        try {
            return AvroType.fromStringSchema(type);
        }
        catch {
            // no-op
        }
        switch (type) {
            case AvroComplex.RECORD:
                if (schema.aliases) {
                    throw new Error(`aliases currently is not supported, schema: ${schema}`);
                }
                if (!schema.name) {
                    throw new Error(`Required attribute 'name' doesn't exist on schema: ${schema}`);
                }
                // eslint-disable-next-line no-case-declarations
                const fields = {};
                if (!schema.fields) {
                    throw new Error(`Required attribute 'fields' doesn't exist on schema: ${schema}`);
                }
                for (const field of schema.fields) {
                    fields[field.name] = AvroType.fromSchema(field.type);
                }
                return new AvroRecordType(fields, schema.name);
            case AvroComplex.ENUM:
                if (schema.aliases) {
                    throw new Error(`aliases currently is not supported, schema: ${schema}`);
                }
                if (!schema.symbols) {
                    throw new Error(`Required attribute 'symbols' doesn't exist on schema: ${schema}`);
                }
                return new AvroEnumType(schema.symbols);
            case AvroComplex.MAP:
                if (!schema.values) {
                    throw new Error(`Required attribute 'values' doesn't exist on schema: ${schema}`);
                }
                return new AvroMapType(AvroType.fromSchema(schema.values));
            case AvroComplex.ARRAY: // Unused today
            case AvroComplex.FIXED: // Unused today
            default:
                throw new Error(`Unexpected Avro type ${type} in ${schema}`);
        }
    }
}
class AvroPrimitiveType extends AvroType {
    _primitive;
    constructor(primitive) {
        super();
        this._primitive = primitive;
    }
    // eslint-disable-next-line @typescript-eslint/no-wrapper-object-types
    read(stream, options = {}) {
        switch (this._primitive) {
            case AvroPrimitive.NULL:
                return AvroParser.readNull();
            case AvroPrimitive.BOOLEAN:
                return AvroParser.readBoolean(stream, options);
            case AvroPrimitive.INT:
                return AvroParser.readInt(stream, options);
            case AvroPrimitive.LONG:
                return AvroParser.readLong(stream, options);
            case AvroPrimitive.FLOAT:
                return AvroParser.readFloat(stream, options);
            case AvroPrimitive.DOUBLE:
                return AvroParser.readDouble(stream, options);
            case AvroPrimitive.BYTES:
                return AvroParser.readBytes(stream, options);
            case AvroPrimitive.STRING:
                return AvroParser.readString(stream, options);
            default:
                throw new Error("Unknown Avro Primitive");
        }
    }
}
class AvroEnumType extends AvroType {
    _symbols;
    constructor(symbols) {
        super();
        this._symbols = symbols;
    }
    // eslint-disable-next-line @typescript-eslint/no-wrapper-object-types
    async read(stream, options = {}) {
        const value = await AvroParser.readInt(stream, options);
        return this._symbols[value];
    }
}
class AvroUnionType extends AvroType {
    _types;
    constructor(types) {
        super();
        this._types = types;
    }
    async read(stream, options = {}) {
        const typeIndex = await AvroParser.readInt(stream, options);
        return this._types[typeIndex].read(stream, options);
    }
}
class AvroMapType extends AvroType {
    _itemType;
    constructor(itemType) {
        super();
        this._itemType = itemType;
    }
    // eslint-disable-next-line @typescript-eslint/no-wrapper-object-types
    read(stream, options = {}) {
        const readItemMethod = (s, opts) => {
            return this._itemType.read(s, opts);
        };
        return AvroParser.readMap(stream, readItemMethod, options);
    }
}
class AvroRecordType extends AvroType {
    _name;
    _fields;
    constructor(fields, name) {
        super();
        this._fields = fields;
        this._name = name;
    }
    // eslint-disable-next-line @typescript-eslint/no-wrapper-object-types
    async read(stream, options = {}) {
        // eslint-disable-next-line @typescript-eslint/no-wrapper-object-types
        const record = {};
        record["$schema"] = this._name;
        for (const key in this._fields) {
            if (Object.prototype.hasOwnProperty.call(this._fields, key)) {
                record[key] = await this._fields[key].read(stream, options);
            }
        }
        return record;
    }
}
//# sourceMappingURL=AvroParser.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/internal-avro/utils/utils.common.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
function arraysEqual(a, b) {
    if (a === b)
        return true;
    if (a == null || b == null)
        return false;
    if (a.length !== b.length)
        return false;
    for (let i = 0; i < a.length; ++i) {
        if (a[i] !== b[i])
            return false;
    }
    return true;
}
//# sourceMappingURL=utils.common.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/internal-avro/AvroReader.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
// TODO: Do a review of non-interfaces
/* eslint-disable @azure/azure-sdk/ts-use-interface-parameters */



class AvroReader {
    _dataStream;
    _headerStream;
    _syncMarker;
    _metadata;
    _itemType;
    _itemsRemainingInBlock;
    // Remembers where we started if partial data stream was provided.
    _initialBlockOffset;
    /// The byte offset within the Avro file (both header and data)
    /// of the start of the current block.
    _blockOffset;
    get blockOffset() {
        return this._blockOffset;
    }
    _objectIndex;
    get objectIndex() {
        return this._objectIndex;
    }
    _initialized;
    constructor(dataStream, headerStream, currentBlockOffset, indexWithinCurrentBlock) {
        this._dataStream = dataStream;
        this._headerStream = headerStream || dataStream;
        this._initialized = false;
        this._blockOffset = currentBlockOffset || 0;
        this._objectIndex = indexWithinCurrentBlock || 0;
        this._initialBlockOffset = currentBlockOffset || 0;
    }
    async initialize(options = {}) {
        const header = await AvroParser.readFixedBytes(this._headerStream, AVRO_INIT_BYTES.length, {
            abortSignal: options.abortSignal,
        });
        if (!arraysEqual(header, AVRO_INIT_BYTES)) {
            throw new Error("Stream is not an Avro file.");
        }
        // File metadata is written as if defined by the following map schema:
        // { "type": "map", "values": "bytes"}
        this._metadata = await AvroParser.readMap(this._headerStream, AvroParser.readString, {
            abortSignal: options.abortSignal,
        });
        // Validate codec
        const codec = this._metadata[AVRO_CODEC_KEY];
        if (!(codec === undefined || codec === null || codec === "null")) {
            throw new Error("Codecs are not supported");
        }
        // The 16-byte, randomly-generated sync marker for this file.
        this._syncMarker = await AvroParser.readFixedBytes(this._headerStream, AVRO_SYNC_MARKER_SIZE, {
            abortSignal: options.abortSignal,
        });
        // Parse the schema
        const schema = JSON.parse(this._metadata[AVRO_SCHEMA_KEY]);
        this._itemType = AvroType.fromSchema(schema);
        if (this._blockOffset === 0) {
            this._blockOffset = this._initialBlockOffset + this._dataStream.position;
        }
        this._itemsRemainingInBlock = await AvroParser.readLong(this._dataStream, {
            abortSignal: options.abortSignal,
        });
        // skip block length
        await AvroParser.readLong(this._dataStream, { abortSignal: options.abortSignal });
        this._initialized = true;
        if (this._objectIndex && this._objectIndex > 0) {
            for (let i = 0; i < this._objectIndex; i++) {
                await this._itemType.read(this._dataStream, { abortSignal: options.abortSignal });
                this._itemsRemainingInBlock--;
            }
        }
    }
    hasNext() {
        return !this._initialized || this._itemsRemainingInBlock > 0;
    }
    async *parseObjects(options = {}) {
        if (!this._initialized) {
            await this.initialize(options);
        }
        while (this.hasNext()) {
            const result = await this._itemType.read(this._dataStream, {
                abortSignal: options.abortSignal,
            });
            this._itemsRemainingInBlock--;
            this._objectIndex++;
            if (this._itemsRemainingInBlock === 0) {
                const marker = await AvroParser.readFixedBytes(this._dataStream, AVRO_SYNC_MARKER_SIZE, {
                    abortSignal: options.abortSignal,
                });
                this._blockOffset = this._initialBlockOffset + this._dataStream.position;
                this._objectIndex = 0;
                if (!arraysEqual(this._syncMarker, marker)) {
                    throw new Error("Stream is not a valid Avro file.");
                }
                try {
                    this._itemsRemainingInBlock = await AvroParser.readLong(this._dataStream, {
                        abortSignal: options.abortSignal,
                    });
                }
                catch {
                    // We hit the end of the stream.
                    this._itemsRemainingInBlock = 0;
                }
                if (this._itemsRemainingInBlock > 0) {
                    // Ignore block size
                    await AvroParser.readLong(this._dataStream, { abortSignal: options.abortSignal });
                }
            }
            yield result;
        }
    }
}
//# sourceMappingURL=AvroReader.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/internal-avro/AvroReadable.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
class AvroReadable {
}
//# sourceMappingURL=AvroReadable.js.map
// EXTERNAL MODULE: external "buffer"
var external_buffer_ = __nccwpck_require__(181);
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/internal-avro/AvroReadableFromStream.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



const ABORT_ERROR = new AbortError_AbortError("Reading from the avro stream was aborted.");
class AvroReadableFromStream extends AvroReadable {
    _position;
    _readable;
    toUint8Array(data) {
        if (typeof data === "string") {
            return external_buffer_.Buffer.from(data);
        }
        return data;
    }
    constructor(readable) {
        super();
        this._readable = readable;
        this._position = 0;
    }
    get position() {
        return this._position;
    }
    async read(size, options = {}) {
        if (options.abortSignal?.aborted) {
            throw ABORT_ERROR;
        }
        if (size < 0) {
            throw new Error(`size parameter should be positive: ${size}`);
        }
        if (size === 0) {
            return new Uint8Array();
        }
        if (!this._readable.readable) {
            throw new Error("Stream no longer readable.");
        }
        // See if there is already enough data.
        const chunk = this._readable.read(size);
        if (chunk) {
            this._position += chunk.length;
            // chunk.length maybe less than desired size if the stream ends.
            return this.toUint8Array(chunk);
        }
        else {
            // register callback to wait for enough data to read
            return new Promise((resolve, reject) => {
                /* eslint-disable @typescript-eslint/no-use-before-define */
                const cleanUp = () => {
                    this._readable.removeListener("readable", readableCallback);
                    this._readable.removeListener("error", rejectCallback);
                    this._readable.removeListener("end", rejectCallback);
                    this._readable.removeListener("close", rejectCallback);
                    if (options.abortSignal) {
                        options.abortSignal.removeEventListener("abort", abortHandler);
                    }
                };
                const readableCallback = () => {
                    const callbackChunk = this._readable.read(size);
                    if (callbackChunk) {
                        this._position += callbackChunk.length;
                        cleanUp();
                        // callbackChunk.length maybe less than desired size if the stream ends.
                        resolve(this.toUint8Array(callbackChunk));
                    }
                };
                const rejectCallback = () => {
                    cleanUp();
                    reject();
                };
                const abortHandler = () => {
                    cleanUp();
                    reject(ABORT_ERROR);
                };
                this._readable.on("readable", readableCallback);
                this._readable.once("error", rejectCallback);
                this._readable.once("end", rejectCallback);
                this._readable.once("close", rejectCallback);
                if (options.abortSignal) {
                    options.abortSignal.addEventListener("abort", abortHandler);
                }
                /* eslint-enable @typescript-eslint/no-use-before-define */
            });
        }
    }
}
//# sourceMappingURL=AvroReadableFromStream.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/internal-avro/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/utils/BlobQuickQueryStream.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * A Node.js BlobQuickQueryStream will internally parse avro data stream for blob query.
 */
class BlobQuickQueryStream extends external_node_stream_.Readable {
    source;
    avroReader;
    avroIter;
    avroPaused = true;
    onProgress;
    onError;
    /**
     * Creates an instance of BlobQuickQueryStream.
     *
     * @param source - The current ReadableStream returned from getter
     * @param options -
     */
    constructor(source, options = {}) {
        super();
        this.source = source;
        this.onProgress = options.onProgress;
        this.onError = options.onError;
        this.avroReader = new AvroReader(new AvroReadableFromStream(this.source));
        this.avroIter = this.avroReader.parseObjects({ abortSignal: options.abortSignal });
    }
    _read() {
        if (this.avroPaused) {
            this.readInternal().catch((err) => {
                this.emit("error", err);
            });
        }
    }
    async readInternal() {
        this.avroPaused = false;
        let avroNext;
        do {
            avroNext = await this.avroIter.next();
            if (avroNext.done) {
                break;
            }
            const obj = avroNext.value;
            const schema = obj.$schema;
            if (typeof schema !== "string") {
                throw Error("Missing schema in avro record.");
            }
            switch (schema) {
                case "com.microsoft.azure.storage.queryBlobContents.resultData":
                    {
                        const data = obj.data;
                        if (data instanceof Uint8Array === false) {
                            throw Error("Invalid data in avro result record.");
                        }
                        if (!this.push(Buffer.from(data))) {
                            this.avroPaused = true;
                        }
                    }
                    break;
                case "com.microsoft.azure.storage.queryBlobContents.progress":
                    {
                        const bytesScanned = obj.bytesScanned;
                        if (typeof bytesScanned !== "number") {
                            throw Error("Invalid bytesScanned in avro progress record.");
                        }
                        if (this.onProgress) {
                            this.onProgress({ loadedBytes: bytesScanned });
                        }
                    }
                    break;
                case "com.microsoft.azure.storage.queryBlobContents.end":
                    if (this.onProgress) {
                        const totalBytes = obj.totalBytes;
                        if (typeof totalBytes !== "number") {
                            throw Error("Invalid totalBytes in avro end record.");
                        }
                        this.onProgress({ loadedBytes: totalBytes });
                    }
                    this.push(null);
                    break;
                case "com.microsoft.azure.storage.queryBlobContents.error":
                    if (this.onError) {
                        const fatal = obj.fatal;
                        if (typeof fatal !== "boolean") {
                            throw Error("Invalid fatal in avro error record.");
                        }
                        const name = obj.name;
                        if (typeof name !== "string") {
                            throw Error("Invalid name in avro error record.");
                        }
                        const description = obj.description;
                        if (typeof description !== "string") {
                            throw Error("Invalid description in avro error record.");
                        }
                        const position = obj.position;
                        if (typeof position !== "number") {
                            throw Error("Invalid position in avro error record.");
                        }
                        this.onError({
                            position,
                            name,
                            isFatal: fatal,
                            description,
                        });
                    }
                    break;
                default:
                    throw Error(`Unknown schema ${schema} in avro progress record.`);
            }
        } while (!avroNext.done && !this.avroPaused);
    }
}
//# sourceMappingURL=BlobQuickQueryStream.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/BlobQueryResponse.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * BlobQueryResponse implements BlobDownloadResponseModel interface, and in Node.js runtime it will
 * parse avro data returned by blob query.
 */
class BlobQueryResponse {
    /**
     * Indicates that the service supports
     * requests for partial file content.
     *
     * @readonly
     */
    get acceptRanges() {
        return this.originalResponse.acceptRanges;
    }
    /**
     * Returns if it was previously specified
     * for the file.
     *
     * @readonly
     */
    get cacheControl() {
        return this.originalResponse.cacheControl;
    }
    /**
     * Returns the value that was specified
     * for the 'x-ms-content-disposition' header and specifies how to process the
     * response.
     *
     * @readonly
     */
    get contentDisposition() {
        return this.originalResponse.contentDisposition;
    }
    /**
     * Returns the value that was specified
     * for the Content-Encoding request header.
     *
     * @readonly
     */
    get contentEncoding() {
        return this.originalResponse.contentEncoding;
    }
    /**
     * Returns the value that was specified
     * for the Content-Language request header.
     *
     * @readonly
     */
    get contentLanguage() {
        return this.originalResponse.contentLanguage;
    }
    /**
     * The current sequence number for a
     * page blob. This header is not returned for block blobs or append blobs.
     *
     * @readonly
     */
    get blobSequenceNumber() {
        return this.originalResponse.blobSequenceNumber;
    }
    /**
     * The blob's type. Possible values include:
     * 'BlockBlob', 'PageBlob', 'AppendBlob'.
     *
     * @readonly
     */
    get blobType() {
        return this.originalResponse.blobType;
    }
    /**
     * The number of bytes present in the
     * response body.
     *
     * @readonly
     */
    get contentLength() {
        return this.originalResponse.contentLength;
    }
    /**
     * If the file has an MD5 hash and the
     * request is to read the full file, this response header is returned so that
     * the client can check for message content integrity. If the request is to
     * read a specified range and the 'x-ms-range-get-content-md5' is set to
     * true, then the request returns an MD5 hash for the range, as long as the
     * range size is less than or equal to 4 MB. If neither of these sets of
     * conditions is true, then no value is returned for the 'Content-MD5'
     * header.
     *
     * @readonly
     */
    get contentMD5() {
        return this.originalResponse.contentMD5;
    }
    /**
     * Indicates the range of bytes returned if
     * the client requested a subset of the file by setting the Range request
     * header.
     *
     * @readonly
     */
    get contentRange() {
        return this.originalResponse.contentRange;
    }
    /**
     * The content type specified for the file.
     * The default content type is 'application/octet-stream'
     *
     * @readonly
     */
    get contentType() {
        return this.originalResponse.contentType;
    }
    /**
     * Conclusion time of the last attempted
     * Copy File operation where this file was the destination file. This value
     * can specify the time of a completed, aborted, or failed copy attempt.
     *
     * @readonly
     */
    get copyCompletedOn() {
        return undefined;
    }
    /**
     * String identifier for the last attempted Copy
     * File operation where this file was the destination file.
     *
     * @readonly
     */
    get copyId() {
        return this.originalResponse.copyId;
    }
    /**
     * Contains the number of bytes copied and
     * the total bytes in the source in the last attempted Copy File operation
     * where this file was the destination file. Can show between 0 and
     * Content-Length bytes copied.
     *
     * @readonly
     */
    get copyProgress() {
        return this.originalResponse.copyProgress;
    }
    /**
     * URL up to 2KB in length that specifies the
     * source file used in the last attempted Copy File operation where this file
     * was the destination file.
     *
     * @readonly
     */
    get copySource() {
        return this.originalResponse.copySource;
    }
    /**
     * State of the copy operation
     * identified by 'x-ms-copy-id'. Possible values include: 'pending',
     * 'success', 'aborted', 'failed'
     *
     * @readonly
     */
    get copyStatus() {
        return this.originalResponse.copyStatus;
    }
    /**
     * Only appears when
     * x-ms-copy-status is failed or pending. Describes cause of fatal or
     * non-fatal copy operation failure.
     *
     * @readonly
     */
    get copyStatusDescription() {
        return this.originalResponse.copyStatusDescription;
    }
    /**
     * When a blob is leased,
     * specifies whether the lease is of infinite or fixed duration. Possible
     * values include: 'infinite', 'fixed'.
     *
     * @readonly
     */
    get leaseDuration() {
        return this.originalResponse.leaseDuration;
    }
    /**
     * Lease state of the blob. Possible
     * values include: 'available', 'leased', 'expired', 'breaking', 'broken'.
     *
     * @readonly
     */
    get leaseState() {
        return this.originalResponse.leaseState;
    }
    /**
     * The current lease status of the
     * blob. Possible values include: 'locked', 'unlocked'.
     *
     * @readonly
     */
    get leaseStatus() {
        return this.originalResponse.leaseStatus;
    }
    /**
     * A UTC date/time value generated by the service that
     * indicates the time at which the response was initiated.
     *
     * @readonly
     */
    get date() {
        return this.originalResponse.date;
    }
    /**
     * The number of committed blocks
     * present in the blob. This header is returned only for append blobs.
     *
     * @readonly
     */
    get blobCommittedBlockCount() {
        return this.originalResponse.blobCommittedBlockCount;
    }
    /**
     * The ETag contains a value that you can use to
     * perform operations conditionally, in quotes.
     *
     * @readonly
     */
    get etag() {
        return this.originalResponse.etag;
    }
    /**
     * The error code.
     *
     * @readonly
     */
    get errorCode() {
        return this.originalResponse.errorCode;
    }
    /**
     * The value of this header is set to
     * true if the file data and application metadata are completely encrypted
     * using the specified algorithm. Otherwise, the value is set to false (when
     * the file is unencrypted, or if only parts of the file/application metadata
     * are encrypted).
     *
     * @readonly
     */
    get isServerEncrypted() {
        return this.originalResponse.isServerEncrypted;
    }
    /**
     * If the blob has a MD5 hash, and if
     * request contains range header (Range or x-ms-range), this response header
     * is returned with the value of the whole blob's MD5 value. This value may
     * or may not be equal to the value returned in Content-MD5 header, with the
     * latter calculated from the requested range.
     *
     * @readonly
     */
    get blobContentMD5() {
        return this.originalResponse.blobContentMD5;
    }
    /**
     * Returns the date and time the file was last
     * modified. Any operation that modifies the file or its properties updates
     * the last modified time.
     *
     * @readonly
     */
    get lastModified() {
        return this.originalResponse.lastModified;
    }
    /**
     * A name-value pair
     * to associate with a file storage object.
     *
     * @readonly
     */
    get metadata() {
        return this.originalResponse.metadata;
    }
    /**
     * This header uniquely identifies the request
     * that was made and can be used for troubleshooting the request.
     *
     * @readonly
     */
    get requestId() {
        return this.originalResponse.requestId;
    }
    /**
     * If a client request id header is sent in the request, this header will be present in the
     * response with the same value.
     *
     * @readonly
     */
    get clientRequestId() {
        return this.originalResponse.clientRequestId;
    }
    /**
     * Indicates the version of the File service used
     * to execute the request.
     *
     * @readonly
     */
    get version() {
        return this.originalResponse.version;
    }
    /**
     * The SHA-256 hash of the encryption key used to encrypt the blob. This value is only returned
     * when the blob was encrypted with a customer-provided key.
     *
     * @readonly
     */
    get encryptionKeySha256() {
        return this.originalResponse.encryptionKeySha256;
    }
    /**
     * If the request is to read a specified range and the x-ms-range-get-content-crc64 is set to
     * true, then the request returns a crc64 for the range, as long as the range size is less than
     * or equal to 4 MB. If both x-ms-range-get-content-crc64 & x-ms-range-get-content-md5 is
     * specified in the same request, it will fail with 400(Bad Request)
     */
    get contentCrc64() {
        return this.originalResponse.contentCrc64;
    }
    /**
     * The response body as a browser Blob.
     * Always undefined in node.js.
     *
     * @readonly
     */
    get blobBody() {
        return undefined;
    }
    /**
     * The response body as a node.js Readable stream.
     * Always undefined in the browser.
     *
     * It will parse avor data returned by blob query.
     *
     * @readonly
     */
    get readableStreamBody() {
        return esm_isNodeLike ? this.blobDownloadStream : undefined;
    }
    /**
     * The HTTP response.
     */
    get _response() {
        return this.originalResponse._response;
    }
    originalResponse;
    blobDownloadStream;
    /**
     * Creates an instance of BlobQueryResponse.
     *
     * @param originalResponse -
     * @param options -
     */
    constructor(originalResponse, options = {}) {
        this.originalResponse = originalResponse;
        this.blobDownloadStream = new BlobQuickQueryStream(this.originalResponse.readableStreamBody, options);
    }
}
//# sourceMappingURL=BlobQueryResponse.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/models.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Represents the access tier on a blob.
 * For detailed information about block blob level tiering see {@link https://learn.microsoft.com/azure/storage/blobs/storage-blob-storage-tiers|Hot, cool and archive storage tiers.}
 */
var BlockBlobTier;
(function (BlockBlobTier) {
    /**
     * Optimized for storing data that is accessed frequently.
     */
    BlockBlobTier["Hot"] = "Hot";
    /**
     * Optimized for storing data that is infrequently accessed and stored for at least 30 days.
     */
    BlockBlobTier["Cool"] = "Cool";
    /**
     * Optimized for storing data that is rarely accessed.
     */
    BlockBlobTier["Cold"] = "Cold";
    /**
     * Optimized for storing data that is rarely accessed and stored for at least 180 days
     * with flexible latency requirements (on the order of hours).
     */
    BlockBlobTier["Archive"] = "Archive";
})(BlockBlobTier || (BlockBlobTier = {}));
/**
 * Specifies the page blob tier to set the blob to. This is only applicable to page blobs on premium storage accounts.
 * Please see {@link https://learn.microsoft.com/azure/storage/storage-premium-storage#scalability-and-performance-targets|here}
 * for detailed information on the corresponding IOPS and throughput per PageBlobTier.
 */
var PremiumPageBlobTier;
(function (PremiumPageBlobTier) {
    /**
     * P4 Tier.
     */
    PremiumPageBlobTier["P4"] = "P4";
    /**
     * P6 Tier.
     */
    PremiumPageBlobTier["P6"] = "P6";
    /**
     * P10 Tier.
     */
    PremiumPageBlobTier["P10"] = "P10";
    /**
     * P15 Tier.
     */
    PremiumPageBlobTier["P15"] = "P15";
    /**
     * P20 Tier.
     */
    PremiumPageBlobTier["P20"] = "P20";
    /**
     * P30 Tier.
     */
    PremiumPageBlobTier["P30"] = "P30";
    /**
     * P40 Tier.
     */
    PremiumPageBlobTier["P40"] = "P40";
    /**
     * P50 Tier.
     */
    PremiumPageBlobTier["P50"] = "P50";
    /**
     * P60 Tier.
     */
    PremiumPageBlobTier["P60"] = "P60";
    /**
     * P70 Tier.
     */
    PremiumPageBlobTier["P70"] = "P70";
    /**
     * P80 Tier.
     */
    PremiumPageBlobTier["P80"] = "P80";
})(PremiumPageBlobTier || (PremiumPageBlobTier = {}));
function toAccessTier(tier) {
    if (tier === undefined) {
        return undefined;
    }
    return tier; // No more check if string is a valid AccessTier, and left this to underlay logic to decide(service).
}
function ensureCpkIfSpecified(cpk, isHttps) {
    if (cpk && !isHttps) {
        throw new RangeError("Customer-provided encryption key must be used over HTTPS.");
    }
    if (cpk && !cpk.encryptionAlgorithm) {
        cpk.encryptionAlgorithm = EncryptionAlgorithmAES25;
    }
}
/**
 * Defines the known cloud audiences for Storage.
 */
var StorageBlobAudience;
(function (StorageBlobAudience) {
    /**
     * The OAuth scope to use to retrieve an AAD token for Azure Storage.
     */
    StorageBlobAudience["StorageOAuthScopes"] = "https://storage.azure.com/.default";
    /**
     * The OAuth scope to use to retrieve an AAD token for Azure Disk.
     */
    StorageBlobAudience["DiskComputeOAuthScopes"] = "https://disk.compute.azure.com/.default";
})(StorageBlobAudience || (StorageBlobAudience = {}));
/**
 *
 * To get OAuth audience for a storage account for blob service.
 */
function getBlobServiceAccountAudience(storageAccountName) {
    return `https://${storageAccountName}.blob.core.windows.net/.default`;
}
//# sourceMappingURL=models.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/PageBlobRangeResponse.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Function that converts PageRange and ClearRange to a common Range object.
 * PageRange and ClearRange have start and end while Range offset and count
 * this function normalizes to Range.
 * @param response - Model PageBlob Range response
 */
function rangeResponseFromModel(response) {
    const pageRange = (response._response.parsedBody.pageRange || []).map((x) => ({
        offset: x.start,
        count: x.end - x.start,
    }));
    const clearRange = (response._response.parsedBody.clearRange || []).map((x) => ({
        offset: x.start,
        count: x.end - x.start,
    }));
    return {
        ...response,
        pageRange,
        clearRange,
        _response: {
            ...response._response,
            parsedBody: {
                pageRange,
                clearRange,
            },
        },
    };
}
//# sourceMappingURL=PageBlobRangeResponse.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/logger.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

/**
 * The `@azure/logger` configuration for this package.
 * @internal
 */
const logger_logger = esm_createClientLogger("core-lro");
//# sourceMappingURL=logger.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/poller/constants.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.
/**
 * The default time interval to wait before sending the next polling request.
 */
const constants_POLL_INTERVAL_IN_MS = 2000;
/**
 * The closed set of terminal states.
 */
const terminalStates = ["succeeded", "canceled", "failed"];
//# sourceMappingURL=constants.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/poller/operation.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.


/**
 * Deserializes the state
 */
function operation_deserializeState(serializedState) {
    try {
        return JSON.parse(serializedState).state;
    }
    catch (e) {
        throw new Error(`Unable to deserialize input state: ${serializedState}`);
    }
}
function setStateError(inputs) {
    const { state, stateProxy, isOperationError } = inputs;
    return (error) => {
        if (isOperationError(error)) {
            stateProxy.setError(state, error);
            stateProxy.setFailed(state);
        }
        throw error;
    };
}
function appendReadableErrorMessage(currentMessage, innerMessage) {
    let message = currentMessage;
    if (message.slice(-1) !== ".") {
        message = message + ".";
    }
    return message + " " + innerMessage;
}
function simplifyError(err) {
    let message = err.message;
    let code = err.code;
    let curErr = err;
    while (curErr.innererror) {
        curErr = curErr.innererror;
        code = curErr.code;
        message = appendReadableErrorMessage(message, curErr.message);
    }
    return {
        code,
        message,
    };
}
function processOperationStatus(result) {
    const { state, stateProxy, status, isDone, processResult, getError, response, setErrorAsResult } = result;
    switch (status) {
        case "succeeded": {
            stateProxy.setSucceeded(state);
            break;
        }
        case "failed": {
            const err = getError === null || getError === void 0 ? void 0 : getError(response);
            let postfix = "";
            if (err) {
                const { code, message } = simplifyError(err);
                postfix = `. ${code}. ${message}`;
            }
            const errStr = `The long-running operation has failed${postfix}`;
            stateProxy.setError(state, new Error(errStr));
            stateProxy.setFailed(state);
            logger_logger.warning(errStr);
            break;
        }
        case "canceled": {
            stateProxy.setCanceled(state);
            break;
        }
    }
    if ((isDone === null || isDone === void 0 ? void 0 : isDone(response, state)) ||
        (isDone === undefined &&
            ["succeeded", "canceled"].concat(setErrorAsResult ? [] : ["failed"]).includes(status))) {
        stateProxy.setResult(state, buildResult({
            response,
            state,
            processResult,
        }));
    }
}
function buildResult(inputs) {
    const { processResult, response, state } = inputs;
    return processResult ? processResult(response, state) : response;
}
/**
 * Initiates the long-running operation.
 */
async function operation_initOperation(inputs) {
    const { init, stateProxy, processResult, getOperationStatus, withOperationLocation, setErrorAsResult, } = inputs;
    const { operationLocation, resourceLocation, metadata, response } = await init();
    if (operationLocation)
        withOperationLocation === null || withOperationLocation === void 0 ? void 0 : withOperationLocation(operationLocation, false);
    const config = {
        metadata,
        operationLocation,
        resourceLocation,
    };
    logger_logger.verbose(`LRO: Operation description:`, config);
    const state = stateProxy.initState(config);
    const status = getOperationStatus({ response, state, operationLocation });
    processOperationStatus({ state, status, stateProxy, response, setErrorAsResult, processResult });
    return state;
}
async function pollOperationHelper(inputs) {
    const { poll, state, stateProxy, operationLocation, getOperationStatus, getResourceLocation, isOperationError, options, } = inputs;
    const response = await poll(operationLocation, options).catch(setStateError({
        state,
        stateProxy,
        isOperationError,
    }));
    const status = getOperationStatus(response, state);
    logger_logger.verbose(`LRO: Status:\n\tPolling from: ${state.config.operationLocation}\n\tOperation status: ${status}\n\tPolling status: ${terminalStates.includes(status) ? "Stopped" : "Running"}`);
    if (status === "succeeded") {
        const resourceLocation = getResourceLocation(response, state);
        if (resourceLocation !== undefined) {
            return {
                response: await poll(resourceLocation).catch(setStateError({ state, stateProxy, isOperationError })),
                status,
            };
        }
    }
    return { response, status };
}
/** Polls the long-running operation. */
async function operation_pollOperation(inputs) {
    const { poll, state, stateProxy, options, getOperationStatus, getResourceLocation, getOperationLocation, isOperationError, withOperationLocation, getPollingInterval, processResult, getError, updateState, setDelay, isDone, setErrorAsResult, } = inputs;
    const { operationLocation } = state.config;
    if (operationLocation !== undefined) {
        const { response, status } = await pollOperationHelper({
            poll,
            getOperationStatus,
            state,
            stateProxy,
            operationLocation,
            getResourceLocation,
            isOperationError,
            options,
        });
        processOperationStatus({
            status,
            response,
            state,
            stateProxy,
            isDone,
            processResult,
            getError,
            setErrorAsResult,
        });
        if (!terminalStates.includes(status)) {
            const intervalInMs = getPollingInterval === null || getPollingInterval === void 0 ? void 0 : getPollingInterval(response);
            if (intervalInMs)
                setDelay(intervalInMs);
            const location = getOperationLocation === null || getOperationLocation === void 0 ? void 0 : getOperationLocation(response, state);
            if (location !== undefined) {
                const isUpdated = operationLocation !== location;
                state.config.operationLocation = location;
                withOperationLocation === null || withOperationLocation === void 0 ? void 0 : withOperationLocation(location, isUpdated);
            }
            else
                withOperationLocation === null || withOperationLocation === void 0 ? void 0 : withOperationLocation(operationLocation, false);
        }
        updateState === null || updateState === void 0 ? void 0 : updateState(state, response);
    }
}
//# sourceMappingURL=operation.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/http/operation.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.


function getOperationLocationPollingUrl(inputs) {
    const { azureAsyncOperation, operationLocation } = inputs;
    return operationLocation !== null && operationLocation !== void 0 ? operationLocation : azureAsyncOperation;
}
function getLocationHeader(rawResponse) {
    return rawResponse.headers["location"];
}
function getOperationLocationHeader(rawResponse) {
    return rawResponse.headers["operation-location"];
}
function getAzureAsyncOperationHeader(rawResponse) {
    return rawResponse.headers["azure-asyncoperation"];
}
function findResourceLocation(inputs) {
    var _a;
    const { location, requestMethod, requestPath, resourceLocationConfig } = inputs;
    switch (requestMethod) {
        case "PUT": {
            return requestPath;
        }
        case "DELETE": {
            return undefined;
        }
        case "PATCH": {
            return (_a = getDefault()) !== null && _a !== void 0 ? _a : requestPath;
        }
        default: {
            return getDefault();
        }
    }
    function getDefault() {
        switch (resourceLocationConfig) {
            case "azure-async-operation": {
                return undefined;
            }
            case "original-uri": {
                return requestPath;
            }
            case "location":
            default: {
                return location;
            }
        }
    }
}
function operation_inferLroMode(inputs) {
    const { rawResponse, requestMethod, requestPath, resourceLocationConfig } = inputs;
    const operationLocation = getOperationLocationHeader(rawResponse);
    const azureAsyncOperation = getAzureAsyncOperationHeader(rawResponse);
    const pollingUrl = getOperationLocationPollingUrl({ operationLocation, azureAsyncOperation });
    const location = getLocationHeader(rawResponse);
    const normalizedRequestMethod = requestMethod === null || requestMethod === void 0 ? void 0 : requestMethod.toLocaleUpperCase();
    if (pollingUrl !== undefined) {
        return {
            mode: "OperationLocation",
            operationLocation: pollingUrl,
            resourceLocation: findResourceLocation({
                requestMethod: normalizedRequestMethod,
                location,
                requestPath,
                resourceLocationConfig,
            }),
        };
    }
    else if (location !== undefined) {
        return {
            mode: "ResourceLocation",
            operationLocation: location,
        };
    }
    else if (normalizedRequestMethod === "PUT" && requestPath) {
        return {
            mode: "Body",
            operationLocation: requestPath,
        };
    }
    else {
        return undefined;
    }
}
function transformStatus(inputs) {
    const { status, statusCode } = inputs;
    if (typeof status !== "string" && status !== undefined) {
        throw new Error(`Polling was unsuccessful. Expected status to have a string value or no value but it has instead: ${status}. This doesn't necessarily indicate the operation has failed. Check your Azure subscription or resource status for more information.`);
    }
    switch (status === null || status === void 0 ? void 0 : status.toLocaleLowerCase()) {
        case undefined:
            return toOperationStatus(statusCode);
        case "succeeded":
            return "succeeded";
        case "failed":
            return "failed";
        case "running":
        case "accepted":
        case "started":
        case "canceling":
        case "cancelling":
            return "running";
        case "canceled":
        case "cancelled":
            return "canceled";
        default: {
            logger_logger.verbose(`LRO: unrecognized operation status: ${status}`);
            return status;
        }
    }
}
function getStatus(rawResponse) {
    var _a;
    const { status } = (_a = rawResponse.body) !== null && _a !== void 0 ? _a : {};
    return transformStatus({ status, statusCode: rawResponse.statusCode });
}
function getProvisioningState(rawResponse) {
    var _a, _b;
    const { properties, provisioningState } = (_a = rawResponse.body) !== null && _a !== void 0 ? _a : {};
    const status = (_b = properties === null || properties === void 0 ? void 0 : properties.provisioningState) !== null && _b !== void 0 ? _b : provisioningState;
    return transformStatus({ status, statusCode: rawResponse.statusCode });
}
function toOperationStatus(statusCode) {
    if (statusCode === 202) {
        return "running";
    }
    else if (statusCode < 300) {
        return "succeeded";
    }
    else {
        return "failed";
    }
}
function operation_parseRetryAfter({ rawResponse }) {
    const retryAfter = rawResponse.headers["retry-after"];
    if (retryAfter !== undefined) {
        // Retry-After header value is either in HTTP date format, or in seconds
        const retryAfterInSeconds = parseInt(retryAfter);
        return isNaN(retryAfterInSeconds)
            ? calculatePollingIntervalFromDate(new Date(retryAfter))
            : retryAfterInSeconds * 1000;
    }
    return undefined;
}
function operation_getErrorFromResponse(response) {
    const error = accessBodyProperty(response, "error");
    if (!error) {
        logger_logger.warning(`The long-running operation failed but there is no error property in the response's body`);
        return;
    }
    if (!error.code || !error.message) {
        logger_logger.warning(`The long-running operation failed but the error property in the response's body doesn't contain code or message`);
        return;
    }
    return error;
}
function calculatePollingIntervalFromDate(retryAfterDate) {
    const timeNow = Math.floor(new Date().getTime());
    const retryAfterTime = retryAfterDate.getTime();
    if (timeNow < retryAfterTime) {
        return retryAfterTime - timeNow;
    }
    return undefined;
}
function operation_getStatusFromInitialResponse(inputs) {
    const { response, state, operationLocation } = inputs;
    function helper() {
        var _a;
        const mode = (_a = state.config.metadata) === null || _a === void 0 ? void 0 : _a["mode"];
        switch (mode) {
            case undefined:
                return toOperationStatus(response.rawResponse.statusCode);
            case "Body":
                return operation_getOperationStatus(response, state);
            default:
                return "running";
        }
    }
    const status = helper();
    return status === "running" && operationLocation === undefined ? "succeeded" : status;
}
/**
 * Initiates the long-running operation.
 */
async function initHttpOperation(inputs) {
    const { stateProxy, resourceLocationConfig, processResult, lro, setErrorAsResult } = inputs;
    return operation_initOperation({
        init: async () => {
            const response = await lro.sendInitialRequest();
            const config = operation_inferLroMode({
                rawResponse: response.rawResponse,
                requestPath: lro.requestPath,
                requestMethod: lro.requestMethod,
                resourceLocationConfig,
            });
            return Object.assign({ response, operationLocation: config === null || config === void 0 ? void 0 : config.operationLocation, resourceLocation: config === null || config === void 0 ? void 0 : config.resourceLocation }, ((config === null || config === void 0 ? void 0 : config.mode) ? { metadata: { mode: config.mode } } : {}));
        },
        stateProxy,
        processResult: processResult
            ? ({ flatResponse }, state) => processResult(flatResponse, state)
            : ({ flatResponse }) => flatResponse,
        getOperationStatus: operation_getStatusFromInitialResponse,
        setErrorAsResult,
    });
}
function operation_getOperationLocation({ rawResponse }, state) {
    var _a;
    const mode = (_a = state.config.metadata) === null || _a === void 0 ? void 0 : _a["mode"];
    switch (mode) {
        case "OperationLocation": {
            return getOperationLocationPollingUrl({
                operationLocation: getOperationLocationHeader(rawResponse),
                azureAsyncOperation: getAzureAsyncOperationHeader(rawResponse),
            });
        }
        case "ResourceLocation": {
            return getLocationHeader(rawResponse);
        }
        case "Body":
        default: {
            return undefined;
        }
    }
}
function operation_getOperationStatus({ rawResponse }, state) {
    var _a;
    const mode = (_a = state.config.metadata) === null || _a === void 0 ? void 0 : _a["mode"];
    switch (mode) {
        case "OperationLocation": {
            return getStatus(rawResponse);
        }
        case "ResourceLocation": {
            return toOperationStatus(rawResponse.statusCode);
        }
        case "Body": {
            return getProvisioningState(rawResponse);
        }
        default:
            throw new Error(`Internal error: Unexpected operation mode: ${mode}`);
    }
}
function accessBodyProperty({ flatResponse, rawResponse }, prop) {
    var _a, _b;
    return (_a = flatResponse === null || flatResponse === void 0 ? void 0 : flatResponse[prop]) !== null && _a !== void 0 ? _a : (_b = rawResponse.body) === null || _b === void 0 ? void 0 : _b[prop];
}
function operation_getResourceLocation(res, state) {
    const loc = accessBodyProperty(res, "resourceLocation");
    if (loc && typeof loc === "string") {
        state.config.resourceLocation = loc;
    }
    return state.config.resourceLocation;
}
function operation_isOperationError(e) {
    return e.name === "RestError";
}
/** Polls the long-running operation. */
async function pollHttpOperation(inputs) {
    const { lro, stateProxy, options, processResult, updateState, setDelay, state, setErrorAsResult, } = inputs;
    return operation_pollOperation({
        state,
        stateProxy,
        setDelay,
        processResult: processResult
            ? ({ flatResponse }, inputState) => processResult(flatResponse, inputState)
            : ({ flatResponse }) => flatResponse,
        getError: operation_getErrorFromResponse,
        updateState,
        getPollingInterval: operation_parseRetryAfter,
        getOperationLocation: operation_getOperationLocation,
        getOperationStatus: operation_getOperationStatus,
        isOperationError: operation_isOperationError,
        getResourceLocation: operation_getResourceLocation,
        options,
        /**
         * The expansion here is intentional because `lro` could be an object that
         * references an inner this, so we need to preserve a reference to it.
         */
        poll: async (location, inputOptions) => lro.sendPollRequest(location, inputOptions),
        setErrorAsResult,
    });
}
//# sourceMappingURL=operation.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/poller/poller.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.



const createStateProxy = () => ({
    /**
     * The state at this point is created to be of type OperationState<TResult>.
     * It will be updated later to be of type TState when the
     * customer-provided callback, `updateState`, is called during polling.
     */
    initState: (config) => ({ status: "running", config }),
    setCanceled: (state) => (state.status = "canceled"),
    setError: (state, error) => (state.error = error),
    setResult: (state, result) => (state.result = result),
    setRunning: (state) => (state.status = "running"),
    setSucceeded: (state) => (state.status = "succeeded"),
    setFailed: (state) => (state.status = "failed"),
    getError: (state) => state.error,
    getResult: (state) => state.result,
    isCanceled: (state) => state.status === "canceled",
    isFailed: (state) => state.status === "failed",
    isRunning: (state) => state.status === "running",
    isSucceeded: (state) => state.status === "succeeded",
});
/**
 * Returns a poller factory.
 */
function poller_buildCreatePoller(inputs) {
    const { getOperationLocation, getStatusFromInitialResponse, getStatusFromPollResponse, isOperationError, getResourceLocation, getPollingInterval, getError, resolveOnUnsuccessful, } = inputs;
    return async ({ init, poll }, options) => {
        const { processResult, updateState, withOperationLocation: withOperationLocationCallback, intervalInMs = POLL_INTERVAL_IN_MS, restoreFrom, } = options || {};
        const stateProxy = createStateProxy();
        const withOperationLocation = withOperationLocationCallback
            ? (() => {
                let called = false;
                return (operationLocation, isUpdated) => {
                    if (isUpdated)
                        withOperationLocationCallback(operationLocation);
                    else if (!called)
                        withOperationLocationCallback(operationLocation);
                    called = true;
                };
            })()
            : undefined;
        const state = restoreFrom
            ? deserializeState(restoreFrom)
            : await initOperation({
                init,
                stateProxy,
                processResult,
                getOperationStatus: getStatusFromInitialResponse,
                withOperationLocation,
                setErrorAsResult: !resolveOnUnsuccessful,
            });
        let resultPromise;
        const abortController = new AbortController();
        const handlers = new Map();
        const handleProgressEvents = async () => handlers.forEach((h) => h(state));
        const cancelErrMsg = "Operation was canceled";
        let currentPollIntervalInMs = intervalInMs;
        const poller = {
            getOperationState: () => state,
            getResult: () => state.result,
            isDone: () => ["succeeded", "failed", "canceled"].includes(state.status),
            isStopped: () => resultPromise === undefined,
            stopPolling: () => {
                abortController.abort();
            },
            toString: () => JSON.stringify({
                state,
            }),
            onProgress: (callback) => {
                const s = Symbol();
                handlers.set(s, callback);
                return () => handlers.delete(s);
            },
            pollUntilDone: (pollOptions) => (resultPromise !== null && resultPromise !== void 0 ? resultPromise : (resultPromise = (async () => {
                const { abortSignal: inputAbortSignal } = pollOptions || {};
                // In the future we can use AbortSignal.any() instead
                function abortListener() {
                    abortController.abort();
                }
                const abortSignal = abortController.signal;
                if (inputAbortSignal === null || inputAbortSignal === void 0 ? void 0 : inputAbortSignal.aborted) {
                    abortController.abort();
                }
                else if (!abortSignal.aborted) {
                    inputAbortSignal === null || inputAbortSignal === void 0 ? void 0 : inputAbortSignal.addEventListener("abort", abortListener, { once: true });
                }
                try {
                    if (!poller.isDone()) {
                        await poller.poll({ abortSignal });
                        while (!poller.isDone()) {
                            await delay(currentPollIntervalInMs, { abortSignal });
                            await poller.poll({ abortSignal });
                        }
                    }
                }
                finally {
                    inputAbortSignal === null || inputAbortSignal === void 0 ? void 0 : inputAbortSignal.removeEventListener("abort", abortListener);
                }
                if (resolveOnUnsuccessful) {
                    return poller.getResult();
                }
                else {
                    switch (state.status) {
                        case "succeeded":
                            return poller.getResult();
                        case "canceled":
                            throw new Error(cancelErrMsg);
                        case "failed":
                            throw state.error;
                        case "notStarted":
                        case "running":
                            throw new Error(`Polling completed without succeeding or failing`);
                    }
                }
            })().finally(() => {
                resultPromise = undefined;
            }))),
            async poll(pollOptions) {
                if (resolveOnUnsuccessful) {
                    if (poller.isDone())
                        return;
                }
                else {
                    switch (state.status) {
                        case "succeeded":
                            return;
                        case "canceled":
                            throw new Error(cancelErrMsg);
                        case "failed":
                            throw state.error;
                    }
                }
                await pollOperation({
                    poll,
                    state,
                    stateProxy,
                    getOperationLocation,
                    isOperationError,
                    withOperationLocation,
                    getPollingInterval,
                    getOperationStatus: getStatusFromPollResponse,
                    getResourceLocation,
                    processResult,
                    getError,
                    updateState,
                    options: pollOptions,
                    setDelay: (pollIntervalInMs) => {
                        currentPollIntervalInMs = pollIntervalInMs;
                    },
                    setErrorAsResult: !resolveOnUnsuccessful,
                });
                await handleProgressEvents();
                if (!resolveOnUnsuccessful) {
                    switch (state.status) {
                        case "canceled":
                            throw new Error(cancelErrMsg);
                        case "failed":
                            throw state.error;
                    }
                }
            },
        };
        return poller;
    };
}
//# sourceMappingURL=poller.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/http/poller.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.


/**
 * Creates a poller that can be used to poll a long-running operation.
 * @param lro - Description of the long-running operation
 * @param options - options to configure the poller
 * @returns an initialized poller
 */
async function createHttpPoller(lro, options) {
    const { resourceLocationConfig, intervalInMs, processResult, restoreFrom, updateState, withOperationLocation, resolveOnUnsuccessful = false, } = options || {};
    return buildCreatePoller({
        getStatusFromInitialResponse,
        getStatusFromPollResponse: getOperationStatus,
        isOperationError,
        getOperationLocation,
        getResourceLocation,
        getPollingInterval: parseRetryAfter,
        getError: getErrorFromResponse,
        resolveOnUnsuccessful,
    })({
        init: async () => {
            const response = await lro.sendInitialRequest();
            const config = inferLroMode({
                rawResponse: response.rawResponse,
                requestPath: lro.requestPath,
                requestMethod: lro.requestMethod,
                resourceLocationConfig,
            });
            return Object.assign({ response, operationLocation: config === null || config === void 0 ? void 0 : config.operationLocation, resourceLocation: config === null || config === void 0 ? void 0 : config.resourceLocation }, ((config === null || config === void 0 ? void 0 : config.mode) ? { metadata: { mode: config.mode } } : {}));
        },
        poll: lro.sendPollRequest,
    }, {
        intervalInMs,
        withOperationLocation,
        restoreFrom,
        updateState,
        processResult: processResult
            ? ({ flatResponse }, state) => processResult(flatResponse, state)
            : ({ flatResponse }) => flatResponse,
    });
}
//# sourceMappingURL=poller.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/legacy/lroEngine/operation.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.


const operation_createStateProxy = () => ({
    initState: (config) => ({ config, isStarted: true }),
    setCanceled: (state) => (state.isCancelled = true),
    setError: (state, error) => (state.error = error),
    setResult: (state, result) => (state.result = result),
    setRunning: (state) => (state.isStarted = true),
    setSucceeded: (state) => (state.isCompleted = true),
    setFailed: () => {
        /** empty body */
    },
    getError: (state) => state.error,
    getResult: (state) => state.result,
    isCanceled: (state) => !!state.isCancelled,
    isFailed: (state) => !!state.error,
    isRunning: (state) => !!state.isStarted,
    isSucceeded: (state) => Boolean(state.isCompleted && !state.isCancelled && !state.error),
});
class GenericPollOperation {
    constructor(state, lro, setErrorAsResult, lroResourceLocationConfig, processResult, updateState, isDone) {
        this.state = state;
        this.lro = lro;
        this.setErrorAsResult = setErrorAsResult;
        this.lroResourceLocationConfig = lroResourceLocationConfig;
        this.processResult = processResult;
        this.updateState = updateState;
        this.isDone = isDone;
    }
    setPollerConfig(pollerConfig) {
        this.pollerConfig = pollerConfig;
    }
    async update(options) {
        var _a;
        const stateProxy = operation_createStateProxy();
        if (!this.state.isStarted) {
            this.state = Object.assign(Object.assign({}, this.state), (await initHttpOperation({
                lro: this.lro,
                stateProxy,
                resourceLocationConfig: this.lroResourceLocationConfig,
                processResult: this.processResult,
                setErrorAsResult: this.setErrorAsResult,
            })));
        }
        const updateState = this.updateState;
        const isDone = this.isDone;
        if (!this.state.isCompleted && this.state.error === undefined) {
            await pollHttpOperation({
                lro: this.lro,
                state: this.state,
                stateProxy,
                processResult: this.processResult,
                updateState: updateState
                    ? (state, { rawResponse }) => updateState(state, rawResponse)
                    : undefined,
                isDone: isDone
                    ? ({ flatResponse }, state) => isDone(flatResponse, state)
                    : undefined,
                options,
                setDelay: (intervalInMs) => {
                    this.pollerConfig.intervalInMs = intervalInMs;
                },
                setErrorAsResult: this.setErrorAsResult,
            });
        }
        (_a = options === null || options === void 0 ? void 0 : options.fireProgress) === null || _a === void 0 ? void 0 : _a.call(options, this.state);
        return this;
    }
    async cancel() {
        logger_logger.error("`cancelOperation` is deprecated because it wasn't implemented");
        return this;
    }
    /**
     * Serializes the Poller operation.
     */
    toString() {
        return JSON.stringify({
            state: this.state,
        });
    }
}
//# sourceMappingURL=operation.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/legacy/poller.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.
/**
 * When a poller is manually stopped through the `stopPolling` method,
 * the poller will be rejected with an instance of the PollerStoppedError.
 */
class PollerStoppedError extends Error {
    constructor(message) {
        super(message);
        this.name = "PollerStoppedError";
        Object.setPrototypeOf(this, PollerStoppedError.prototype);
    }
}
/**
 * When the operation is cancelled, the poller will be rejected with an instance
 * of the PollerCancelledError.
 */
class PollerCancelledError extends Error {
    constructor(message) {
        super(message);
        this.name = "PollerCancelledError";
        Object.setPrototypeOf(this, PollerCancelledError.prototype);
    }
}
/**
 * A class that represents the definition of a program that polls through consecutive requests
 * until it reaches a state of completion.
 *
 * A poller can be executed manually, by polling request by request by calling to the `poll()` method repeatedly, until its operation is completed.
 * It also provides a way to wait until the operation completes, by calling `pollUntilDone()` and waiting until the operation finishes.
 * Pollers can also request the cancellation of the ongoing process to whom is providing the underlying long running operation.
 *
 * ```ts
 * const poller = new MyPoller();
 *
 * // Polling just once:
 * await poller.poll();
 *
 * // We can try to cancel the request here, by calling:
 * //
 * //     await poller.cancelOperation();
 * //
 *
 * // Getting the final result:
 * const result = await poller.pollUntilDone();
 * ```
 *
 * The Poller is defined by two types, a type representing the state of the poller, which
 * must include a basic set of properties from `PollOperationState<TResult>`,
 * and a return type defined by `TResult`, which can be anything.
 *
 * The Poller class implements the `PollerLike` interface, which allows poller implementations to avoid having
 * to export the Poller's class directly, and instead only export the already instantiated poller with the PollerLike type.
 *
 * ```ts
 * class Client {
 *   public async makePoller: PollerLike<MyOperationState, MyResult> {
 *     const poller = new MyPoller({});
 *     // It might be preferred to return the poller after the first request is made,
 *     // so that some information can be obtained right away.
 *     await poller.poll();
 *     return poller;
 *   }
 * }
 *
 * const poller: PollerLike<MyOperationState, MyResult> = myClient.makePoller();
 * ```
 *
 * A poller can be created through its constructor, then it can be polled until it's completed.
 * At any point in time, the state of the poller can be obtained without delay through the getOperationState method.
 * At any point in time, the intermediate forms of the result type can be requested without delay.
 * Once the underlying operation is marked as completed, the poller will stop and the final value will be returned.
 *
 * ```ts
 * const poller = myClient.makePoller();
 * const state: MyOperationState = poller.getOperationState();
 *
 * // The intermediate result can be obtained at any time.
 * const result: MyResult | undefined = poller.getResult();
 *
 * // The final result can only be obtained after the poller finishes.
 * const result: MyResult = await poller.pollUntilDone();
 * ```
 *
 */
// eslint-disable-next-line no-use-before-define
class Poller {
    /**
     * A poller needs to be initialized by passing in at least the basic properties of the `PollOperation<TState, TResult>`.
     *
     * When writing an implementation of a Poller, this implementation needs to deal with the initialization
     * of any custom state beyond the basic definition of the poller. The basic poller assumes that the poller's
     * operation has already been defined, at least its basic properties. The code below shows how to approach
     * the definition of the constructor of a new custom poller.
     *
     * ```ts
     * export class MyPoller extends Poller<MyOperationState, string> {
     *   constructor({
     *     // Anything you might need outside of the basics
     *   }) {
     *     let state: MyOperationState = {
     *       privateProperty: private,
     *       publicProperty: public,
     *     };
     *
     *     const operation = {
     *       state,
     *       update,
     *       cancel,
     *       toString
     *     }
     *
     *     // Sending the operation to the parent's constructor.
     *     super(operation);
     *
     *     // You can assign more local properties here.
     *   }
     * }
     * ```
     *
     * Inside of this constructor, a new promise is created. This will be used to
     * tell the user when the poller finishes (see `pollUntilDone()`). The promise's
     * resolve and reject methods are also used internally to control when to resolve
     * or reject anyone waiting for the poller to finish.
     *
     * The constructor of a custom implementation of a poller is where any serialized version of
     * a previous poller's operation should be deserialized into the operation sent to the
     * base constructor. For example:
     *
     * ```ts
     * export class MyPoller extends Poller<MyOperationState, string> {
     *   constructor(
     *     baseOperation: string | undefined
     *   ) {
     *     let state: MyOperationState = {};
     *     if (baseOperation) {
     *       state = {
     *         ...JSON.parse(baseOperation).state,
     *         ...state
     *       };
     *     }
     *     const operation = {
     *       state,
     *       // ...
     *     }
     *     super(operation);
     *   }
     * }
     * ```
     *
     * @param operation - Must contain the basic properties of `PollOperation<State, TResult>`.
     */
    constructor(operation) {
        /** controls whether to throw an error if the operation failed or was canceled. */
        this.resolveOnUnsuccessful = false;
        this.stopped = true;
        this.pollProgressCallbacks = [];
        this.operation = operation;
        this.promise = new Promise((resolve, reject) => {
            this.resolve = resolve;
            this.reject = reject;
        });
        // This prevents the UnhandledPromiseRejectionWarning in node.js from being thrown.
        // The above warning would get thrown if `poller.poll` is called, it returns an error,
        // and pullUntilDone did not have a .catch or await try/catch on it's return value.
        this.promise.catch(() => {
            /* intentionally blank */
        });
    }
    /**
     * Starts a loop that will break only if the poller is done
     * or if the poller is stopped.
     */
    async startPolling(pollOptions = {}) {
        if (this.stopped) {
            this.stopped = false;
        }
        while (!this.isStopped() && !this.isDone()) {
            await this.poll(pollOptions);
            await this.delay();
        }
    }
    /**
     * pollOnce does one polling, by calling to the update method of the underlying
     * poll operation to make any relevant change effective.
     *
     * It only optionally receives an object with an abortSignal property, from \@azure/abort-controller's AbortSignalLike.
     *
     * @param options - Optional properties passed to the operation's update method.
     */
    async pollOnce(options = {}) {
        if (!this.isDone()) {
            this.operation = await this.operation.update({
                abortSignal: options.abortSignal,
                fireProgress: this.fireProgress.bind(this),
            });
        }
        this.processUpdatedState();
    }
    /**
     * fireProgress calls the functions passed in via onProgress the method of the poller.
     *
     * It loops over all of the callbacks received from onProgress, and executes them, sending them
     * the current operation state.
     *
     * @param state - The current operation state.
     */
    fireProgress(state) {
        for (const callback of this.pollProgressCallbacks) {
            callback(state);
        }
    }
    /**
     * Invokes the underlying operation's cancel method.
     */
    async cancelOnce(options = {}) {
        this.operation = await this.operation.cancel(options);
    }
    /**
     * Returns a promise that will resolve once a single polling request finishes.
     * It does this by calling the update method of the Poller's operation.
     *
     * It only optionally receives an object with an abortSignal property, from \@azure/abort-controller's AbortSignalLike.
     *
     * @param options - Optional properties passed to the operation's update method.
     */
    poll(options = {}) {
        if (!this.pollOncePromise) {
            this.pollOncePromise = this.pollOnce(options);
            const clearPollOncePromise = () => {
                this.pollOncePromise = undefined;
            };
            this.pollOncePromise.then(clearPollOncePromise, clearPollOncePromise).catch(this.reject);
        }
        return this.pollOncePromise;
    }
    processUpdatedState() {
        if (this.operation.state.error) {
            this.stopped = true;
            if (!this.resolveOnUnsuccessful) {
                this.reject(this.operation.state.error);
                throw this.operation.state.error;
            }
        }
        if (this.operation.state.isCancelled) {
            this.stopped = true;
            if (!this.resolveOnUnsuccessful) {
                const error = new PollerCancelledError("Operation was canceled");
                this.reject(error);
                throw error;
            }
        }
        if (this.isDone() && this.resolve) {
            // If the poller has finished polling, this means we now have a result.
            // However, it can be the case that TResult is instantiated to void, so
            // we are not expecting a result anyway. To assert that we might not
            // have a result eventually after finishing polling, we cast the result
            // to TResult.
            this.resolve(this.getResult());
        }
    }
    /**
     * Returns a promise that will resolve once the underlying operation is completed.
     */
    async pollUntilDone(pollOptions = {}) {
        if (this.stopped) {
            this.startPolling(pollOptions).catch(this.reject);
        }
        // This is needed because the state could have been updated by
        // `cancelOperation`, e.g. the operation is canceled or an error occurred.
        this.processUpdatedState();
        return this.promise;
    }
    /**
     * Invokes the provided callback after each polling is completed,
     * sending the current state of the poller's operation.
     *
     * It returns a method that can be used to stop receiving updates on the given callback function.
     */
    onProgress(callback) {
        this.pollProgressCallbacks.push(callback);
        return () => {
            this.pollProgressCallbacks = this.pollProgressCallbacks.filter((c) => c !== callback);
        };
    }
    /**
     * Returns true if the poller has finished polling.
     */
    isDone() {
        const state = this.operation.state;
        return Boolean(state.isCompleted || state.isCancelled || state.error);
    }
    /**
     * Stops the poller from continuing to poll.
     */
    stopPolling() {
        if (!this.stopped) {
            this.stopped = true;
            if (this.reject) {
                this.reject(new PollerStoppedError("This poller is already stopped"));
            }
        }
    }
    /**
     * Returns true if the poller is stopped.
     */
    isStopped() {
        return this.stopped;
    }
    /**
     * Attempts to cancel the underlying operation.
     *
     * It only optionally receives an object with an abortSignal property, from \@azure/abort-controller's AbortSignalLike.
     *
     * If it's called again before it finishes, it will throw an error.
     *
     * @param options - Optional properties passed to the operation's update method.
     */
    cancelOperation(options = {}) {
        if (!this.cancelPromise) {
            this.cancelPromise = this.cancelOnce(options);
        }
        else if (options.abortSignal) {
            throw new Error("A cancel request is currently pending");
        }
        return this.cancelPromise;
    }
    /**
     * Returns the state of the operation.
     *
     * Even though TState will be the same type inside any of the methods of any extension of the Poller class,
     * implementations of the pollers can customize what's shared with the public by writing their own
     * version of the `getOperationState` method, and by defining two types, one representing the internal state of the poller
     * and a public type representing a safe to share subset of the properties of the internal state.
     * Their definition of getOperationState can then return their public type.
     *
     * Example:
     *
     * ```ts
     * // Let's say we have our poller's operation state defined as:
     * interface MyOperationState extends PollOperationState<ResultType> {
     *   privateProperty?: string;
     *   publicProperty?: string;
     * }
     *
     * // To allow us to have a true separation of public and private state, we have to define another interface:
     * interface PublicState extends PollOperationState<ResultType> {
     *   publicProperty?: string;
     * }
     *
     * // Then, we define our Poller as follows:
     * export class MyPoller extends Poller<MyOperationState, ResultType> {
     *   // ... More content is needed here ...
     *
     *   public getOperationState(): PublicState {
     *     const state: PublicState = this.operation.state;
     *     return {
     *       // Properties from PollOperationState<TResult>
     *       isStarted: state.isStarted,
     *       isCompleted: state.isCompleted,
     *       isCancelled: state.isCancelled,
     *       error: state.error,
     *       result: state.result,
     *
     *       // The only other property needed by PublicState.
     *       publicProperty: state.publicProperty
     *     }
     *   }
     * }
     * ```
     *
     * You can see this in the tests of this repository, go to the file:
     * `../test/utils/testPoller.ts`
     * and look for the getOperationState implementation.
     */
    getOperationState() {
        return this.operation.state;
    }
    /**
     * Returns the result value of the operation,
     * regardless of the state of the poller.
     * It can return undefined or an incomplete form of the final TResult value
     * depending on the implementation.
     */
    getResult() {
        const state = this.operation.state;
        return state.result;
    }
    /**
     * Returns a serialized version of the poller's operation
     * by invoking the operation's toString method.
     */
    toString() {
        return this.operation.toString();
    }
}
//# sourceMappingURL=poller.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/legacy/lroEngine/lroEngine.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.




/**
 * The LRO Engine, a class that performs polling.
 */
class LroEngine extends Poller {
    constructor(lro, options) {
        const { intervalInMs = constants_POLL_INTERVAL_IN_MS, resumeFrom, resolveOnUnsuccessful = false, isDone, lroResourceLocationConfig, processResult, updateState, } = options || {};
        const state = resumeFrom
            ? operation_deserializeState(resumeFrom)
            : {};
        const operation = new GenericPollOperation(state, lro, !resolveOnUnsuccessful, lroResourceLocationConfig, processResult, updateState, isDone);
        super(operation);
        this.resolveOnUnsuccessful = resolveOnUnsuccessful;
        this.config = { intervalInMs: intervalInMs };
        operation.setPollerConfig(this.config);
    }
    /**
     * The method used by the poller to wait before attempting to update its operation.
     */
    delay() {
        return new Promise((resolve) => setTimeout(() => resolve(), this.config.intervalInMs));
    }
}
//# sourceMappingURL=lroEngine.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/legacy/lroEngine/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-lro/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

/**
 * This can be uncommented to expose the protocol-agnostic poller
 */
// export {
//   BuildCreatePollerOptions,
//   Operation,
//   CreatePollerOptions,
//   OperationConfig,
//   RestorableOperationState,
// } from "./poller/models";
// export { buildCreatePoller } from "./poller/poller";
/** legacy */



//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/pollers/BlobStartCopyFromUrlPoller.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * This is the poller returned by {@link BlobClient.beginCopyFromURL}.
 * This can not be instantiated directly outside of this package.
 *
 * @hidden
 */
class BlobBeginCopyFromUrlPoller extends Poller {
    intervalInMs;
    constructor(options) {
        const { blobClient, copySource, intervalInMs = 15000, onProgress, resumeFrom, startCopyFromURLOptions, } = options;
        let state;
        if (resumeFrom) {
            state = JSON.parse(resumeFrom).state;
        }
        const operation = makeBlobBeginCopyFromURLPollOperation({
            ...state,
            blobClient,
            copySource,
            startCopyFromURLOptions,
        });
        super(operation);
        if (typeof onProgress === "function") {
            this.onProgress(onProgress);
        }
        this.intervalInMs = intervalInMs;
    }
    delay() {
        return delay_delay(this.intervalInMs);
    }
}
/**
 * Note: Intentionally using function expression over arrow function expression
 * so that the function can be invoked with a different context.
 * This affects what `this` refers to.
 * @hidden
 */
const cancel = async function cancel(options = {}) {
    const state = this.state;
    const { copyId } = state;
    if (state.isCompleted) {
        return makeBlobBeginCopyFromURLPollOperation(state);
    }
    if (!copyId) {
        state.isCancelled = true;
        return makeBlobBeginCopyFromURLPollOperation(state);
    }
    // if abortCopyFromURL throws, it will bubble up to user's poller.cancelOperation call
    await state.blobClient.abortCopyFromURL(copyId, {
        abortSignal: options.abortSignal,
    });
    state.isCancelled = true;
    return makeBlobBeginCopyFromURLPollOperation(state);
};
/**
 * Note: Intentionally using function expression over arrow function expression
 * so that the function can be invoked with a different context.
 * This affects what `this` refers to.
 * @hidden
 */
const update = async function update(options = {}) {
    const state = this.state;
    const { blobClient, copySource, startCopyFromURLOptions } = state;
    if (!state.isStarted) {
        state.isStarted = true;
        const result = await blobClient.startCopyFromURL(copySource, startCopyFromURLOptions);
        // copyId is needed to abort
        state.copyId = result.copyId;
        if (result.copyStatus === "success") {
            state.result = result;
            state.isCompleted = true;
        }
    }
    else if (!state.isCompleted) {
        try {
            const result = await state.blobClient.getProperties({ abortSignal: options.abortSignal });
            const { copyStatus, copyProgress } = result;
            const prevCopyProgress = state.copyProgress;
            if (copyProgress) {
                state.copyProgress = copyProgress;
            }
            if (copyStatus === "pending" &&
                copyProgress !== prevCopyProgress &&
                typeof options.fireProgress === "function") {
                // trigger in setTimeout, or swallow error?
                options.fireProgress(state);
            }
            else if (copyStatus === "success") {
                state.result = result;
                state.isCompleted = true;
            }
            else if (copyStatus === "failed") {
                state.error = new Error(`Blob copy failed with reason: "${result.copyStatusDescription || "unknown"}"`);
                state.isCompleted = true;
            }
        }
        catch (err) {
            state.error = err;
            state.isCompleted = true;
        }
    }
    return makeBlobBeginCopyFromURLPollOperation(state);
};
/**
 * Note: Intentionally using function expression over arrow function expression
 * so that the function can be invoked with a different context.
 * This affects what `this` refers to.
 * @hidden
 */
const BlobStartCopyFromUrlPoller_toString = function toString() {
    return JSON.stringify({ state: this.state }, (key, value) => {
        // remove blobClient from serialized state since a client can't be hydrated from this info.
        if (key === "blobClient") {
            return undefined;
        }
        return value;
    });
};
/**
 * Creates a poll operation given the provided state.
 * @hidden
 */
function makeBlobBeginCopyFromURLPollOperation(state) {
    return {
        state: { ...state },
        cancel,
        toString: BlobStartCopyFromUrlPoller_toString,
        update,
    };
}
//# sourceMappingURL=BlobStartCopyFromUrlPoller.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/Range.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Generate a range string. For example:
 *
 * "bytes=255-" or "bytes=0-511"
 *
 * @param iRange -
 */
function rangeToString(iRange) {
    if (iRange.offset < 0) {
        throw new RangeError(`Range.offset cannot be smaller than 0.`);
    }
    if (iRange.count && iRange.count <= 0) {
        throw new RangeError(`Range.count must be larger than 0. Leave it undefined if you want a range from offset to the end.`);
    }
    return iRange.count
        ? `bytes=${iRange.offset}-${iRange.offset + iRange.count - 1}`
        : `bytes=${iRange.offset}-`;
}
//# sourceMappingURL=Range.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/utils/Batch.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
// In browser, during webpack or browserify bundling, this module will be replaced by 'events'
// https://github.com/Gozala/events

/**
 * States for Batch.
 */
var BatchStates;
(function (BatchStates) {
    BatchStates[BatchStates["Good"] = 0] = "Good";
    BatchStates[BatchStates["Error"] = 1] = "Error";
})(BatchStates || (BatchStates = {}));
/**
 * Batch provides basic parallel execution with concurrency limits.
 * Will stop execute left operations when one of the executed operation throws an error.
 * But Batch cannot cancel ongoing operations, you need to cancel them by yourself.
 */
class Batch {
    /**
     * Concurrency. Must be lager than 0.
     */
    concurrency;
    /**
     * Number of active operations under execution.
     */
    actives = 0;
    /**
     * Number of completed operations under execution.
     */
    completed = 0;
    /**
     * Offset of next operation to be executed.
     */
    offset = 0;
    /**
     * Operation array to be executed.
     */
    operations = [];
    /**
     * States of Batch. When an error happens, state will turn into error.
     * Batch will stop execute left operations.
     */
    state = BatchStates.Good;
    /**
     * A private emitter used to pass events inside this class.
     */
    emitter;
    /**
     * Creates an instance of Batch.
     * @param concurrency -
     */
    constructor(concurrency = 5) {
        if (concurrency < 1) {
            throw new RangeError("concurrency must be larger than 0");
        }
        this.concurrency = concurrency;
        this.emitter = new external_events_.EventEmitter();
    }
    /**
     * Add a operation into queue.
     *
     * @param operation -
     */
    addOperation(operation) {
        this.operations.push(async () => {
            try {
                this.actives++;
                await operation();
                this.actives--;
                this.completed++;
                this.parallelExecute();
            }
            catch (error) {
                this.emitter.emit("error", error);
            }
        });
    }
    /**
     * Start execute operations in the queue.
     *
     */
    async do() {
        if (this.operations.length === 0) {
            return Promise.resolve();
        }
        this.parallelExecute();
        return new Promise((resolve, reject) => {
            this.emitter.on("finish", resolve);
            this.emitter.on("error", (error) => {
                this.state = BatchStates.Error;
                reject(error);
            });
        });
    }
    /**
     * Get next operation to be executed. Return null when reaching ends.
     *
     */
    nextOperation() {
        if (this.offset < this.operations.length) {
            return this.operations[this.offset++];
        }
        return null;
    }
    /**
     * Start execute operations. One one the most important difference between
     * this method with do() is that do() wraps as an sync method.
     *
     */
    parallelExecute() {
        if (this.state === BatchStates.Error) {
            return;
        }
        if (this.completed >= this.operations.length) {
            this.emitter.emit("finish");
            return;
        }
        while (this.actives < this.concurrency) {
            const operation = this.nextOperation();
            if (operation) {
                operation();
            }
            else {
                return;
            }
        }
    }
}
//# sourceMappingURL=Batch.js.map
// EXTERNAL MODULE: external "node:fs"
var external_node_fs_ = __nccwpck_require__(3024);
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/utils/utils.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * Reads a readable stream into buffer. Fill the buffer from offset to end.
 *
 * @param stream - A Node.js Readable stream
 * @param buffer - Buffer to be filled, length must greater than or equal to offset
 * @param offset - From which position in the buffer to be filled, inclusive
 * @param end - To which position in the buffer to be filled, exclusive
 * @param encoding - Encoding of the Readable stream
 */
async function streamToBuffer(stream, buffer, offset, end, encoding) {
    let pos = 0; // Position in stream
    const count = end - offset; // Total amount of data needed in stream
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error(`The operation cannot be completed in timeout.`)), REQUEST_TIMEOUT);
        stream.on("readable", () => {
            if (pos >= count) {
                clearTimeout(timeout);
                resolve();
                return;
            }
            let chunk = stream.read();
            if (!chunk) {
                return;
            }
            if (typeof chunk === "string") {
                chunk = Buffer.from(chunk, encoding);
            }
            // How much data needed in this chunk
            const chunkLength = pos + chunk.length > count ? count - pos : chunk.length;
            buffer.fill(chunk.slice(0, chunkLength), offset + pos, offset + pos + chunkLength);
            pos += chunkLength;
        });
        stream.on("end", () => {
            clearTimeout(timeout);
            if (pos < count) {
                reject(new Error(`Stream drains before getting enough data needed. Data read: ${pos}, data need: ${count}`));
            }
            resolve();
        });
        stream.on("error", (msg) => {
            clearTimeout(timeout);
            reject(msg);
        });
    });
}
/**
 * Reads a readable stream into buffer entirely.
 *
 * @param stream - A Node.js Readable stream
 * @param buffer - Buffer to be filled, length must greater than or equal to offset
 * @param encoding - Encoding of the Readable stream
 * @returns with the count of bytes read.
 * @throws `RangeError` If buffer size is not big enough.
 */
async function streamToBuffer2(stream, buffer, encoding) {
    let pos = 0; // Position in stream
    const bufferSize = buffer.length;
    return new Promise((resolve, reject) => {
        stream.on("readable", () => {
            let chunk = stream.read();
            if (!chunk) {
                return;
            }
            if (typeof chunk === "string") {
                chunk = Buffer.from(chunk, encoding);
            }
            if (pos + chunk.length > bufferSize) {
                reject(new Error(`Stream exceeds buffer size. Buffer size: ${bufferSize}`));
                return;
            }
            buffer.fill(chunk, pos, pos + chunk.length);
            pos += chunk.length;
        });
        stream.on("end", () => {
            resolve(pos);
        });
        stream.on("error", reject);
    });
}
/**
 * Reads a readable stream into a buffer.
 *
 * @param stream - A Node.js Readable stream
 * @param encoding - Encoding of the Readable stream
 * @returns with the count of bytes read.
 */
async function streamToBuffer3(readableStream, encoding) {
    return new Promise((resolve, reject) => {
        const chunks = [];
        readableStream.on("data", (data) => {
            chunks.push(typeof data === "string" ? Buffer.from(data, encoding) : data);
        });
        readableStream.on("end", () => {
            resolve(Buffer.concat(chunks));
        });
        readableStream.on("error", reject);
    });
}
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * Writes the content of a readstream to a local file. Returns a Promise which is completed after the file handle is closed.
 *
 * @param rs - The read stream.
 * @param file - Destination file path.
 */
async function readStreamToLocalFile(rs, file) {
    return new Promise((resolve, reject) => {
        const ws = external_node_fs_.createWriteStream(file);
        rs.on("error", (err) => {
            reject(err);
        });
        ws.on("error", (err) => {
            reject(err);
        });
        ws.on("close", resolve);
        rs.pipe(ws);
    });
}
/**
 * ONLY AVAILABLE IN NODE.JS RUNTIME.
 *
 * Promisified version of fs.stat().
 */
const fsStat = external_node_util_.promisify(external_node_fs_.stat);
const fsCreateReadStream = external_node_fs_.createReadStream;
//# sourceMappingURL=utils.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/Clients.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.





















/**
 * A BlobClient represents a URL to an Azure Storage blob; the blob may be a block blob,
 * append blob, or page blob.
 */
class BlobClient extends StorageClient_StorageClient {
    /**
     * blobContext provided by protocol layer.
     */
    blobContext;
    _name;
    _containerName;
    _versionId;
    _snapshot;
    /**
     * The name of the blob.
     */
    get name() {
        return this._name;
    }
    /**
     * The name of the storage container the blob is associated with.
     */
    get containerName() {
        return this._containerName;
    }
    constructor(urlOrConnectionString, credentialOrPipelineOrContainerName, blobNameOrOptions, 
    // Legacy, no fix for eslint error without breaking. Disable it for this interface.
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    options) {
        options = options || {};
        let pipeline;
        let url;
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
            options = blobNameOrOptions;
            pipeline = newPipeline(credentialOrPipelineOrContainerName, options);
        }
        else if (!credentialOrPipelineOrContainerName &&
            typeof credentialOrPipelineOrContainerName !== "string") {
            // (url: string, credential?: StorageSharedKeyCredential | AnonymousCredential | TokenCredential, options?: StoragePipelineOptions)
            // The second parameter is undefined. Use anonymous credential.
            url = urlOrConnectionString;
            if (blobNameOrOptions && typeof blobNameOrOptions !== "string") {
                options = blobNameOrOptions;
            }
            pipeline = newPipeline(new AnonymousCredential(), options);
        }
        else if (credentialOrPipelineOrContainerName &&
            typeof credentialOrPipelineOrContainerName === "string" &&
            blobNameOrOptions &&
            typeof blobNameOrOptions === "string") {
            // (connectionString: string, containerName: string, blobName: string, options?: StoragePipelineOptions)
            const containerName = credentialOrPipelineOrContainerName;
            const blobName = blobNameOrOptions;
            const extractedCreds = utils_common_extractConnectionStringParts(urlOrConnectionString);
            if (extractedCreds.kind === "AccountConnString") {
                if (esm_isNodeLike) {
                    const sharedKeyCredential = new StorageSharedKeyCredential(extractedCreds.accountName, extractedCreds.accountKey);
                    url = utils_common_appendToURLPath(utils_common_appendToURLPath(extractedCreds.url, encodeURIComponent(containerName)), encodeURIComponent(blobName));
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
                    utils_common_appendToURLPath(utils_common_appendToURLPath(extractedCreds.url, encodeURIComponent(containerName)), encodeURIComponent(blobName)) +
                        "?" +
                        extractedCreds.accountSas;
                pipeline = newPipeline(new AnonymousCredential(), options);
            }
            else {
                throw new Error("Connection string must be either an Account connection string or a SAS connection string");
            }
        }
        else {
            throw new Error("Expecting non-empty strings for containerName and blobName parameters");
        }
        super(url, pipeline);
        ({ blobName: this._name, containerName: this._containerName } =
            this.getBlobAndContainerNamesFromUrl());
        this.blobContext = this.storageClientContext.blob;
        this._snapshot = utils_common_getURLParameter(this.url, utils_constants_URLConstants.Parameters.SNAPSHOT);
        this._versionId = utils_common_getURLParameter(this.url, utils_constants_URLConstants.Parameters.VERSIONID);
    }
    /**
     * Creates a new BlobClient object identical to the source but with the specified snapshot timestamp.
     * Provide "" will remove the snapshot and return a Client to the base blob.
     *
     * @param snapshot - The snapshot timestamp.
     * @returns A new BlobClient object identical to the source but with the specified snapshot timestamp
     */
    withSnapshot(snapshot) {
        return new BlobClient(utils_common_setURLParameter(this.url, utils_constants_URLConstants.Parameters.SNAPSHOT, snapshot.length === 0 ? undefined : snapshot), this.pipeline);
    }
    /**
     * Creates a new BlobClient object pointing to a version of this blob.
     * Provide "" will remove the versionId and return a Client to the base blob.
     *
     * @param versionId - The versionId.
     * @returns A new BlobClient object pointing to the version of this blob.
     */
    withVersion(versionId) {
        return new BlobClient(utils_common_setURLParameter(this.url, utils_constants_URLConstants.Parameters.VERSIONID, versionId.length === 0 ? undefined : versionId), this.pipeline);
    }
    /**
     * Creates a AppendBlobClient object.
     *
     */
    getAppendBlobClient() {
        return new AppendBlobClient(this.url, this.pipeline);
    }
    /**
     * Creates a BlockBlobClient object.
     *
     */
    getBlockBlobClient() {
        return new BlockBlobClient(this.url, this.pipeline);
    }
    /**
     * Creates a PageBlobClient object.
     *
     */
    getPageBlobClient() {
        return new PageBlobClient(this.url, this.pipeline);
    }
    /**
     * Reads or downloads a blob from the system, including its metadata and properties.
     * You can also call Get Blob to read a snapshot.
     *
     * * In Node.js, data returns in a Readable stream readableStreamBody
     * * In browsers, data returns in a promise blobBody
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/get-blob
     *
     * @param offset - From which position of the blob to download, greater than or equal to 0
     * @param count - How much data to be downloaded, greater than 0. Will download to the end when undefined
     * @param options - Optional options to Blob Download operation.
     *
     *
     * Example usage (Node.js):
     *
     * ```ts snippet:ReadmeSampleDownloadBlob_Node
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
     * const blobClient = containerClient.getBlobClient(blobName);
     *
     * // Get blob content from position 0 to the end
     * // In Node.js, get downloaded data by accessing downloadBlockBlobResponse.readableStreamBody
     * const downloadBlockBlobResponse = await blobClient.download();
     * if (downloadBlockBlobResponse.readableStreamBody) {
     *   const downloaded = await streamToString(downloadBlockBlobResponse.readableStreamBody);
     *   console.log(`Downloaded blob content: ${downloaded}`);
     * }
     *
     * async function streamToString(stream: NodeJS.ReadableStream): Promise<string> {
     *   const result = await new Promise<Buffer<ArrayBuffer>>((resolve, reject) => {
     *     const chunks: Buffer[] = [];
     *     stream.on("data", (data) => {
     *       chunks.push(Buffer.isBuffer(data) ? data : Buffer.from(data));
     *     });
     *     stream.on("end", () => {
     *       resolve(Buffer.concat(chunks));
     *     });
     *     stream.on("error", reject);
     *   });
     *   return result.toString();
     * }
     * ```
     *
     * Example usage (browser):
     *
     * ```ts snippet:ReadmeSampleDownloadBlob_Browser
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
     * const blobClient = containerClient.getBlobClient(blobName);
     *
     * // Get blob content from position 0 to the end
     * // In browsers, get downloaded data by accessing downloadBlockBlobResponse.blobBody
     * const downloadBlockBlobResponse = await blobClient.download();
     * const blobBody = await downloadBlockBlobResponse.blobBody;
     * if (blobBody) {
     *   const downloaded = await blobBody.text();
     *   console.log(`Downloaded blob content: ${downloaded}`);
     * }
     * ```
     */
    async download(offset = 0, count, options = {}) {
        options.conditions = options.conditions || {};
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("BlobClient-download", options, async (updatedOptions) => {
            const res = utils_common_assertResponse((await this.blobContext.download({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                requestOptions: {
                    onDownloadProgress: esm_isNodeLike ? undefined : options.onProgress, // for Node.js, progress is reported by RetriableReadableStream
                },
                range: offset === 0 && !count ? undefined : rangeToString({ offset, count }),
                rangeGetContentMD5: options.rangeGetContentMD5,
                rangeGetContentCRC64: options.rangeGetContentCrc64,
                snapshot: options.snapshot,
                cpkInfo: options.customerProvidedKey,
                tracingOptions: updatedOptions.tracingOptions,
            })));
            const wrappedRes = {
                ...res,
                _response: res._response, // _response is made non-enumerable
                objectReplicationDestinationPolicyId: res.objectReplicationPolicyId,
                objectReplicationSourceProperties: parseObjectReplicationRecord(res.objectReplicationRules),
            };
            // Return browser response immediately
            if (!esm_isNodeLike) {
                return wrappedRes;
            }
            // We support retrying when download stream unexpected ends in Node.js runtime
            // Following code shouldn't be bundled into browser build, however some
            // bundlers may try to bundle following code and "FileReadResponse.ts".
            // In this case, "FileDownloadResponse.browser.ts" will be used as a shim of "FileDownloadResponse.ts"
            // The config is in package.json "browser" field
            if (options.maxRetryRequests === undefined || options.maxRetryRequests < 0) {
                // TODO: Default value or make it a required parameter?
                options.maxRetryRequests = DEFAULT_MAX_DOWNLOAD_RETRY_REQUESTS;
            }
            if (res.contentLength === undefined) {
                throw new RangeError(`File download response doesn't contain valid content length header`);
            }
            if (!res.etag) {
                throw new RangeError(`File download response doesn't contain valid etag header`);
            }
            return new BlobDownloadResponse(wrappedRes, async (start) => {
                const updatedDownloadOptions = {
                    leaseAccessConditions: options.conditions,
                    modifiedAccessConditions: {
                        ifMatch: options.conditions.ifMatch || res.etag,
                        ifModifiedSince: options.conditions.ifModifiedSince,
                        ifNoneMatch: options.conditions.ifNoneMatch,
                        ifUnmodifiedSince: options.conditions.ifUnmodifiedSince,
                        ifTags: options.conditions?.tagConditions,
                    },
                    range: rangeToString({
                        count: offset + res.contentLength - start,
                        offset: start,
                    }),
                    rangeGetContentMD5: options.rangeGetContentMD5,
                    rangeGetContentCRC64: options.rangeGetContentCrc64,
                    snapshot: options.snapshot,
                    cpkInfo: options.customerProvidedKey,
                };
                // Debug purpose only
                // console.log(
                //   `Read from internal stream, range: ${
                //     updatedOptions.range
                //   }, options: ${JSON.stringify(updatedOptions)}`
                // );
                return (await this.blobContext.download({
                    abortSignal: options.abortSignal,
                    ...updatedDownloadOptions,
                })).readableStreamBody;
            }, offset, res.contentLength, {
                maxRetryRequests: options.maxRetryRequests,
                onProgress: options.onProgress,
            });
        });
    }
    /**
     * Returns true if the Azure blob resource represented by this client exists; false otherwise.
     *
     * NOTE: use this function with care since an existing blob might be deleted by other clients or
     * applications. Vice versa new blobs might be added by other clients or applications after this
     * function completes.
     *
     * @param options - options to Exists operation.
     */
    async exists(options = {}) {
        return tracingClient.withSpan("BlobClient-exists", options, async (updatedOptions) => {
            try {
                ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
                await this.getProperties({
                    abortSignal: options.abortSignal,
                    customerProvidedKey: options.customerProvidedKey,
                    conditions: options.conditions,
                    tracingOptions: updatedOptions.tracingOptions,
                });
                return true;
            }
            catch (e) {
                if (e.statusCode === 404) {
                    // Expected exception when checking blob existence
                    return false;
                }
                else if (e.statusCode === 409 &&
                    (e.details.errorCode === BlobUsesCustomerSpecifiedEncryptionMsg ||
                        e.details.errorCode === BlobDoesNotUseCustomerSpecifiedEncryption)) {
                    // Expected exception when checking blob existence
                    return true;
                }
                throw e;
            }
        });
    }
    /**
     * Returns all user-defined metadata, standard HTTP properties, and system properties
     * for the blob. It does not return the content of the blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-blob-properties
     *
     * WARNING: The `metadata` object returned in the response will have its keys in lowercase, even if
     * they originally contained uppercase characters. This differs from the metadata keys returned by
     * the methods of {@link ContainerClient} that list blobs using the `includeMetadata` option, which
     * will retain their original casing.
     *
     * @param options - Optional options to Get Properties operation.
     */
    async getProperties(options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("BlobClient-getProperties", options, async (updatedOptions) => {
            const res = utils_common_assertResponse(await this.blobContext.getProperties({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                cpkInfo: options.customerProvidedKey,
                tracingOptions: updatedOptions.tracingOptions,
            }));
            return {
                ...res,
                _response: res._response, // _response is made non-enumerable
                objectReplicationDestinationPolicyId: res.objectReplicationPolicyId,
                objectReplicationSourceProperties: parseObjectReplicationRecord(res.objectReplicationRules),
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
     * @param options - Optional options to Blob Delete operation.
     */
    async delete(options = {}) {
        options.conditions = options.conditions || {};
        return tracingClient.withSpan("BlobClient-delete", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.delete({
                abortSignal: options.abortSignal,
                deleteSnapshots: options.deleteSnapshots,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Marks the specified blob or snapshot for deletion if it exists. The blob is later deleted
     * during garbage collection. Note that in order to delete a blob, you must delete
     * all of its snapshots. You can delete both at the same time with the Delete
     * Blob operation.
     * @see https://learn.microsoft.com/rest/api/storageservices/delete-blob
     *
     * @param options - Optional options to Blob Delete operation.
     */
    async deleteIfExists(options = {}) {
        return tracingClient.withSpan("BlobClient-deleteIfExists", options, async (updatedOptions) => {
            try {
                const res = utils_common_assertResponse(await this.delete(updatedOptions));
                return {
                    succeeded: true,
                    ...res,
                    _response: res._response, // _response is made non-enumerable
                };
            }
            catch (e) {
                if (e.details?.errorCode === "BlobNotFound") {
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
     * Restores the contents and metadata of soft deleted blob and any associated
     * soft deleted snapshots. Undelete Blob is supported only on version 2017-07-29
     * or later.
     * @see https://learn.microsoft.com/rest/api/storageservices/undelete-blob
     *
     * @param options - Optional options to Blob Undelete operation.
     */
    async undelete(options = {}) {
        return tracingClient.withSpan("BlobClient-undelete", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.undelete({
                abortSignal: options.abortSignal,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Sets system properties on the blob.
     *
     * If no value provided, or no value provided for the specified blob HTTP headers,
     * these blob HTTP headers without a value will be cleared.
     * @see https://learn.microsoft.com/rest/api/storageservices/set-blob-properties
     *
     * @param blobHTTPHeaders - If no value provided, or no value provided for
     *                                                   the specified blob HTTP headers, these blob HTTP
     *                                                   headers without a value will be cleared.
     *                                                   A common header to set is `blobContentType`
     *                                                   enabling the browser to provide functionality
     *                                                   based on file type.
     * @param options - Optional options to Blob Set HTTP Headers operation.
     */
    async setHTTPHeaders(blobHTTPHeaders, options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("BlobClient-setHTTPHeaders", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.setHttpHeaders({
                abortSignal: options.abortSignal,
                blobHttpHeaders: blobHTTPHeaders,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                // cpkInfo: options.customerProvidedKey, // CPK is not included in Swagger, should change this back when this issue is fixed in Swagger.
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Sets user-defined metadata for the specified blob as one or more name-value pairs.
     *
     * If no option provided, or no metadata defined in the parameter, the blob
     * metadata will be removed.
     * @see https://learn.microsoft.com/rest/api/storageservices/set-blob-metadata
     *
     * @param metadata - Replace existing metadata with this value.
     *                               If no value provided the existing metadata will be removed.
     * @param options - Optional options to Set Metadata operation.
     */
    async setMetadata(metadata, options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("BlobClient-setMetadata", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.setMetadata({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                metadata,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Sets tags on the underlying blob.
     * A blob can have up to 10 tags. Tag keys must be between 1 and 128 characters.  Tag values must be between 0 and 256 characters.
     * Valid tag key and value characters include lower and upper case letters, digits (0-9),
     * space (' '), plus ('+'), minus ('-'), period ('.'), foward slash ('/'), colon (':'), equals ('='), and underscore ('_').
     *
     * @param tags -
     * @param options -
     */
    async setTags(tags, options = {}) {
        return tracingClient.withSpan("BlobClient-setTags", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.setTags({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                blobModifiedAccessConditions: options.conditions,
                tracingOptions: updatedOptions.tracingOptions,
                tags: toBlobTags(tags),
            }));
        });
    }
    /**
     * Gets the tags associated with the underlying blob.
     *
     * @param options -
     */
    async getTags(options = {}) {
        return tracingClient.withSpan("BlobClient-getTags", options, async (updatedOptions) => {
            const response = utils_common_assertResponse(await this.blobContext.getTags({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                blobModifiedAccessConditions: options.conditions,
                tracingOptions: updatedOptions.tracingOptions,
            }));
            const wrappedResponse = {
                ...response,
                _response: response._response, // _response is made non-enumerable
                tags: toTags({ blobTagSet: response.blobTagSet }) || {},
            };
            return wrappedResponse;
        });
    }
    /**
     * Get a {@link BlobLeaseClient} that manages leases on the blob.
     *
     * @param proposeLeaseId - Initial proposed lease Id.
     * @returns A new BlobLeaseClient object for managing leases on the blob.
     */
    getBlobLeaseClient(proposeLeaseId) {
        return new BlobLeaseClient(this, proposeLeaseId);
    }
    /**
     * Creates a read-only snapshot of a blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/snapshot-blob
     *
     * @param options - Optional options to the Blob Create Snapshot operation.
     */
    async createSnapshot(options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("BlobClient-createSnapshot", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.createSnapshot({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                metadata: options.metadata,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Asynchronously copies a blob to a destination within the storage account.
     * This method returns a long running operation poller that allows you to wait
     * indefinitely until the copy is completed.
     * You can also cancel a copy before it is completed by calling `cancelOperation` on the poller.
     * Note that the onProgress callback will not be invoked if the operation completes in the first
     * request, and attempting to cancel a completed copy will result in an error being thrown.
     *
     * In version 2012-02-12 and later, the source for a Copy Blob operation can be
     * a committed blob in any Azure storage account.
     * Beginning with version 2015-02-21, the source for a Copy Blob operation can be
     * an Azure file in any Azure storage account.
     * Only storage accounts created on or after June 7th, 2012 allow the Copy Blob
     * operation to copy from another storage account.
     * @see https://learn.microsoft.com/rest/api/storageservices/copy-blob
     *
     * ```ts snippet:ClientsBeginCopyFromURL
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
     * const blobClient = containerClient.getBlobClient(blobName);
     *
     * // Example using automatic polling
     * const automaticCopyPoller = await blobClient.beginCopyFromURL("url");
     * const automaticResult = await automaticCopyPoller.pollUntilDone();
     *
     * // Example using manual polling
     * const manualCopyPoller = await blobClient.beginCopyFromURL("url");
     * while (!manualCopyPoller.isDone()) {
     *   await manualCopyPoller.poll();
     * }
     * const manualResult = manualCopyPoller.getResult();
     *
     * // Example using progress updates
     * const progressUpdatesCopyPoller = await blobClient.beginCopyFromURL("url", {
     *   onProgress(state) {
     *     console.log(`Progress: ${state.copyProgress}`);
     *   },
     * });
     * const progressUpdatesResult = await progressUpdatesCopyPoller.pollUntilDone();
     *
     * // Example using a changing polling interval (default 15 seconds)
     * const pollingIntervalCopyPoller = await blobClient.beginCopyFromURL("url", {
     *   intervalInMs: 1000, // poll blob every 1 second for copy progress
     * });
     * const pollingIntervalResult = await pollingIntervalCopyPoller.pollUntilDone();
     *
     * // Example using copy cancellation:
     * const cancelCopyPoller = await blobClient.beginCopyFromURL("url");
     * // cancel operation after starting it.
     * try {
     *   await cancelCopyPoller.cancelOperation();
     *   // calls to get the result now throw PollerCancelledError
     *   cancelCopyPoller.getResult();
     * } catch (err: any) {
     *   if (err.name === "PollerCancelledError") {
     *     console.log("The copy was cancelled.");
     *   }
     * }
     * ```
     *
     * @param copySource - url to the source Azure Blob/File.
     * @param options - Optional options to the Blob Start Copy From URL operation.
     */
    async beginCopyFromURL(copySource, options = {}) {
        const client = {
            abortCopyFromURL: (...args) => this.abortCopyFromURL(...args),
            getProperties: (...args) => this.getProperties(...args),
            startCopyFromURL: (...args) => this.startCopyFromURL(...args),
        };
        const poller = new BlobBeginCopyFromUrlPoller({
            blobClient: client,
            copySource,
            intervalInMs: options.intervalInMs,
            onProgress: options.onProgress,
            resumeFrom: options.resumeFrom,
            startCopyFromURLOptions: options,
        });
        // Trigger the startCopyFromURL call by calling poll.
        // Any errors from this method should be surfaced to the user.
        await poller.poll();
        return poller;
    }
    /**
     * Aborts a pending asynchronous Copy Blob operation, and leaves a destination blob with zero
     * length and full metadata. Version 2012-02-12 and newer.
     * @see https://learn.microsoft.com/rest/api/storageservices/abort-copy-blob
     *
     * @param copyId - Id of the Copy From URL operation.
     * @param options - Optional options to the Blob Abort Copy From URL operation.
     */
    async abortCopyFromURL(copyId, options = {}) {
        return tracingClient.withSpan("BlobClient-abortCopyFromURL", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.abortCopyFromURL(copyId, {
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * The synchronous Copy From URL operation copies a blob or an internet resource to a new blob. It will not
     * return a response until the copy is complete.
     * @see https://learn.microsoft.com/rest/api/storageservices/copy-blob-from-url
     *
     * @param copySource - The source URL to copy from, Shared Access Signature(SAS) maybe needed for authentication
     * @param options -
     */
    async syncCopyFromURL(copySource, options = {}) {
        options.conditions = options.conditions || {};
        options.sourceConditions = options.sourceConditions || {};
        return tracingClient.withSpan("BlobClient-syncCopyFromURL", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.copyFromURL(copySource, {
                abortSignal: options.abortSignal,
                metadata: options.metadata,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                sourceModifiedAccessConditions: {
                    sourceIfMatch: options.sourceConditions?.ifMatch,
                    sourceIfModifiedSince: options.sourceConditions?.ifModifiedSince,
                    sourceIfNoneMatch: options.sourceConditions?.ifNoneMatch,
                    sourceIfUnmodifiedSince: options.sourceConditions?.ifUnmodifiedSince,
                },
                sourceContentMD5: options.sourceContentMD5,
                copySourceAuthorization: utils_common_httpAuthorizationToString(options.sourceAuthorization),
                tier: toAccessTier(options.tier),
                blobTagsString: toBlobTagsString(options.tags),
                immutabilityPolicyExpiry: options.immutabilityPolicy?.expiriesOn,
                immutabilityPolicyMode: options.immutabilityPolicy?.policyMode,
                legalHold: options.legalHold,
                encryptionScope: options.encryptionScope,
                copySourceTags: options.copySourceTags,
                fileRequestIntent: options.sourceShareTokenIntent,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Sets the tier on a blob. The operation is allowed on a page blob in a premium
     * storage account and on a block blob in a blob storage account (locally redundant
     * storage only). A premium page blob's tier determines the allowed size, IOPS,
     * and bandwidth of the blob. A block blob's tier determines Hot/Cool/Archive
     * storage type. This operation does not update the blob's ETag.
     * @see https://learn.microsoft.com/rest/api/storageservices/set-blob-tier
     *
     * @param tier - The tier to be set on the blob. Valid values are Hot, Cool, or Archive.
     * @param options - Optional options to the Blob Set Tier operation.
     */
    async setAccessTier(tier, options = {}) {
        return tracingClient.withSpan("BlobClient-setAccessTier", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.setTier(toAccessTier(tier), {
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                rehydratePriority: options.rehydratePriority,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    async downloadToBuffer(param1, param2, param3, param4 = {}) {
        let buffer;
        let offset = 0;
        let count = 0;
        let options = param4;
        if (param1 instanceof Buffer) {
            buffer = param1;
            offset = param2 || 0;
            count = typeof param3 === "number" ? param3 : 0;
        }
        else {
            offset = typeof param1 === "number" ? param1 : 0;
            count = typeof param2 === "number" ? param2 : 0;
            options = param3 || {};
        }
        let blockSize = options.blockSize ?? 0;
        if (blockSize < 0) {
            throw new RangeError("blockSize option must be >= 0");
        }
        if (blockSize === 0) {
            blockSize = DEFAULT_BLOB_DOWNLOAD_BLOCK_BYTES;
        }
        if (offset < 0) {
            throw new RangeError("offset option must be >= 0");
        }
        if (count && count <= 0) {
            throw new RangeError("count option must be greater than 0");
        }
        if (!options.conditions) {
            options.conditions = {};
        }
        return tracingClient.withSpan("BlobClient-downloadToBuffer", options, async (updatedOptions) => {
            // Customer doesn't specify length, get it
            if (!count) {
                const response = await this.getProperties({
                    ...options,
                    tracingOptions: updatedOptions.tracingOptions,
                });
                count = response.contentLength - offset;
                if (count < 0) {
                    throw new RangeError(`offset ${offset} shouldn't be larger than blob size ${response.contentLength}`);
                }
            }
            // Allocate the buffer of size = count if the buffer is not provided
            if (!buffer) {
                try {
                    buffer = Buffer.alloc(count);
                }
                catch (error) {
                    throw new Error(`Unable to allocate the buffer of size: ${count}(in bytes). Please try passing your own buffer to the "downloadToBuffer" method or try using other methods like "download" or "downloadToFile".\t ${error.message}`);
                }
            }
            if (buffer.length < count) {
                throw new RangeError(`The buffer's size should be equal to or larger than the request count of bytes: ${count}`);
            }
            let transferProgress = 0;
            const batch = new Batch(options.concurrency);
            for (let off = offset; off < offset + count; off = off + blockSize) {
                batch.addOperation(async () => {
                    // Exclusive chunk end position
                    let chunkEnd = offset + count;
                    if (off + blockSize < chunkEnd) {
                        chunkEnd = off + blockSize;
                    }
                    const response = await this.download(off, chunkEnd - off, {
                        abortSignal: options.abortSignal,
                        conditions: options.conditions,
                        maxRetryRequests: options.maxRetryRequestsPerBlock,
                        customerProvidedKey: options.customerProvidedKey,
                        tracingOptions: updatedOptions.tracingOptions,
                    });
                    const stream = response.readableStreamBody;
                    await streamToBuffer(stream, buffer, off - offset, chunkEnd - offset);
                    // Update progress after block is downloaded, in case of block trying
                    // Could provide finer grained progress updating inside HTTP requests,
                    // only if convenience layer download try is enabled
                    transferProgress += chunkEnd - off;
                    if (options.onProgress) {
                        options.onProgress({ loadedBytes: transferProgress });
                    }
                });
            }
            await batch.do();
            return buffer;
        });
    }
    /**
     * ONLY AVAILABLE IN NODE.JS RUNTIME.
     *
     * Downloads an Azure Blob to a local file.
     * Fails if the the given file path already exits.
     * Offset and count are optional, pass 0 and undefined respectively to download the entire blob.
     *
     * @param filePath -
     * @param offset - From which position of the block blob to download.
     * @param count - How much data to be downloaded. Will download to the end when passing undefined.
     * @param options - Options to Blob download options.
     * @returns The response data for blob download operation,
     *                                                 but with readableStreamBody set to undefined since its
     *                                                 content is already read and written into a local file
     *                                                 at the specified path.
     */
    async downloadToFile(filePath, offset = 0, count, options = {}) {
        return tracingClient.withSpan("BlobClient-downloadToFile", options, async (updatedOptions) => {
            const response = await this.download(offset, count, {
                ...options,
                tracingOptions: updatedOptions.tracingOptions,
            });
            if (response.readableStreamBody) {
                await readStreamToLocalFile(response.readableStreamBody, filePath);
            }
            // The stream is no longer accessible so setting it to undefined.
            response.blobDownloadStream = undefined;
            return response;
        });
    }
    getBlobAndContainerNamesFromUrl() {
        let containerName;
        let blobName;
        try {
            //  URL may look like the following
            // "https://myaccount.blob.core.windows.net/mycontainer/blob?sasString";
            // "https://myaccount.blob.core.windows.net/mycontainer/blob";
            // "https://myaccount.blob.core.windows.net/mycontainer/blob/a.txt?sasString";
            // "https://myaccount.blob.core.windows.net/mycontainer/blob/a.txt";
            // IPv4/IPv6 address hosts, Endpoints - `http://127.0.0.1:10000/devstoreaccount1/containername/blob`
            // http://localhost:10001/devstoreaccount1/containername/blob
            const parsedUrl = new URL(this.url);
            if (parsedUrl.host.split(".")[1] === "blob") {
                // "https://myaccount.blob.core.windows.net/containername/blob".
                // .getPath() -> /containername/blob
                const pathComponents = parsedUrl.pathname.match("/([^/]*)(/(.*))?");
                containerName = pathComponents[1];
                blobName = pathComponents[3];
            }
            else if (utils_common_isIpEndpointStyle(parsedUrl)) {
                // IPv4/IPv6 address hosts... Example - http://192.0.0.10:10001/devstoreaccount1/containername/blob
                // Single word domain without a [dot] in the endpoint... Example - http://localhost:10001/devstoreaccount1/containername/blob
                // .getPath() -> /devstoreaccount1/containername/blob
                const pathComponents = parsedUrl.pathname.match("/([^/]*)/([^/]*)(/(.*))?");
                containerName = pathComponents[2];
                blobName = pathComponents[4];
            }
            else {
                // "https://customdomain.com/containername/blob".
                // .getPath() -> /containername/blob
                const pathComponents = parsedUrl.pathname.match("/([^/]*)(/(.*))?");
                containerName = pathComponents[1];
                blobName = pathComponents[3];
            }
            // decode the encoded blobName, containerName - to get all the special characters that might be present in them
            containerName = decodeURIComponent(containerName);
            blobName = decodeURIComponent(blobName);
            // Azure Storage Server will replace "\" with "/" in the blob names
            //   doing the same in the SDK side so that the user doesn't have to replace "\" instances in the blobName
            blobName = blobName.replace(/\\/g, "/");
            if (!containerName) {
                throw new Error("Provided containerName is invalid.");
            }
            return { blobName, containerName };
        }
        catch (error) {
            throw new Error("Unable to extract blobName and containerName with provided information.");
        }
    }
    /**
     * Asynchronously copies a blob to a destination within the storage account.
     * In version 2012-02-12 and later, the source for a Copy Blob operation can be
     * a committed blob in any Azure storage account.
     * Beginning with version 2015-02-21, the source for a Copy Blob operation can be
     * an Azure file in any Azure storage account.
     * Only storage accounts created on or after June 7th, 2012 allow the Copy Blob
     * operation to copy from another storage account.
     * @see https://learn.microsoft.com/rest/api/storageservices/copy-blob
     *
     * @param copySource - url to the source Azure Blob/File.
     * @param options - Optional options to the Blob Start Copy From URL operation.
     */
    async startCopyFromURL(copySource, options = {}) {
        return tracingClient.withSpan("BlobClient-startCopyFromURL", options, async (updatedOptions) => {
            options.conditions = options.conditions || {};
            options.sourceConditions = options.sourceConditions || {};
            return utils_common_assertResponse(await this.blobContext.startCopyFromURL(copySource, {
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                metadata: options.metadata,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                sourceModifiedAccessConditions: {
                    sourceIfMatch: options.sourceConditions.ifMatch,
                    sourceIfModifiedSince: options.sourceConditions.ifModifiedSince,
                    sourceIfNoneMatch: options.sourceConditions.ifNoneMatch,
                    sourceIfUnmodifiedSince: options.sourceConditions.ifUnmodifiedSince,
                    sourceIfTags: options.sourceConditions.tagConditions,
                },
                immutabilityPolicyExpiry: options.immutabilityPolicy?.expiriesOn,
                immutabilityPolicyMode: options.immutabilityPolicy?.policyMode,
                legalHold: options.legalHold,
                rehydratePriority: options.rehydratePriority,
                tier: toAccessTier(options.tier),
                blobTagsString: toBlobTagsString(options.tags),
                sealBlob: options.sealBlob,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Only available for BlobClient constructed with a shared key credential.
     *
     * Generates a Blob Service Shared Access Signature (SAS) URI based on the client properties
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
                blobName: this._name,
                snapshotTime: this._snapshot,
                versionId: this._versionId,
                ...options,
            }, this.credential).toString();
            resolve(utils_common_appendToURLQuery(this.url, sas));
        });
    }
    /**
     * Only available for BlobClient constructed with a shared key credential.
     *
     * Generates string to sign for a Blob Service Shared Access Signature (SAS) URI based on
     * the client properties and parameters passed in. The SAS is signed by the shared key credential of the client.
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
            blobName: this._name,
            snapshotTime: this._snapshot,
            versionId: this._versionId,
            ...options,
        }, this.credential).stringToSign;
    }
    /**
     *
     * Generates a Blob Service Shared Access Signature (SAS) URI based on
     * the client properties and parameters passed in. The SAS is signed by the input user delegation key.
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
                blobName: this._name,
                snapshotTime: this._snapshot,
                versionId: this._versionId,
                ...options,
            }, userDelegationKey, this.accountName).toString();
            resolve(utils_common_appendToURLQuery(this.url, sas));
        });
    }
    /**
     * Only available for BlobClient constructed with a shared key credential.
     *
     * Generates string to sign for a Blob Service Shared Access Signature (SAS) URI based on
     * the client properties and parameters passed in. The SAS is signed by the input user delegation key.
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
            blobName: this._name,
            snapshotTime: this._snapshot,
            versionId: this._versionId,
            ...options,
        }, userDelegationKey, this.accountName).stringToSign;
    }
    /**
     * Delete the immutablility policy on the blob.
     *
     * @param options - Optional options to delete immutability policy on the blob.
     */
    async deleteImmutabilityPolicy(options = {}) {
        return tracingClient.withSpan("BlobClient-deleteImmutabilityPolicy", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.deleteImmutabilityPolicy({
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Set immutability policy on the blob.
     *
     * @param options - Optional options to set immutability policy on the blob.
     */
    async setImmutabilityPolicy(immutabilityPolicy, options = {}) {
        return tracingClient.withSpan("BlobClient-setImmutabilityPolicy", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.setImmutabilityPolicy({
                immutabilityPolicyExpiry: immutabilityPolicy.expiriesOn,
                immutabilityPolicyMode: immutabilityPolicy.policyMode,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Set legal hold on the blob.
     *
     * @param options - Optional options to set legal hold on the blob.
     */
    async setLegalHold(legalHoldEnabled, options = {}) {
        return tracingClient.withSpan("BlobClient-setLegalHold", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.setLegalHold(legalHoldEnabled, {
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
        return tracingClient.withSpan("BlobClient-getAccountInfo", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blobContext.getAccountInfo({
                abortSignal: options.abortSignal,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
}
/**
 * AppendBlobClient defines a set of operations applicable to append blobs.
 */
class AppendBlobClient extends BlobClient {
    /**
     * appendBlobsContext provided by protocol layer.
     */
    appendBlobContext;
    constructor(urlOrConnectionString, credentialOrPipelineOrContainerName, blobNameOrOptions, 
    // Legacy, no fix for eslint error without breaking. Disable it for this interface.
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    options) {
        // In TypeScript we cannot simply pass all parameters to super() like below so have to duplicate the code instead.
        //   super(s, credentialOrPipelineOrContainerNameOrOptions, blobNameOrOptions, options);
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
            // (url: string, credential?: StorageSharedKeyCredential | AnonymousCredential | TokenCredential, options?: StoragePipelineOptions)      url = urlOrConnectionString;
            url = urlOrConnectionString;
            options = blobNameOrOptions;
            pipeline = newPipeline(credentialOrPipelineOrContainerName, options);
        }
        else if (!credentialOrPipelineOrContainerName &&
            typeof credentialOrPipelineOrContainerName !== "string") {
            // (url: string, credential?: StorageSharedKeyCredential | AnonymousCredential | TokenCredential, options?: StoragePipelineOptions)
            url = urlOrConnectionString;
            // The second parameter is undefined. Use anonymous credential.
            pipeline = newPipeline(new AnonymousCredential(), options);
        }
        else if (credentialOrPipelineOrContainerName &&
            typeof credentialOrPipelineOrContainerName === "string" &&
            blobNameOrOptions &&
            typeof blobNameOrOptions === "string") {
            // (connectionString: string, containerName: string, blobName: string, options?: StoragePipelineOptions)
            const containerName = credentialOrPipelineOrContainerName;
            const blobName = blobNameOrOptions;
            const extractedCreds = utils_common_extractConnectionStringParts(urlOrConnectionString);
            if (extractedCreds.kind === "AccountConnString") {
                if (esm_isNodeLike) {
                    const sharedKeyCredential = new StorageSharedKeyCredential(extractedCreds.accountName, extractedCreds.accountKey);
                    url = utils_common_appendToURLPath(utils_common_appendToURLPath(extractedCreds.url, encodeURIComponent(containerName)), encodeURIComponent(blobName));
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
                    utils_common_appendToURLPath(utils_common_appendToURLPath(extractedCreds.url, encodeURIComponent(containerName)), encodeURIComponent(blobName)) +
                        "?" +
                        extractedCreds.accountSas;
                pipeline = newPipeline(new AnonymousCredential(), options);
            }
            else {
                throw new Error("Connection string must be either an Account connection string or a SAS connection string");
            }
        }
        else {
            throw new Error("Expecting non-empty strings for containerName and blobName parameters");
        }
        super(url, pipeline);
        this.appendBlobContext = this.storageClientContext.appendBlob;
    }
    /**
     * Creates a new AppendBlobClient object identical to the source but with the
     * specified snapshot timestamp.
     * Provide "" will remove the snapshot and return a Client to the base blob.
     *
     * @param snapshot - The snapshot timestamp.
     * @returns A new AppendBlobClient object identical to the source but with the specified snapshot timestamp.
     */
    withSnapshot(snapshot) {
        return new AppendBlobClient(utils_common_setURLParameter(this.url, utils_constants_URLConstants.Parameters.SNAPSHOT, snapshot.length === 0 ? undefined : snapshot), this.pipeline);
    }
    /**
     * Creates a 0-length append blob. Call AppendBlock to append data to an append blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/put-blob
     *
     * @param options - Options to the Append Block Create operation.
     *
     *
     * Example usage:
     *
     * ```ts snippet:ClientsCreateAppendBlob
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
     *
     * const appendBlobClient = containerClient.getAppendBlobClient(blobName);
     * await appendBlobClient.create();
     * ```
     */
    async create(options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("AppendBlobClient-create", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.appendBlobContext.create(0, {
                abortSignal: options.abortSignal,
                blobHttpHeaders: options.blobHTTPHeaders,
                leaseAccessConditions: options.conditions,
                metadata: options.metadata,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                immutabilityPolicyExpiry: options.immutabilityPolicy?.expiriesOn,
                immutabilityPolicyMode: options.immutabilityPolicy?.policyMode,
                legalHold: options.legalHold,
                blobTagsString: toBlobTagsString(options.tags),
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Creates a 0-length append blob. Call AppendBlock to append data to an append blob.
     * If the blob with the same name already exists, the content of the existing blob will remain unchanged.
     * @see https://learn.microsoft.com/rest/api/storageservices/put-blob
     *
     * @param options -
     */
    async createIfNotExists(options = {}) {
        const conditions = { ifNoneMatch: ETagAny };
        return tracingClient.withSpan("AppendBlobClient-createIfNotExists", options, async (updatedOptions) => {
            try {
                const res = utils_common_assertResponse(await this.create({
                    ...updatedOptions,
                    conditions,
                }));
                return {
                    succeeded: true,
                    ...res,
                    _response: res._response, // _response is made non-enumerable
                };
            }
            catch (e) {
                if (e.details?.errorCode === "BlobAlreadyExists") {
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
     * Seals the append blob, making it read only.
     *
     * @param options -
     */
    async seal(options = {}) {
        options.conditions = options.conditions || {};
        return tracingClient.withSpan("AppendBlobClient-seal", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.appendBlobContext.seal({
                abortSignal: options.abortSignal,
                appendPositionAccessConditions: options.conditions,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Commits a new block of data to the end of the existing append blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/append-block
     *
     * @param body - Data to be appended.
     * @param contentLength - Length of the body in bytes.
     * @param options - Options to the Append Block operation.
     *
     *
     * Example usage:
     *
     * ```ts snippet:ClientsAppendBlock
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
     *
     * const content = "Hello World!";
     *
     * // Create a new append blob and append data to the blob.
     * const newAppendBlobClient = containerClient.getAppendBlobClient(blobName);
     * await newAppendBlobClient.create();
     * await newAppendBlobClient.appendBlock(content, content.length);
     *
     * // Append data to an existing append blob.
     * const existingAppendBlobClient = containerClient.getAppendBlobClient(blobName);
     * await existingAppendBlobClient.appendBlock(content, content.length);
     * ```
     */
    async appendBlock(body, contentLength, options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("AppendBlobClient-appendBlock", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.appendBlobContext.appendBlock(contentLength, body, {
                abortSignal: options.abortSignal,
                appendPositionAccessConditions: options.conditions,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                requestOptions: {
                    onUploadProgress: options.onProgress,
                },
                transactionalContentMD5: options.transactionalContentMD5,
                transactionalContentCrc64: options.transactionalContentCrc64,
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * The Append Block operation commits a new block of data to the end of an existing append blob
     * where the contents are read from a source url.
     * @see https://learn.microsoft.com/rest/api/storageservices/append-block-from-url
     *
     * @param sourceURL -
     *                 The url to the blob that will be the source of the copy. A source blob in the same storage account can
     *                 be authenticated via Shared Key. However, if the source is a blob in another account, the source blob
     *                 must either be public or must be authenticated via a shared access signature. If the source blob is
     *                 public, no authentication is required to perform the operation.
     * @param sourceOffset - Offset in source to be appended
     * @param count - Number of bytes to be appended as a block
     * @param options -
     */
    async appendBlockFromURL(sourceURL, sourceOffset, count, options = {}) {
        options.conditions = options.conditions || {};
        options.sourceConditions = options.sourceConditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("AppendBlobClient-appendBlockFromURL", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.appendBlobContext.appendBlockFromUrl(sourceURL, 0, {
                abortSignal: options.abortSignal,
                sourceRange: rangeToString({ offset: sourceOffset, count }),
                sourceContentMD5: options.sourceContentMD5,
                sourceContentCrc64: options.sourceContentCrc64,
                leaseAccessConditions: options.conditions,
                appendPositionAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                sourceModifiedAccessConditions: {
                    sourceIfMatch: options.sourceConditions?.ifMatch,
                    sourceIfModifiedSince: options.sourceConditions?.ifModifiedSince,
                    sourceIfNoneMatch: options.sourceConditions?.ifNoneMatch,
                    sourceIfUnmodifiedSince: options.sourceConditions?.ifUnmodifiedSince,
                },
                copySourceAuthorization: utils_common_httpAuthorizationToString(options.sourceAuthorization),
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                fileRequestIntent: options.sourceShareTokenIntent,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
}
/**
 * BlockBlobClient defines a set of operations applicable to block blobs.
 */
class BlockBlobClient extends BlobClient {
    /**
     * blobContext provided by protocol layer.
     *
     * Note. Ideally BlobClient should set BlobClient.blobContext to protected. However, API
     * extractor has issue blocking that. Here we redecelare _blobContext in BlockBlobClient.
     */
    _blobContext;
    /**
     * blockBlobContext provided by protocol layer.
     */
    blockBlobContext;
    constructor(urlOrConnectionString, credentialOrPipelineOrContainerName, blobNameOrOptions, 
    // Legacy, no fix for eslint error without breaking. Disable it for this interface.
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    options) {
        // In TypeScript we cannot simply pass all parameters to super() like below so have to duplicate the code instead.
        //   super(s, credentialOrPipelineOrContainerNameOrOptions, blobNameOrOptions, options);
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
            options = blobNameOrOptions;
            pipeline = newPipeline(credentialOrPipelineOrContainerName, options);
        }
        else if (!credentialOrPipelineOrContainerName &&
            typeof credentialOrPipelineOrContainerName !== "string") {
            // (url: string, credential?: StorageSharedKeyCredential | AnonymousCredential | TokenCredential, options?: StoragePipelineOptions)
            // The second parameter is undefined. Use anonymous credential.
            url = urlOrConnectionString;
            if (blobNameOrOptions && typeof blobNameOrOptions !== "string") {
                options = blobNameOrOptions;
            }
            pipeline = newPipeline(new AnonymousCredential(), options);
        }
        else if (credentialOrPipelineOrContainerName &&
            typeof credentialOrPipelineOrContainerName === "string" &&
            blobNameOrOptions &&
            typeof blobNameOrOptions === "string") {
            // (connectionString: string, containerName: string, blobName: string, options?: StoragePipelineOptions)
            const containerName = credentialOrPipelineOrContainerName;
            const blobName = blobNameOrOptions;
            const extractedCreds = utils_common_extractConnectionStringParts(urlOrConnectionString);
            if (extractedCreds.kind === "AccountConnString") {
                if (esm_isNodeLike) {
                    const sharedKeyCredential = new StorageSharedKeyCredential(extractedCreds.accountName, extractedCreds.accountKey);
                    url = utils_common_appendToURLPath(utils_common_appendToURLPath(extractedCreds.url, encodeURIComponent(containerName)), encodeURIComponent(blobName));
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
                    utils_common_appendToURLPath(utils_common_appendToURLPath(extractedCreds.url, encodeURIComponent(containerName)), encodeURIComponent(blobName)) +
                        "?" +
                        extractedCreds.accountSas;
                pipeline = newPipeline(new AnonymousCredential(), options);
            }
            else {
                throw new Error("Connection string must be either an Account connection string or a SAS connection string");
            }
        }
        else {
            throw new Error("Expecting non-empty strings for containerName and blobName parameters");
        }
        super(url, pipeline);
        this.blockBlobContext = this.storageClientContext.blockBlob;
        this._blobContext = this.storageClientContext.blob;
    }
    /**
     * Creates a new BlockBlobClient object identical to the source but with the
     * specified snapshot timestamp.
     * Provide "" will remove the snapshot and return a URL to the base blob.
     *
     * @param snapshot - The snapshot timestamp.
     * @returns A new BlockBlobClient object identical to the source but with the specified snapshot timestamp.
     */
    withSnapshot(snapshot) {
        return new BlockBlobClient(utils_common_setURLParameter(this.url, utils_constants_URLConstants.Parameters.SNAPSHOT, snapshot.length === 0 ? undefined : snapshot), this.pipeline);
    }
    /**
     * ONLY AVAILABLE IN NODE.JS RUNTIME.
     *
     * Quick query for a JSON or CSV formatted blob.
     *
     * Example usage (Node.js):
     *
     * ```ts snippet:ClientsQuery
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
     * // Query and convert a blob to a string
     * const queryBlockBlobResponse = await blockBlobClient.query("select from BlobStorage");
     * if (queryBlockBlobResponse.readableStreamBody) {
     *   const downloadedBuffer = await streamToBuffer(queryBlockBlobResponse.readableStreamBody);
     *   const downloaded = downloadedBuffer.toString();
     *   console.log(`Query blob content: ${downloaded}`);
     * }
     *
     * async function streamToBuffer(readableStream: NodeJS.ReadableStream): Promise<Buffer> {
     *   return new Promise((resolve, reject) => {
     *     const chunks: Buffer[] = [];
     *     readableStream.on("data", (data) => {
     *       chunks.push(data instanceof Buffer ? data : Buffer.from(data));
     *     });
     *     readableStream.on("end", () => {
     *       resolve(Buffer.concat(chunks));
     *     });
     *     readableStream.on("error", reject);
     *   });
     * }
     * ```
     *
     * @param query -
     * @param options -
     */
    async query(query, options = {}) {
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        if (!esm_isNodeLike) {
            throw new Error("This operation currently is only supported in Node.js.");
        }
        return tracingClient.withSpan("BlockBlobClient-query", options, async (updatedOptions) => {
            const response = utils_common_assertResponse((await this._blobContext.query({
                abortSignal: options.abortSignal,
                queryRequest: {
                    queryType: "SQL",
                    expression: query,
                    inputSerialization: toQuerySerialization(options.inputTextConfiguration),
                    outputSerialization: toQuerySerialization(options.outputTextConfiguration),
                },
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                cpkInfo: options.customerProvidedKey,
                tracingOptions: updatedOptions.tracingOptions,
            })));
            return new BlobQueryResponse(response, {
                abortSignal: options.abortSignal,
                onProgress: options.onProgress,
                onError: options.onError,
            });
        });
    }
    /**
     * Creates a new block blob, or updates the content of an existing block blob.
     * Updating an existing block blob overwrites any existing metadata on the blob.
     * Partial updates are not supported; the content of the existing blob is
     * overwritten with the new content. To perform a partial update of a block blob's,
     * use {@link stageBlock} and {@link commitBlockList}.
     *
     * This is a non-parallel uploading method, please use {@link uploadFile},
     * {@link uploadStream} or {@link uploadBrowserData} for better performance
     * with concurrency uploading.
     *
     * @see https://learn.microsoft.com/rest/api/storageservices/put-blob
     *
     * @param body - Blob, string, ArrayBuffer, ArrayBufferView or a function
     *                               which returns a new Readable stream whose offset is from data source beginning.
     * @param contentLength - Length of body in bytes. Use Buffer.byteLength() to calculate body length for a
     *                               string including non non-Base64/Hex-encoded characters.
     * @param options - Options to the Block Blob Upload operation.
     * @returns Response data for the Block Blob Upload operation.
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
    async upload(body, contentLength, options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("BlockBlobClient-upload", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blockBlobContext.upload(contentLength, body, {
                abortSignal: options.abortSignal,
                blobHttpHeaders: options.blobHTTPHeaders,
                leaseAccessConditions: options.conditions,
                metadata: options.metadata,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                requestOptions: {
                    onUploadProgress: options.onProgress,
                },
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                immutabilityPolicyExpiry: options.immutabilityPolicy?.expiriesOn,
                immutabilityPolicyMode: options.immutabilityPolicy?.policyMode,
                legalHold: options.legalHold,
                tier: toAccessTier(options.tier),
                blobTagsString: toBlobTagsString(options.tags),
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Creates a new Block Blob where the contents of the blob are read from a given URL.
     * This API is supported beginning with the 2020-04-08 version. Partial updates
     * are not supported with Put Blob from URL; the content of an existing blob is overwritten with
     * the content of the new blob.  To perform partial updates to a block blob’s contents using a
     * source URL, use {@link stageBlockFromURL} and {@link commitBlockList}.
     *
     * @param sourceURL - Specifies the URL of the blob. The value
     *                           may be a URL of up to 2 KB in length that specifies a blob.
     *                           The value should be URL-encoded as it would appear
     *                           in a request URI. The source blob must either be public
     *                           or must be authenticated via a shared access signature.
     *                           If the source blob is public, no authentication is required
     *                           to perform the operation. Here are some examples of source object URLs:
     *                           - https://myaccount.blob.core.windows.net/mycontainer/myblob
     *                           - https://myaccount.blob.core.windows.net/mycontainer/myblob?snapshot=<DateTime>
     * @param options - Optional parameters.
     */
    async syncUploadFromURL(sourceURL, options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("BlockBlobClient-syncUploadFromURL", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blockBlobContext.putBlobFromUrl(0, sourceURL, {
                ...options,
                blobHttpHeaders: options.blobHTTPHeaders,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                sourceModifiedAccessConditions: {
                    sourceIfMatch: options.sourceConditions?.ifMatch,
                    sourceIfModifiedSince: options.sourceConditions?.ifModifiedSince,
                    sourceIfNoneMatch: options.sourceConditions?.ifNoneMatch,
                    sourceIfUnmodifiedSince: options.sourceConditions?.ifUnmodifiedSince,
                    sourceIfTags: options.sourceConditions?.tagConditions,
                },
                cpkInfo: options.customerProvidedKey,
                copySourceAuthorization: utils_common_httpAuthorizationToString(options.sourceAuthorization),
                tier: toAccessTier(options.tier),
                blobTagsString: toBlobTagsString(options.tags),
                copySourceTags: options.copySourceTags,
                fileRequestIntent: options.sourceShareTokenIntent,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Uploads the specified block to the block blob's "staging area" to be later
     * committed by a call to commitBlockList.
     * @see https://learn.microsoft.com/rest/api/storageservices/put-block
     *
     * @param blockId - A 64-byte value that is base64-encoded
     * @param body - Data to upload to the staging area.
     * @param contentLength - Number of bytes to upload.
     * @param options - Options to the Block Blob Stage Block operation.
     * @returns Response data for the Block Blob Stage Block operation.
     */
    async stageBlock(blockId, body, contentLength, options = {}) {
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("BlockBlobClient-stageBlock", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blockBlobContext.stageBlock(blockId, contentLength, body, {
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                requestOptions: {
                    onUploadProgress: options.onProgress,
                },
                transactionalContentMD5: options.transactionalContentMD5,
                transactionalContentCrc64: options.transactionalContentCrc64,
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * The Stage Block From URL operation creates a new block to be committed as part
     * of a blob where the contents are read from a URL.
     * This API is available starting in version 2018-03-28.
     * @see https://learn.microsoft.com/rest/api/storageservices/put-block-from-url
     *
     * @param blockId - A 64-byte value that is base64-encoded
     * @param sourceURL - Specifies the URL of the blob. The value
     *                           may be a URL of up to 2 KB in length that specifies a blob.
     *                           The value should be URL-encoded as it would appear
     *                           in a request URI. The source blob must either be public
     *                           or must be authenticated via a shared access signature.
     *                           If the source blob is public, no authentication is required
     *                           to perform the operation. Here are some examples of source object URLs:
     *                           - https://myaccount.blob.core.windows.net/mycontainer/myblob
     *                           - https://myaccount.blob.core.windows.net/mycontainer/myblob?snapshot=<DateTime>
     * @param offset - From which position of the blob to download, greater than or equal to 0
     * @param count - How much data to be downloaded, greater than 0. Will download to the end when undefined
     * @param options - Options to the Block Blob Stage Block From URL operation.
     * @returns Response data for the Block Blob Stage Block From URL operation.
     */
    async stageBlockFromURL(blockId, sourceURL, offset = 0, count, options = {}) {
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("BlockBlobClient-stageBlockFromURL", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blockBlobContext.stageBlockFromURL(blockId, 0, sourceURL, {
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                sourceContentMD5: options.sourceContentMD5,
                sourceContentCrc64: options.sourceContentCrc64,
                sourceRange: offset === 0 && !count ? undefined : rangeToString({ offset, count }),
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                copySourceAuthorization: utils_common_httpAuthorizationToString(options.sourceAuthorization),
                fileRequestIntent: options.sourceShareTokenIntent,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Writes a blob by specifying the list of block IDs that make up the blob.
     * In order to be written as part of a blob, a block must have been successfully written
     * to the server in a prior {@link stageBlock} operation. You can call {@link commitBlockList} to
     * update a blob by uploading only those blocks that have changed, then committing the new and existing
     * blocks together. Any blocks not specified in the block list and permanently deleted.
     * @see https://learn.microsoft.com/rest/api/storageservices/put-block-list
     *
     * @param blocks -  Array of 64-byte value that is base64-encoded
     * @param options - Options to the Block Blob Commit Block List operation.
     * @returns Response data for the Block Blob Commit Block List operation.
     */
    async commitBlockList(blocks, options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("BlockBlobClient-commitBlockList", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.blockBlobContext.commitBlockList({ latest: blocks }, {
                abortSignal: options.abortSignal,
                blobHttpHeaders: options.blobHTTPHeaders,
                leaseAccessConditions: options.conditions,
                metadata: options.metadata,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                immutabilityPolicyExpiry: options.immutabilityPolicy?.expiriesOn,
                immutabilityPolicyMode: options.immutabilityPolicy?.policyMode,
                legalHold: options.legalHold,
                tier: toAccessTier(options.tier),
                blobTagsString: toBlobTagsString(options.tags),
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Returns the list of blocks that have been uploaded as part of a block blob
     * using the specified block list filter.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-block-list
     *
     * @param listType - Specifies whether to return the list of committed blocks,
     *                                        the list of uncommitted blocks, or both lists together.
     * @param options - Options to the Block Blob Get Block List operation.
     * @returns Response data for the Block Blob Get Block List operation.
     */
    async getBlockList(listType, options = {}) {
        return tracingClient.withSpan("BlockBlobClient-getBlockList", options, async (updatedOptions) => {
            const res = utils_common_assertResponse(await this.blockBlobContext.getBlockList(listType, {
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                tracingOptions: updatedOptions.tracingOptions,
            }));
            if (!res.committedBlocks) {
                res.committedBlocks = [];
            }
            if (!res.uncommittedBlocks) {
                res.uncommittedBlocks = [];
            }
            return res;
        });
    }
    // High level functions
    /**
     * Uploads a Buffer(Node.js)/Blob(browsers)/ArrayBuffer/ArrayBufferView object to a BlockBlob.
     *
     * When data length is no more than the specifiled {@link BlockBlobParallelUploadOptions.maxSingleShotSize} (default is
     * {@link BLOCK_BLOB_MAX_UPLOAD_BLOB_BYTES}), this method will use 1 {@link upload} call to finish the upload.
     * Otherwise, this method will call {@link stageBlock} to upload blocks, and finally call {@link commitBlockList}
     * to commit the block list.
     *
     * A common {@link BlockBlobParallelUploadOptions.blobHTTPHeaders} option to set is
     * `blobContentType`, enabling the browser to provide
     * functionality based on file type.
     *
     * @param data - Buffer(Node.js), Blob, ArrayBuffer or ArrayBufferView
     * @param options -
     */
    async uploadData(data, options = {}) {
        return tracingClient.withSpan("BlockBlobClient-uploadData", options, async (updatedOptions) => {
            if (esm_isNodeLike) {
                let buffer;
                if (data instanceof Buffer) {
                    buffer = data;
                }
                else if (data instanceof ArrayBuffer) {
                    buffer = Buffer.from(data);
                }
                else {
                    data = data;
                    buffer = Buffer.from(data.buffer, data.byteOffset, data.byteLength);
                }
                return this.uploadSeekableInternal((offset, size) => buffer.slice(offset, offset + size), buffer.byteLength, updatedOptions);
            }
            else {
                const browserBlob = new Blob([data]);
                return this.uploadSeekableInternal((offset, size) => browserBlob.slice(offset, offset + size), browserBlob.size, updatedOptions);
            }
        });
    }
    /**
     * ONLY AVAILABLE IN BROWSERS.
     *
     * Uploads a browser Blob/File/ArrayBuffer/ArrayBufferView object to block blob.
     *
     * When buffer length lesser than or equal to 256MB, this method will use 1 upload call to finish the upload.
     * Otherwise, this method will call {@link stageBlock} to upload blocks, and finally call
     * {@link commitBlockList} to commit the block list.
     *
     * A common {@link BlockBlobParallelUploadOptions.blobHTTPHeaders} option to set is
     * `blobContentType`, enabling the browser to provide
     * functionality based on file type.
     *
     * @deprecated Use {@link uploadData} instead.
     *
     * @param browserData - Blob, File, ArrayBuffer or ArrayBufferView
     * @param options - Options to upload browser data.
     * @returns Response data for the Blob Upload operation.
     */
    async uploadBrowserData(browserData, options = {}) {
        return tracingClient.withSpan("BlockBlobClient-uploadBrowserData", options, async (updatedOptions) => {
            const browserBlob = new Blob([browserData]);
            return this.uploadSeekableInternal((offset, size) => browserBlob.slice(offset, offset + size), browserBlob.size, updatedOptions);
        });
    }
    /**
     *
     * Uploads data to block blob. Requires a bodyFactory as the data source,
     * which need to return a {@link HttpRequestBody} object with the offset and size provided.
     *
     * When data length is no more than the specified {@link BlockBlobParallelUploadOptions.maxSingleShotSize} (default is
     * {@link BLOCK_BLOB_MAX_UPLOAD_BLOB_BYTES}), this method will use 1 {@link upload} call to finish the upload.
     * Otherwise, this method will call {@link stageBlock} to upload blocks, and finally call {@link commitBlockList}
     * to commit the block list.
     *
     * @param bodyFactory -
     * @param size - size of the data to upload.
     * @param options - Options to Upload to Block Blob operation.
     * @returns Response data for the Blob Upload operation.
     */
    async uploadSeekableInternal(bodyFactory, size, options = {}) {
        let blockSize = options.blockSize ?? 0;
        if (blockSize < 0 || blockSize > BLOCK_BLOB_MAX_STAGE_BLOCK_BYTES) {
            throw new RangeError(`blockSize option must be >= 0 and <= ${BLOCK_BLOB_MAX_STAGE_BLOCK_BYTES}`);
        }
        const maxSingleShotSize = options.maxSingleShotSize ?? BLOCK_BLOB_MAX_UPLOAD_BLOB_BYTES;
        if (maxSingleShotSize < 0 || maxSingleShotSize > BLOCK_BLOB_MAX_UPLOAD_BLOB_BYTES) {
            throw new RangeError(`maxSingleShotSize option must be >= 0 and <= ${BLOCK_BLOB_MAX_UPLOAD_BLOB_BYTES}`);
        }
        if (blockSize === 0) {
            if (size > BLOCK_BLOB_MAX_STAGE_BLOCK_BYTES * BLOCK_BLOB_MAX_BLOCKS) {
                throw new RangeError(`${size} is too larger to upload to a block blob.`);
            }
            if (size > maxSingleShotSize) {
                blockSize = Math.ceil(size / BLOCK_BLOB_MAX_BLOCKS);
                if (blockSize < DEFAULT_BLOB_DOWNLOAD_BLOCK_BYTES) {
                    blockSize = DEFAULT_BLOB_DOWNLOAD_BLOCK_BYTES;
                }
            }
        }
        if (!options.blobHTTPHeaders) {
            options.blobHTTPHeaders = {};
        }
        if (!options.conditions) {
            options.conditions = {};
        }
        return tracingClient.withSpan("BlockBlobClient-uploadSeekableInternal", options, async (updatedOptions) => {
            if (size <= maxSingleShotSize) {
                return utils_common_assertResponse(await this.upload(bodyFactory(0, size), size, updatedOptions));
            }
            const numBlocks = Math.floor((size - 1) / blockSize) + 1;
            if (numBlocks > BLOCK_BLOB_MAX_BLOCKS) {
                throw new RangeError(`The buffer's size is too big or the BlockSize is too small;` +
                    `the number of blocks must be <= ${BLOCK_BLOB_MAX_BLOCKS}`);
            }
            const blockList = [];
            const blockIDPrefix = esm_randomUUID();
            let transferProgress = 0;
            const batch = new Batch(options.concurrency);
            for (let i = 0; i < numBlocks; i++) {
                batch.addOperation(async () => {
                    const blockID = utils_common_generateBlockID(blockIDPrefix, i);
                    const start = blockSize * i;
                    const end = i === numBlocks - 1 ? size : start + blockSize;
                    const contentLength = end - start;
                    blockList.push(blockID);
                    await this.stageBlock(blockID, bodyFactory(start, contentLength), contentLength, {
                        abortSignal: options.abortSignal,
                        conditions: options.conditions,
                        encryptionScope: options.encryptionScope,
                        tracingOptions: updatedOptions.tracingOptions,
                    });
                    // Update progress after block is successfully uploaded to server, in case of block trying
                    // TODO: Hook with convenience layer progress event in finer level
                    transferProgress += contentLength;
                    if (options.onProgress) {
                        options.onProgress({
                            loadedBytes: transferProgress,
                        });
                    }
                });
            }
            await batch.do();
            return this.commitBlockList(blockList, updatedOptions);
        });
    }
    /**
     * ONLY AVAILABLE IN NODE.JS RUNTIME.
     *
     * Uploads a local file in blocks to a block blob.
     *
     * When file size lesser than or equal to 256MB, this method will use 1 upload call to finish the upload.
     * Otherwise, this method will call stageBlock to upload blocks, and finally call commitBlockList
     * to commit the block list.
     *
     * @param filePath - Full path of local file
     * @param options - Options to Upload to Block Blob operation.
     * @returns Response data for the Blob Upload operation.
     */
    async uploadFile(filePath, options = {}) {
        return tracingClient.withSpan("BlockBlobClient-uploadFile", options, async (updatedOptions) => {
            const size = (await fsStat(filePath)).size;
            return this.uploadSeekableInternal((offset, count) => {
                return () => fsCreateReadStream(filePath, {
                    autoClose: true,
                    end: count ? offset + count - 1 : Infinity,
                    start: offset,
                });
            }, size, {
                ...options,
                tracingOptions: updatedOptions.tracingOptions,
            });
        });
    }
    /**
     * ONLY AVAILABLE IN NODE.JS RUNTIME.
     *
     * Uploads a Node.js Readable stream into block blob.
     *
     * PERFORMANCE IMPROVEMENT TIPS:
     * * Input stream highWaterMark is better to set a same value with bufferSize
     *    parameter, which will avoid Buffer.concat() operations.
     *
     * @param stream - Node.js Readable stream
     * @param bufferSize - Size of every buffer allocated, also the block size in the uploaded block blob. Default value is 8MB
     * @param maxConcurrency -  Max concurrency indicates the max number of buffers that can be allocated,
     *                                 positive correlation with max uploading concurrency. Default value is 5
     * @param options - Options to Upload Stream to Block Blob operation.
     * @returns Response data for the Blob Upload operation.
     */
    async uploadStream(stream, bufferSize = DEFAULT_BLOCK_BUFFER_SIZE_BYTES, maxConcurrency = 5, options = {}) {
        if (!options.blobHTTPHeaders) {
            options.blobHTTPHeaders = {};
        }
        if (!options.conditions) {
            options.conditions = {};
        }
        return tracingClient.withSpan("BlockBlobClient-uploadStream", options, async (updatedOptions) => {
            let blockNum = 0;
            const blockIDPrefix = esm_randomUUID();
            let transferProgress = 0;
            const blockList = [];
            const scheduler = new BufferScheduler(stream, bufferSize, maxConcurrency, async (body, length) => {
                const blockID = utils_common_generateBlockID(blockIDPrefix, blockNum);
                blockList.push(blockID);
                blockNum++;
                await this.stageBlock(blockID, body, length, {
                    customerProvidedKey: options.customerProvidedKey,
                    conditions: options.conditions,
                    encryptionScope: options.encryptionScope,
                    tracingOptions: updatedOptions.tracingOptions,
                });
                // Update progress after block is successfully uploaded to server, in case of block trying
                transferProgress += length;
                if (options.onProgress) {
                    options.onProgress({ loadedBytes: transferProgress });
                }
            }, 
            // concurrency should set a smaller value than maxConcurrency, which is helpful to
            // reduce the possibility when a outgoing handler waits for stream data, in
            // this situation, outgoing handlers are blocked.
            // Outgoing queue shouldn't be empty.
            Math.ceil((maxConcurrency / 4) * 3));
            await scheduler.do();
            return utils_common_assertResponse(await this.commitBlockList(blockList, {
                ...options,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
}
/**
 * PageBlobClient defines a set of operations applicable to page blobs.
 */
class PageBlobClient extends BlobClient {
    /**
     * pageBlobsContext provided by protocol layer.
     */
    pageBlobContext;
    constructor(urlOrConnectionString, credentialOrPipelineOrContainerName, blobNameOrOptions, 
    // Legacy, no fix for eslint error without breaking. Disable it for this interface.
    /* eslint-disable-next-line @azure/azure-sdk/ts-naming-options*/
    options) {
        // In TypeScript we cannot simply pass all parameters to super() like below so have to duplicate the code instead.
        //   super(s, credentialOrPipelineOrContainerNameOrOptions, blobNameOrOptions, options);
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
            options = blobNameOrOptions;
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
            typeof credentialOrPipelineOrContainerName === "string" &&
            blobNameOrOptions &&
            typeof blobNameOrOptions === "string") {
            // (connectionString: string, containerName: string, blobName: string, options?: StoragePipelineOptions)
            const containerName = credentialOrPipelineOrContainerName;
            const blobName = blobNameOrOptions;
            const extractedCreds = utils_common_extractConnectionStringParts(urlOrConnectionString);
            if (extractedCreds.kind === "AccountConnString") {
                if (esm_isNodeLike) {
                    const sharedKeyCredential = new StorageSharedKeyCredential(extractedCreds.accountName, extractedCreds.accountKey);
                    url = utils_common_appendToURLPath(utils_common_appendToURLPath(extractedCreds.url, encodeURIComponent(containerName)), encodeURIComponent(blobName));
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
                    utils_common_appendToURLPath(utils_common_appendToURLPath(extractedCreds.url, encodeURIComponent(containerName)), encodeURIComponent(blobName)) +
                        "?" +
                        extractedCreds.accountSas;
                pipeline = newPipeline(new AnonymousCredential(), options);
            }
            else {
                throw new Error("Connection string must be either an Account connection string or a SAS connection string");
            }
        }
        else {
            throw new Error("Expecting non-empty strings for containerName and blobName parameters");
        }
        super(url, pipeline);
        this.pageBlobContext = this.storageClientContext.pageBlob;
    }
    /**
     * Creates a new PageBlobClient object identical to the source but with the
     * specified snapshot timestamp.
     * Provide "" will remove the snapshot and return a Client to the base blob.
     *
     * @param snapshot - The snapshot timestamp.
     * @returns A new PageBlobClient object identical to the source but with the specified snapshot timestamp.
     */
    withSnapshot(snapshot) {
        return new PageBlobClient(utils_common_setURLParameter(this.url, utils_constants_URLConstants.Parameters.SNAPSHOT, snapshot.length === 0 ? undefined : snapshot), this.pipeline);
    }
    /**
     * Creates a page blob of the specified length. Call uploadPages to upload data
     * data to a page blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/put-blob
     *
     * @param size - size of the page blob.
     * @param options - Options to the Page Blob Create operation.
     * @returns Response data for the Page Blob Create operation.
     */
    async create(size, options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("PageBlobClient-create", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.pageBlobContext.create(0, size, {
                abortSignal: options.abortSignal,
                blobHttpHeaders: options.blobHTTPHeaders,
                blobSequenceNumber: options.blobSequenceNumber,
                leaseAccessConditions: options.conditions,
                metadata: options.metadata,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                immutabilityPolicyExpiry: options.immutabilityPolicy?.expiriesOn,
                immutabilityPolicyMode: options.immutabilityPolicy?.policyMode,
                legalHold: options.legalHold,
                tier: toAccessTier(options.tier),
                blobTagsString: toBlobTagsString(options.tags),
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Creates a page blob of the specified length. Call uploadPages to upload data
     * data to a page blob. If the blob with the same name already exists, the content
     * of the existing blob will remain unchanged.
     * @see https://learn.microsoft.com/rest/api/storageservices/put-blob
     *
     * @param size - size of the page blob.
     * @param options -
     */
    async createIfNotExists(size, options = {}) {
        return tracingClient.withSpan("PageBlobClient-createIfNotExists", options, async (updatedOptions) => {
            try {
                const conditions = { ifNoneMatch: ETagAny };
                const res = utils_common_assertResponse(await this.create(size, {
                    ...options,
                    conditions,
                    tracingOptions: updatedOptions.tracingOptions,
                }));
                return {
                    succeeded: true,
                    ...res,
                    _response: res._response, // _response is made non-enumerable
                };
            }
            catch (e) {
                if (e.details?.errorCode === "BlobAlreadyExists") {
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
     * Writes 1 or more pages to the page blob. The start and end offsets must be a multiple of 512.
     * @see https://learn.microsoft.com/rest/api/storageservices/put-page
     *
     * @param body - Data to upload
     * @param offset - Offset of destination page blob
     * @param count - Content length of the body, also number of bytes to be uploaded
     * @param options - Options to the Page Blob Upload Pages operation.
     * @returns Response data for the Page Blob Upload Pages operation.
     */
    async uploadPages(body, offset, count, options = {}) {
        options.conditions = options.conditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("PageBlobClient-uploadPages", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.pageBlobContext.uploadPages(count, body, {
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                requestOptions: {
                    onUploadProgress: options.onProgress,
                },
                range: rangeToString({ offset, count }),
                sequenceNumberAccessConditions: options.conditions,
                transactionalContentMD5: options.transactionalContentMD5,
                transactionalContentCrc64: options.transactionalContentCrc64,
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * The Upload Pages operation writes a range of pages to a page blob where the
     * contents are read from a URL.
     * @see https://learn.microsoft.com/rest/api/storageservices/put-page-from-url
     *
     * @param sourceURL - Specify a URL to the copy source, Shared Access Signature(SAS) maybe needed for authentication
     * @param sourceOffset - The source offset to copy from. Pass 0 to copy from the beginning of source page blob
     * @param destOffset - Offset of destination page blob
     * @param count - Number of bytes to be uploaded from source page blob
     * @param options -
     */
    async uploadPagesFromURL(sourceURL, sourceOffset, destOffset, count, options = {}) {
        options.conditions = options.conditions || {};
        options.sourceConditions = options.sourceConditions || {};
        ensureCpkIfSpecified(options.customerProvidedKey, this.isHttps);
        return tracingClient.withSpan("PageBlobClient-uploadPagesFromURL", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.pageBlobContext.uploadPagesFromURL(sourceURL, rangeToString({ offset: sourceOffset, count }), 0, rangeToString({ offset: destOffset, count }), {
                abortSignal: options.abortSignal,
                sourceContentMD5: options.sourceContentMD5,
                sourceContentCrc64: options.sourceContentCrc64,
                leaseAccessConditions: options.conditions,
                sequenceNumberAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                sourceModifiedAccessConditions: {
                    sourceIfMatch: options.sourceConditions?.ifMatch,
                    sourceIfModifiedSince: options.sourceConditions?.ifModifiedSince,
                    sourceIfNoneMatch: options.sourceConditions?.ifNoneMatch,
                    sourceIfUnmodifiedSince: options.sourceConditions?.ifUnmodifiedSince,
                },
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                copySourceAuthorization: utils_common_httpAuthorizationToString(options.sourceAuthorization),
                fileRequestIntent: options.sourceShareTokenIntent,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Frees the specified pages from the page blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/put-page
     *
     * @param offset - Starting byte position of the pages to clear.
     * @param count - Number of bytes to clear.
     * @param options - Options to the Page Blob Clear Pages operation.
     * @returns Response data for the Page Blob Clear Pages operation.
     */
    async clearPages(offset = 0, count, options = {}) {
        options.conditions = options.conditions || {};
        return tracingClient.withSpan("PageBlobClient-clearPages", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.pageBlobContext.clearPages(0, {
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                range: rangeToString({ offset, count }),
                sequenceNumberAccessConditions: options.conditions,
                cpkInfo: options.customerProvidedKey,
                encryptionScope: options.encryptionScope,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Returns the list of valid page ranges for a page blob or snapshot of a page blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-page-ranges
     *
     * @param offset - Starting byte position of the page ranges.
     * @param count - Number of bytes to get.
     * @param options - Options to the Page Blob Get Ranges operation.
     * @returns Response data for the Page Blob Get Ranges operation.
     */
    async getPageRanges(offset = 0, count, options = {}) {
        options.conditions = options.conditions || {};
        return tracingClient.withSpan("PageBlobClient-getPageRanges", options, async (updatedOptions) => {
            const response = utils_common_assertResponse(await this.pageBlobContext.getPageRanges({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                range: rangeToString({ offset, count }),
                tracingOptions: updatedOptions.tracingOptions,
            }));
            return rangeResponseFromModel(response);
        });
    }
    /**
     * getPageRangesSegment returns a single segment of page ranges starting from the
     * specified Marker. Use an empty Marker to start enumeration from the beginning.
     * After getting a segment, process it, and then call getPageRangesSegment again
     * (passing the the previously-returned Marker) to get the next segment.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-page-ranges
     *
     * @param offset - Starting byte position of the page ranges.
     * @param count - Number of bytes to get.
     * @param marker - A string value that identifies the portion of the list to be returned with the next list operation.
     * @param options - Options to PageBlob Get Page Ranges Segment operation.
     */
    async listPageRangesSegment(offset = 0, count, marker, options = {}) {
        return tracingClient.withSpan("PageBlobClient-getPageRangesSegment", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.pageBlobContext.getPageRanges({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                range: rangeToString({ offset, count }),
                marker: marker,
                maxPageSize: options.maxPageSize,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Returns an AsyncIterableIterator for {@link PageBlobGetPageRangesResponseModel}
     *
     * @param offset - Starting byte position of the page ranges.
     * @param count - Number of bytes to get.
     * @param marker - A string value that identifies the portion of
     *                          the get of page ranges to be returned with the next getting operation. The
     *                          operation returns the ContinuationToken value within the response body if the
     *                          getting operation did not return all page ranges remaining within the current page.
     *                          The ContinuationToken value can be used as the value for
     *                          the marker parameter in a subsequent call to request the next page of get
     *                          items. The marker value is opaque to the client.
     * @param options - Options to List Page Ranges operation.
     */
    async *listPageRangeItemSegments(offset = 0, count, marker, options = {}) {
        let getPageRangeItemSegmentsResponse;
        if (!!marker || marker === undefined) {
            do {
                getPageRangeItemSegmentsResponse = await this.listPageRangesSegment(offset, count, marker, options);
                marker = getPageRangeItemSegmentsResponse.continuationToken;
                yield await getPageRangeItemSegmentsResponse;
            } while (marker);
        }
    }
    /**
     * Returns an AsyncIterableIterator of {@link PageRangeInfo} objects
     *
     * @param offset - Starting byte position of the page ranges.
     * @param count - Number of bytes to get.
     * @param options - Options to List Page Ranges operation.
     */
    async *listPageRangeItems(offset = 0, count, options = {}) {
        let marker;
        for await (const getPageRangesSegment of this.listPageRangeItemSegments(offset, count, marker, options)) {
            yield* ExtractPageRangeInfoItems(getPageRangesSegment);
        }
    }
    /**
     * Returns an async iterable iterator to list of page ranges for a page blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-page-ranges
     *
     *  .byPage() returns an async iterable iterator to list of page ranges for a page blob.
     *
     * ```ts snippet:ClientsListPageBlobs
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
     * const pageBlobClient = containerClient.getPageBlobClient(blobName);
     *
     * // Example using `for await` syntax
     * let i = 1;
     * for await (const pageRange of pageBlobClient.listPageRanges()) {
     *   console.log(`Page range ${i++}: ${pageRange.start} - ${pageRange.end}`);
     * }
     *
     * // Example using `iter.next()` syntax
     * i = 1;
     * const iter = pageBlobClient.listPageRanges();
     * let { value, done } = await iter.next();
     * while (!done) {
     *   console.log(`Page range ${i++}: ${value.start} - ${value.end}`);
     *   ({ value, done } = await iter.next());
     * }
     *
     * // Example using `byPage()` syntax
     * i = 1;
     * for await (const page of pageBlobClient.listPageRanges().byPage({ maxPageSize: 20 })) {
     *   for (const pageRange of page.pageRange || []) {
     *     console.log(`Page range ${i++}: ${pageRange.start} - ${pageRange.end}`);
     *   }
     * }
     *
     * // Example using paging with a marker
     * i = 1;
     * let iterator = pageBlobClient.listPageRanges().byPage({ maxPageSize: 2 });
     * let response = (await iterator.next()).value;
     * // Prints 2 page ranges
     * if (response.pageRange) {
     *   for (const pageRange of response.pageRange) {
     *     console.log(`Page range ${i++}: ${pageRange.start} - ${pageRange.end}`);
     *   }
     * }
     * // Gets next marker
     * let marker = response.continuationToken;
     * // Passing next marker as continuationToken
     * iterator = pageBlobClient.listPageRanges().byPage({ continuationToken: marker, maxPageSize: 10 });
     * response = (await iterator.next()).value;
     * // Prints 10 page ranges
     * if (response.pageRange) {
     *   for (const pageRange of response.pageRange) {
     *     console.log(`Page range ${i++}: ${pageRange.start} - ${pageRange.end}`);
     *   }
     * }
     * ```
     *
     * @param offset - Starting byte position of the page ranges.
     * @param count - Number of bytes to get.
     * @param options - Options to the Page Blob Get Ranges operation.
     * @returns An asyncIterableIterator that supports paging.
     */
    listPageRanges(offset = 0, count, options = {}) {
        options.conditions = options.conditions || {};
        // AsyncIterableIterator to iterate over blobs
        const iter = this.listPageRangeItems(offset, count, options);
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
                return this.listPageRangeItemSegments(offset, count, settings.continuationToken, {
                    maxPageSize: settings.maxPageSize,
                    ...options,
                });
            },
        };
    }
    /**
     * Gets the collection of page ranges that differ between a specified snapshot and this page blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-page-ranges
     *
     * @param offset - Starting byte position of the page blob
     * @param count - Number of bytes to get ranges diff.
     * @param prevSnapshot - Timestamp of snapshot to retrieve the difference.
     * @param options - Options to the Page Blob Get Page Ranges Diff operation.
     * @returns Response data for the Page Blob Get Page Range Diff operation.
     */
    async getPageRangesDiff(offset, count, prevSnapshot, options = {}) {
        options.conditions = options.conditions || {};
        return tracingClient.withSpan("PageBlobClient-getPageRangesDiff", options, async (updatedOptions) => {
            const result = utils_common_assertResponse(await this.pageBlobContext.getPageRangesDiff({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                prevsnapshot: prevSnapshot,
                range: rangeToString({ offset, count }),
                tracingOptions: updatedOptions.tracingOptions,
            }));
            return rangeResponseFromModel(result);
        });
    }
    /**
     * getPageRangesDiffSegment returns a single segment of page ranges starting from the
     * specified Marker for difference between previous snapshot and the target page blob.
     * Use an empty Marker to start enumeration from the beginning.
     * After getting a segment, process it, and then call getPageRangesDiffSegment again
     * (passing the the previously-returned Marker) to get the next segment.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-page-ranges
     *
     * @param offset - Starting byte position of the page ranges.
     * @param count - Number of bytes to get.
     * @param prevSnapshotOrUrl - Timestamp of snapshot to retrieve the difference or URL of snapshot to retrieve the difference.
     * @param marker - A string value that identifies the portion of the get to be returned with the next get operation.
     * @param options - Options to the Page Blob Get Page Ranges Diff operation.
     */
    async listPageRangesDiffSegment(offset, count, prevSnapshotOrUrl, marker, options = {}) {
        return tracingClient.withSpan("PageBlobClient-getPageRangesDiffSegment", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.pageBlobContext.getPageRangesDiff({
                abortSignal: options?.abortSignal,
                leaseAccessConditions: options?.conditions,
                modifiedAccessConditions: {
                    ...options?.conditions,
                    ifTags: options?.conditions?.tagConditions,
                },
                prevsnapshot: prevSnapshotOrUrl,
                range: rangeToString({
                    offset: offset,
                    count: count,
                }),
                marker: marker,
                maxPageSize: options?.maxPageSize,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Returns an AsyncIterableIterator for {@link PageBlobGetPageRangesDiffResponseModel}
     *
     *
     * @param offset - Starting byte position of the page ranges.
     * @param count - Number of bytes to get.
     * @param prevSnapshotOrUrl - Timestamp of snapshot to retrieve the difference or URL of snapshot to retrieve the difference.
     * @param marker - A string value that identifies the portion of
     *                          the get of page ranges to be returned with the next getting operation. The
     *                          operation returns the ContinuationToken value within the response body if the
     *                          getting operation did not return all page ranges remaining within the current page.
     *                          The ContinuationToken value can be used as the value for
     *                          the marker parameter in a subsequent call to request the next page of get
     *                          items. The marker value is opaque to the client.
     * @param options - Options to the Page Blob Get Page Ranges Diff operation.
     */
    async *listPageRangeDiffItemSegments(offset, count, prevSnapshotOrUrl, marker, options) {
        let getPageRangeItemSegmentsResponse;
        if (!!marker || marker === undefined) {
            do {
                getPageRangeItemSegmentsResponse = await this.listPageRangesDiffSegment(offset, count, prevSnapshotOrUrl, marker, options);
                marker = getPageRangeItemSegmentsResponse.continuationToken;
                yield await getPageRangeItemSegmentsResponse;
            } while (marker);
        }
    }
    /**
     * Returns an AsyncIterableIterator of {@link PageRangeInfo} objects
     *
     * @param offset - Starting byte position of the page ranges.
     * @param count - Number of bytes to get.
     * @param prevSnapshotOrUrl - Timestamp of snapshot to retrieve the difference or URL of snapshot to retrieve the difference.
     * @param options - Options to the Page Blob Get Page Ranges Diff operation.
     */
    async *listPageRangeDiffItems(offset, count, prevSnapshotOrUrl, options) {
        let marker;
        for await (const getPageRangesSegment of this.listPageRangeDiffItemSegments(offset, count, prevSnapshotOrUrl, marker, options)) {
            yield* ExtractPageRangeInfoItems(getPageRangesSegment);
        }
    }
    /**
     * Returns an async iterable iterator to list of page ranges that differ between a specified snapshot and this page blob.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-page-ranges
     *
     *  .byPage() returns an async iterable iterator to list of page ranges that differ between a specified snapshot and this page blob.
     *
     * ```ts snippet:ClientsListPageBlobsDiff
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
     * const pageBlobClient = containerClient.getPageBlobClient(blobName);
     *
     * const offset = 0;
     * const count = 1024;
     * const previousSnapshot = "<previous snapshot>";
     * // Example using `for await` syntax
     * let i = 1;
     * for await (const pageRange of pageBlobClient.listPageRangesDiff(offset, count, previousSnapshot)) {
     *   console.log(`Page range ${i++}: ${pageRange.start} - ${pageRange.end}`);
     * }
     *
     * // Example using `iter.next()` syntax
     * i = 1;
     * const iter = pageBlobClient.listPageRangesDiff(offset, count, previousSnapshot);
     * let { value, done } = await iter.next();
     * while (!done) {
     *   console.log(`Page range ${i++}: ${value.start} - ${value.end}`);
     *   ({ value, done } = await iter.next());
     * }
     *
     * // Example using `byPage()` syntax
     * i = 1;
     * for await (const page of pageBlobClient
     *   .listPageRangesDiff(offset, count, previousSnapshot)
     *   .byPage({ maxPageSize: 20 })) {
     *   for (const pageRange of page.pageRange || []) {
     *     console.log(`Page range ${i++}: ${pageRange.start} - ${pageRange.end}`);
     *   }
     * }
     *
     * // Example using paging with a marker
     * i = 1;
     * let iterator = pageBlobClient
     *   .listPageRangesDiff(offset, count, previousSnapshot)
     *   .byPage({ maxPageSize: 2 });
     * let response = (await iterator.next()).value;
     * // Prints 2 page ranges
     * if (response.pageRange) {
     *   for (const pageRange of response.pageRange) {
     *     console.log(`Page range ${i++}: ${pageRange.start} - ${pageRange.end}`);
     *   }
     * }
     * // Gets next marker
     * let marker = response.continuationToken;
     * // Passing next marker as continuationToken
     * iterator = pageBlobClient
     *   .listPageRangesDiff(offset, count, previousSnapshot)
     *   .byPage({ continuationToken: marker, maxPageSize: 10 });
     * response = (await iterator.next()).value;
     * // Prints 10 page ranges
     * if (response.pageRange) {
     *   for (const pageRange of response.pageRange) {
     *     console.log(`Page range ${i++}: ${pageRange.start} - ${pageRange.end}`);
     *   }
     * }
     * ```
     *
     * @param offset - Starting byte position of the page ranges.
     * @param count - Number of bytes to get.
     * @param prevSnapshot - Timestamp of snapshot to retrieve the difference.
     * @param options - Options to the Page Blob Get Ranges operation.
     * @returns An asyncIterableIterator that supports paging.
     */
    listPageRangesDiff(offset, count, prevSnapshot, options = {}) {
        options.conditions = options.conditions || {};
        // AsyncIterableIterator to iterate over blobs
        const iter = this.listPageRangeDiffItems(offset, count, prevSnapshot, {
            ...options,
        });
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
                return this.listPageRangeDiffItemSegments(offset, count, prevSnapshot, settings.continuationToken, {
                    maxPageSize: settings.maxPageSize,
                    ...options,
                });
            },
        };
    }
    /**
     * Gets the collection of page ranges that differ between a specified snapshot and this page blob for managed disks.
     * @see https://learn.microsoft.com/rest/api/storageservices/get-page-ranges
     *
     * @param offset - Starting byte position of the page blob
     * @param count - Number of bytes to get ranges diff.
     * @param prevSnapshotUrl - URL of snapshot to retrieve the difference.
     * @param options - Options to the Page Blob Get Page Ranges Diff operation.
     * @returns Response data for the Page Blob Get Page Range Diff operation.
     */
    async getPageRangesDiffForManagedDisks(offset, count, prevSnapshotUrl, options = {}) {
        options.conditions = options.conditions || {};
        return tracingClient.withSpan("PageBlobClient-GetPageRangesDiffForManagedDisks", options, async (updatedOptions) => {
            const response = utils_common_assertResponse(await this.pageBlobContext.getPageRangesDiff({
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                prevSnapshotUrl,
                range: rangeToString({ offset, count }),
                tracingOptions: updatedOptions.tracingOptions,
            }));
            return rangeResponseFromModel(response);
        });
    }
    /**
     * Resizes the page blob to the specified size (which must be a multiple of 512).
     * @see https://learn.microsoft.com/rest/api/storageservices/set-blob-properties
     *
     * @param size - Target size
     * @param options - Options to the Page Blob Resize operation.
     * @returns Response data for the Page Blob Resize operation.
     */
    async resize(size, options = {}) {
        options.conditions = options.conditions || {};
        return tracingClient.withSpan("PageBlobClient-resize", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.pageBlobContext.resize(size, {
                abortSignal: options.abortSignal,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                encryptionScope: options.encryptionScope,
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Sets a page blob's sequence number.
     * @see https://learn.microsoft.com/rest/api/storageservices/set-blob-properties
     *
     * @param sequenceNumberAction - Indicates how the service should modify the blob's sequence number.
     * @param sequenceNumber - Required if sequenceNumberAction is max or update
     * @param options - Options to the Page Blob Update Sequence Number operation.
     * @returns Response data for the Page Blob Update Sequence Number operation.
     */
    async updateSequenceNumber(sequenceNumberAction, sequenceNumber, options = {}) {
        options.conditions = options.conditions || {};
        return tracingClient.withSpan("PageBlobClient-updateSequenceNumber", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.pageBlobContext.updateSequenceNumber(sequenceNumberAction, {
                abortSignal: options.abortSignal,
                blobSequenceNumber: sequenceNumber,
                leaseAccessConditions: options.conditions,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
    /**
     * Begins an operation to start an incremental copy from one page blob's snapshot to this page blob.
     * The snapshot is copied such that only the differential changes between the previously
     * copied snapshot are transferred to the destination.
     * The copied snapshots are complete copies of the original snapshot and can be read or copied from as usual.
     * @see https://learn.microsoft.com/rest/api/storageservices/incremental-copy-blob
     * @see https://learn.microsoft.com/azure/virtual-machines/windows/incremental-snapshots
     *
     * @param copySource - Specifies the name of the source page blob snapshot. For example,
     *                            https://myaccount.blob.core.windows.net/mycontainer/myblob?snapshot=<DateTime>
     * @param options - Options to the Page Blob Copy Incremental operation.
     * @returns Response data for the Page Blob Copy Incremental operation.
     */
    async startCopyIncremental(copySource, options = {}) {
        return tracingClient.withSpan("PageBlobClient-startCopyIncremental", options, async (updatedOptions) => {
            return utils_common_assertResponse(await this.pageBlobContext.copyIncremental(copySource, {
                abortSignal: options.abortSignal,
                modifiedAccessConditions: {
                    ...options.conditions,
                    ifTags: options.conditions?.tagConditions,
                },
                tracingOptions: updatedOptions.tracingOptions,
            }));
        });
    }
}
//# sourceMappingURL=Clients.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/BatchUtils.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


async function getBodyAsText(batchResponse) {
    let buffer = Buffer.alloc(BATCH_MAX_PAYLOAD_IN_BYTES);
    const responseLength = await streamToBuffer2(batchResponse.readableStreamBody, buffer);
    // Slice the buffer to trim the empty ending.
    buffer = buffer.slice(0, responseLength);
    return buffer.toString();
}
function utf8ByteLength(str) {
    return Buffer.byteLength(str);
}
//# sourceMappingURL=BatchUtils.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/storage-blob/dist/esm/BatchResponseParser.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.





const HTTP_HEADER_DELIMITER = ": ";
const SPACE_DELIMITER = " ";
const NOT_FOUND = -1;
/**
 * Util class for parsing batch response.
 */
class BatchResponseParser {
    batchResponse;
    responseBatchBoundary;
    perResponsePrefix;
    batchResponseEnding;
    subRequests;
    constructor(batchResponse, subRequests) {
        if (!batchResponse || !batchResponse.contentType) {
            // In special case(reported), server may return invalid content-type which could not be parsed.
            throw new RangeError("batchResponse is malformed or doesn't contain valid content-type.");
        }
        if (!subRequests || subRequests.size === 0) {
            // This should be prevent during coding.
            throw new RangeError("Invalid state: subRequests is not provided or size is 0.");
        }
        this.batchResponse = batchResponse;
        this.subRequests = subRequests;
        this.responseBatchBoundary = this.batchResponse.contentType.split("=")[1];
        this.perResponsePrefix = `--${this.responseBatchBoundary}${HTTP_LINE_ENDING}`;
        this.batchResponseEnding = `--${this.responseBatchBoundary}--`;
    }
    // For example of response, please refer to https://learn.microsoft.com/rest/api/storageservices/blob-batch#response
    async parseBatchResponse() {
        // When logic reach here, suppose batch request has already succeeded with 202, so we can further parse
        // sub request's response.
        if (this.batchResponse._response.status !== HTTPURLConnection.HTTP_ACCEPTED) {
            throw new Error(`Invalid state: batch request failed with status: '${this.batchResponse._response.status}'.`);
        }
        const responseBodyAsText = await getBodyAsText(this.batchResponse);
        const subResponses = responseBodyAsText
            .split(this.batchResponseEnding)[0] // string after ending is useless
            .split(this.perResponsePrefix)
            .slice(1); // string before first response boundary is useless
        const subResponseCount = subResponses.length;
        // Defensive coding in case of potential error parsing.
        // Note: subResponseCount == 1 is special case where sub request is invalid.
        // We try to prevent such cases through early validation, e.g. validate sub request count >= 1.
        // While in unexpected sub request invalid case, we allow sub response to be parsed and return to user.
        if (subResponseCount !== this.subRequests.size && subResponseCount !== 1) {
            throw new Error("Invalid state: sub responses' count is not equal to sub requests' count.");
        }
        const deserializedSubResponses = new Array(subResponseCount);
        let subResponsesSucceededCount = 0;
        let subResponsesFailedCount = 0;
        // Parse sub subResponses.
        for (let index = 0; index < subResponseCount; index++) {
            const subResponse = subResponses[index];
            const deserializedSubResponse = {};
            deserializedSubResponse.headers = toHttpHeadersLike(esm_httpHeaders_createHttpHeaders());
            const responseLines = subResponse.split(`${HTTP_LINE_ENDING}`);
            let subRespHeaderStartFound = false;
            let subRespHeaderEndFound = false;
            let subRespFailed = false;
            let contentId = NOT_FOUND;
            for (const responseLine of responseLines) {
                if (!subRespHeaderStartFound) {
                    // Convention line to indicate content ID
                    if (responseLine.startsWith(utils_constants_HeaderConstants.CONTENT_ID)) {
                        contentId = parseInt(responseLine.split(HTTP_HEADER_DELIMITER)[1]);
                    }
                    // Http version line with status code indicates the start of sub request's response.
                    // Example: HTTP/1.1 202 Accepted
                    if (responseLine.startsWith(HTTP_VERSION_1_1)) {
                        subRespHeaderStartFound = true;
                        const tokens = responseLine.split(SPACE_DELIMITER);
                        deserializedSubResponse.status = parseInt(tokens[1]);
                        deserializedSubResponse.statusMessage = tokens.slice(2).join(SPACE_DELIMITER);
                    }
                    continue; // Skip convention headers not specifically for sub request i.e. Content-Type: application/http and Content-ID: *
                }
                if (responseLine.trim() === "") {
                    // Sub response's header start line already found, and the first empty line indicates header end line found.
                    if (!subRespHeaderEndFound) {
                        subRespHeaderEndFound = true;
                    }
                    continue; // Skip empty line
                }
                // Note: when code reach here, it indicates subRespHeaderStartFound == true
                if (!subRespHeaderEndFound) {
                    if (responseLine.indexOf(HTTP_HEADER_DELIMITER) === -1) {
                        // Defensive coding to prevent from missing valuable lines.
                        throw new Error(`Invalid state: find non-empty line '${responseLine}' without HTTP header delimiter '${HTTP_HEADER_DELIMITER}'.`);
                    }
                    // Parse headers of sub response.
                    const tokens = responseLine.split(HTTP_HEADER_DELIMITER);
                    deserializedSubResponse.headers.set(tokens[0], tokens[1]);
                    if (tokens[0] === utils_constants_HeaderConstants.X_MS_ERROR_CODE) {
                        deserializedSubResponse.errorCode = tokens[1];
                        subRespFailed = true;
                    }
                }
                else {
                    // Assemble body of sub response.
                    if (!deserializedSubResponse.bodyAsText) {
                        deserializedSubResponse.bodyAsText = "";
                    }
                    deserializedSubResponse.bodyAsText += responseLine;
                }
            } // Inner for end
            // The response will contain the Content-ID header for each corresponding subrequest response to use for tracking.
