        /* int64 artifact_id = 2; */
        if (message.artifactId !== "0")
            writer.tag(2, commonjs.WireType.Varint).int64(message.artifactId);
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? commonjs.UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message github.actions.results.api.v1.FinalizeArtifactResponse
 */
const artifact_FinalizeArtifactResponse = new FinalizeArtifactResponse$Type();
// @generated message type with reflection information, may provide speed optimized methods
class ListArtifactsRequest$Type extends commonjs.MessageType {
    constructor() {
        super("github.actions.results.api.v1.ListArtifactsRequest", [
            { no: 1, name: "workflow_run_backend_id", kind: "scalar", T: 9 /*ScalarType.STRING*/ },
            { no: 2, name: "workflow_job_run_backend_id", kind: "scalar", T: 9 /*ScalarType.STRING*/ },
            { no: 3, name: "name_filter", kind: "message", T: () => StringValue },
            { no: 4, name: "id_filter", kind: "message", T: () => Int64Value }
        ]);
    }
    create(value) {
        const message = { workflowRunBackendId: "", workflowJobRunBackendId: "" };
        globalThis.Object.defineProperty(message, commonjs.MESSAGE_TYPE, { enumerable: false, value: this });
        if (value !== undefined)
            (0,commonjs.reflectionMergePartial)(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target !== null && target !== void 0 ? target : this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* string workflow_run_backend_id */ 1:
                    message.workflowRunBackendId = reader.string();
                    break;
                case /* string workflow_job_run_backend_id */ 2:
                    message.workflowJobRunBackendId = reader.string();
                    break;
                case /* google.protobuf.StringValue name_filter */ 3:
                    message.nameFilter = StringValue.internalBinaryRead(reader, reader.uint32(), options, message.nameFilter);
                    break;
                case /* google.protobuf.Int64Value id_filter */ 4:
                    message.idFilter = Int64Value.internalBinaryRead(reader, reader.uint32(), options, message.idFilter);
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? commonjs.UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* string workflow_run_backend_id = 1; */
        if (message.workflowRunBackendId !== "")
            writer.tag(1, commonjs.WireType.LengthDelimited).string(message.workflowRunBackendId);
        /* string workflow_job_run_backend_id = 2; */
        if (message.workflowJobRunBackendId !== "")
            writer.tag(2, commonjs.WireType.LengthDelimited).string(message.workflowJobRunBackendId);
        /* google.protobuf.StringValue name_filter = 3; */
        if (message.nameFilter)
            StringValue.internalBinaryWrite(message.nameFilter, writer.tag(3, commonjs.WireType.LengthDelimited).fork(), options).join();
        /* google.protobuf.Int64Value id_filter = 4; */
        if (message.idFilter)
            Int64Value.internalBinaryWrite(message.idFilter, writer.tag(4, commonjs.WireType.LengthDelimited).fork(), options).join();
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? commonjs.UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message github.actions.results.api.v1.ListArtifactsRequest
 */
const artifact_ListArtifactsRequest = new ListArtifactsRequest$Type();
// @generated message type with reflection information, may provide speed optimized methods
class ListArtifactsResponse$Type extends commonjs.MessageType {
    constructor() {
        super("github.actions.results.api.v1.ListArtifactsResponse", [
            { no: 1, name: "artifacts", kind: "message", repeat: 2 /*RepeatType.UNPACKED*/, T: () => ListArtifactsResponse_MonolithArtifact }
        ]);
    }
    create(value) {
        const message = { artifacts: [] };
        globalThis.Object.defineProperty(message, commonjs.MESSAGE_TYPE, { enumerable: false, value: this });
        if (value !== undefined)
            (0,commonjs.reflectionMergePartial)(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target !== null && target !== void 0 ? target : this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* repeated github.actions.results.api.v1.ListArtifactsResponse.MonolithArtifact artifacts */ 1:
                    message.artifacts.push(ListArtifactsResponse_MonolithArtifact.internalBinaryRead(reader, reader.uint32(), options));
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? commonjs.UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* repeated github.actions.results.api.v1.ListArtifactsResponse.MonolithArtifact artifacts = 1; */
        for (let i = 0; i < message.artifacts.length; i++)
            ListArtifactsResponse_MonolithArtifact.internalBinaryWrite(message.artifacts[i], writer.tag(1, commonjs.WireType.LengthDelimited).fork(), options).join();
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? commonjs.UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message github.actions.results.api.v1.ListArtifactsResponse
 */
const artifact_ListArtifactsResponse = new ListArtifactsResponse$Type();
// @generated message type with reflection information, may provide speed optimized methods
class ListArtifactsResponse_MonolithArtifact$Type extends commonjs.MessageType {
    constructor() {
        super("github.actions.results.api.v1.ListArtifactsResponse.MonolithArtifact", [
            { no: 1, name: "workflow_run_backend_id", kind: "scalar", T: 9 /*ScalarType.STRING*/ },
            { no: 2, name: "workflow_job_run_backend_id", kind: "scalar", T: 9 /*ScalarType.STRING*/ },
            { no: 3, name: "database_id", kind: "scalar", T: 3 /*ScalarType.INT64*/ },
            { no: 4, name: "name", kind: "scalar", T: 9 /*ScalarType.STRING*/ },
            { no: 5, name: "size", kind: "scalar", T: 3 /*ScalarType.INT64*/ },
            { no: 6, name: "created_at", kind: "message", T: () => Timestamp },
            { no: 7, name: "digest", kind: "message", T: () => StringValue }
        ]);
    }
    create(value) {
        const message = { workflowRunBackendId: "", workflowJobRunBackendId: "", databaseId: "0", name: "", size: "0" };
        globalThis.Object.defineProperty(message, commonjs.MESSAGE_TYPE, { enumerable: false, value: this });
        if (value !== undefined)
            (0,commonjs.reflectionMergePartial)(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target !== null && target !== void 0 ? target : this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* string workflow_run_backend_id */ 1:
                    message.workflowRunBackendId = reader.string();
                    break;
                case /* string workflow_job_run_backend_id */ 2:
                    message.workflowJobRunBackendId = reader.string();
                    break;
                case /* int64 database_id */ 3:
                    message.databaseId = reader.int64().toString();
                    break;
                case /* string name */ 4:
                    message.name = reader.string();
                    break;
                case /* int64 size */ 5:
                    message.size = reader.int64().toString();
                    break;
                case /* google.protobuf.Timestamp created_at */ 6:
                    message.createdAt = Timestamp.internalBinaryRead(reader, reader.uint32(), options, message.createdAt);
                    break;
                case /* google.protobuf.StringValue digest */ 7:
                    message.digest = StringValue.internalBinaryRead(reader, reader.uint32(), options, message.digest);
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? commonjs.UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* string workflow_run_backend_id = 1; */
        if (message.workflowRunBackendId !== "")
            writer.tag(1, commonjs.WireType.LengthDelimited).string(message.workflowRunBackendId);
        /* string workflow_job_run_backend_id = 2; */
        if (message.workflowJobRunBackendId !== "")
            writer.tag(2, commonjs.WireType.LengthDelimited).string(message.workflowJobRunBackendId);
        /* int64 database_id = 3; */
        if (message.databaseId !== "0")
            writer.tag(3, commonjs.WireType.Varint).int64(message.databaseId);
        /* string name = 4; */
        if (message.name !== "")
            writer.tag(4, commonjs.WireType.LengthDelimited).string(message.name);
        /* int64 size = 5; */
        if (message.size !== "0")
            writer.tag(5, commonjs.WireType.Varint).int64(message.size);
        /* google.protobuf.Timestamp created_at = 6; */
        if (message.createdAt)
            Timestamp.internalBinaryWrite(message.createdAt, writer.tag(6, commonjs.WireType.LengthDelimited).fork(), options).join();
        /* google.protobuf.StringValue digest = 7; */
        if (message.digest)
            StringValue.internalBinaryWrite(message.digest, writer.tag(7, commonjs.WireType.LengthDelimited).fork(), options).join();
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? commonjs.UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message github.actions.results.api.v1.ListArtifactsResponse.MonolithArtifact
 */
const ListArtifactsResponse_MonolithArtifact = new ListArtifactsResponse_MonolithArtifact$Type();
// @generated message type with reflection information, may provide speed optimized methods
class GetSignedArtifactURLRequest$Type extends commonjs.MessageType {
    constructor() {
        super("github.actions.results.api.v1.GetSignedArtifactURLRequest", [
            { no: 1, name: "workflow_run_backend_id", kind: "scalar", T: 9 /*ScalarType.STRING*/ },
            { no: 2, name: "workflow_job_run_backend_id", kind: "scalar", T: 9 /*ScalarType.STRING*/ },
            { no: 3, name: "name", kind: "scalar", T: 9 /*ScalarType.STRING*/ }
        ]);
    }
    create(value) {
        const message = { workflowRunBackendId: "", workflowJobRunBackendId: "", name: "" };
        globalThis.Object.defineProperty(message, commonjs.MESSAGE_TYPE, { enumerable: false, value: this });
        if (value !== undefined)
            (0,commonjs.reflectionMergePartial)(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target !== null && target !== void 0 ? target : this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* string workflow_run_backend_id */ 1:
                    message.workflowRunBackendId = reader.string();
                    break;
                case /* string workflow_job_run_backend_id */ 2:
                    message.workflowJobRunBackendId = reader.string();
                    break;
                case /* string name */ 3:
                    message.name = reader.string();
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? commonjs.UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* string workflow_run_backend_id = 1; */
        if (message.workflowRunBackendId !== "")
            writer.tag(1, commonjs.WireType.LengthDelimited).string(message.workflowRunBackendId);
        /* string workflow_job_run_backend_id = 2; */
        if (message.workflowJobRunBackendId !== "")
            writer.tag(2, commonjs.WireType.LengthDelimited).string(message.workflowJobRunBackendId);
        /* string name = 3; */
        if (message.name !== "")
            writer.tag(3, commonjs.WireType.LengthDelimited).string(message.name);
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? commonjs.UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message github.actions.results.api.v1.GetSignedArtifactURLRequest
 */
const artifact_GetSignedArtifactURLRequest = new GetSignedArtifactURLRequest$Type();
// @generated message type with reflection information, may provide speed optimized methods
class GetSignedArtifactURLResponse$Type extends commonjs.MessageType {
    constructor() {
        super("github.actions.results.api.v1.GetSignedArtifactURLResponse", [
            { no: 1, name: "signed_url", kind: "scalar", T: 9 /*ScalarType.STRING*/ }
        ]);
    }
    create(value) {
        const message = { signedUrl: "" };
        globalThis.Object.defineProperty(message, commonjs.MESSAGE_TYPE, { enumerable: false, value: this });
        if (value !== undefined)
            (0,commonjs.reflectionMergePartial)(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target !== null && target !== void 0 ? target : this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* string signed_url */ 1:
                    message.signedUrl = reader.string();
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? commonjs.UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* string signed_url = 1; */
        if (message.signedUrl !== "")
            writer.tag(1, commonjs.WireType.LengthDelimited).string(message.signedUrl);
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? commonjs.UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message github.actions.results.api.v1.GetSignedArtifactURLResponse
 */
const artifact_GetSignedArtifactURLResponse = new GetSignedArtifactURLResponse$Type();
// @generated message type with reflection information, may provide speed optimized methods
class DeleteArtifactRequest$Type extends commonjs.MessageType {
    constructor() {
        super("github.actions.results.api.v1.DeleteArtifactRequest", [
            { no: 1, name: "workflow_run_backend_id", kind: "scalar", T: 9 /*ScalarType.STRING*/ },
            { no: 2, name: "workflow_job_run_backend_id", kind: "scalar", T: 9 /*ScalarType.STRING*/ },
            { no: 3, name: "name", kind: "scalar", T: 9 /*ScalarType.STRING*/ }
        ]);
    }
    create(value) {
        const message = { workflowRunBackendId: "", workflowJobRunBackendId: "", name: "" };
        globalThis.Object.defineProperty(message, commonjs.MESSAGE_TYPE, { enumerable: false, value: this });
        if (value !== undefined)
            (0,commonjs.reflectionMergePartial)(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target !== null && target !== void 0 ? target : this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* string workflow_run_backend_id */ 1:
                    message.workflowRunBackendId = reader.string();
                    break;
                case /* string workflow_job_run_backend_id */ 2:
                    message.workflowJobRunBackendId = reader.string();
                    break;
                case /* string name */ 3:
                    message.name = reader.string();
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? commonjs.UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* string workflow_run_backend_id = 1; */
        if (message.workflowRunBackendId !== "")
            writer.tag(1, commonjs.WireType.LengthDelimited).string(message.workflowRunBackendId);
        /* string workflow_job_run_backend_id = 2; */
        if (message.workflowJobRunBackendId !== "")
            writer.tag(2, commonjs.WireType.LengthDelimited).string(message.workflowJobRunBackendId);
        /* string name = 3; */
        if (message.name !== "")
            writer.tag(3, commonjs.WireType.LengthDelimited).string(message.name);
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? commonjs.UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message github.actions.results.api.v1.DeleteArtifactRequest
 */
const artifact_DeleteArtifactRequest = new DeleteArtifactRequest$Type();
// @generated message type with reflection information, may provide speed optimized methods
class DeleteArtifactResponse$Type extends commonjs.MessageType {
    constructor() {
        super("github.actions.results.api.v1.DeleteArtifactResponse", [
            { no: 1, name: "ok", kind: "scalar", T: 8 /*ScalarType.BOOL*/ },
            { no: 2, name: "artifact_id", kind: "scalar", T: 3 /*ScalarType.INT64*/ }
        ]);
    }
    create(value) {
        const message = { ok: false, artifactId: "0" };
        globalThis.Object.defineProperty(message, commonjs.MESSAGE_TYPE, { enumerable: false, value: this });
        if (value !== undefined)
            (0,commonjs.reflectionMergePartial)(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target !== null && target !== void 0 ? target : this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* bool ok */ 1:
                    message.ok = reader.bool();
                    break;
                case /* int64 artifact_id */ 2:
                    message.artifactId = reader.int64().toString();
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? commonjs.UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* bool ok = 1; */
        if (message.ok !== false)
            writer.tag(1, commonjs.WireType.Varint).bool(message.ok);
        /* int64 artifact_id = 2; */
        if (message.artifactId !== "0")
            writer.tag(2, commonjs.WireType.Varint).int64(message.artifactId);
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? commonjs.UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message github.actions.results.api.v1.DeleteArtifactResponse
 */
const artifact_DeleteArtifactResponse = new DeleteArtifactResponse$Type();
/**
 * @generated ServiceType for protobuf service github.actions.results.api.v1.ArtifactService
 */
const ArtifactService = new build_commonjs/* ServiceType */.C0("github.actions.results.api.v1.ArtifactService", [
    { name: "CreateArtifact", options: {}, I: artifact_CreateArtifactRequest, O: artifact_CreateArtifactResponse },
    { name: "FinalizeArtifact", options: {}, I: artifact_FinalizeArtifactRequest, O: artifact_FinalizeArtifactResponse },
    { name: "ListArtifacts", options: {}, I: artifact_ListArtifactsRequest, O: artifact_ListArtifactsResponse },
    { name: "GetSignedArtifactURL", options: {}, I: artifact_GetSignedArtifactURLRequest, O: artifact_GetSignedArtifactURLResponse },
    { name: "DeleteArtifact", options: {}, I: artifact_DeleteArtifactRequest, O: artifact_DeleteArtifactResponse }
]);
//# sourceMappingURL=artifact.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/generated/results/api/v1/artifact.twirp-client.js

class ArtifactServiceClientJSON {
    constructor(rpc) {
        this.rpc = rpc;
        this.CreateArtifact.bind(this);
        this.FinalizeArtifact.bind(this);
        this.ListArtifacts.bind(this);
        this.GetSignedArtifactURL.bind(this);
        this.DeleteArtifact.bind(this);
    }
    CreateArtifact(request) {
        const data = artifact_CreateArtifactRequest.toJson(request, {
            useProtoFieldName: true,
            emitDefaultValues: false,
        });
        const promise = this.rpc.request("github.actions.results.api.v1.ArtifactService", "CreateArtifact", "application/json", data);
        return promise.then((data) => artifact_CreateArtifactResponse.fromJson(data, {
            ignoreUnknownFields: true,
        }));
    }
    FinalizeArtifact(request) {
        const data = artifact_FinalizeArtifactRequest.toJson(request, {
            useProtoFieldName: true,
            emitDefaultValues: false,
        });
        const promise = this.rpc.request("github.actions.results.api.v1.ArtifactService", "FinalizeArtifact", "application/json", data);
        return promise.then((data) => artifact_FinalizeArtifactResponse.fromJson(data, {
            ignoreUnknownFields: true,
        }));
    }
    ListArtifacts(request) {
        const data = artifact_ListArtifactsRequest.toJson(request, {
            useProtoFieldName: true,
            emitDefaultValues: false,
        });
        const promise = this.rpc.request("github.actions.results.api.v1.ArtifactService", "ListArtifacts", "application/json", data);
        return promise.then((data) => artifact_ListArtifactsResponse.fromJson(data, { ignoreUnknownFields: true }));
    }
    GetSignedArtifactURL(request) {
        const data = artifact_GetSignedArtifactURLRequest.toJson(request, {
            useProtoFieldName: true,
            emitDefaultValues: false,
        });
        const promise = this.rpc.request("github.actions.results.api.v1.ArtifactService", "GetSignedArtifactURL", "application/json", data);
        return promise.then((data) => artifact_GetSignedArtifactURLResponse.fromJson(data, {
            ignoreUnknownFields: true,
        }));
    }
    DeleteArtifact(request) {
        const data = artifact_DeleteArtifactRequest.toJson(request, {
            useProtoFieldName: true,
            emitDefaultValues: false,
        });
        const promise = this.rpc.request("github.actions.results.api.v1.ArtifactService", "DeleteArtifact", "application/json", data);
        return promise.then((data) => artifact_DeleteArtifactResponse.fromJson(data, {
            ignoreUnknownFields: true,
        }));
    }
}
class ArtifactServiceClientProtobuf {
    constructor(rpc) {
        this.rpc = rpc;
        this.CreateArtifact.bind(this);
        this.FinalizeArtifact.bind(this);
        this.ListArtifacts.bind(this);
        this.GetSignedArtifactURL.bind(this);
        this.DeleteArtifact.bind(this);
    }
    CreateArtifact(request) {
        const data = CreateArtifactRequest.toBinary(request);
        const promise = this.rpc.request("github.actions.results.api.v1.ArtifactService", "CreateArtifact", "application/protobuf", data);
        return promise.then((data) => CreateArtifactResponse.fromBinary(data));
    }
    FinalizeArtifact(request) {
        const data = FinalizeArtifactRequest.toBinary(request);
        const promise = this.rpc.request("github.actions.results.api.v1.ArtifactService", "FinalizeArtifact", "application/protobuf", data);
        return promise.then((data) => FinalizeArtifactResponse.fromBinary(data));
    }
    ListArtifacts(request) {
        const data = ListArtifactsRequest.toBinary(request);
        const promise = this.rpc.request("github.actions.results.api.v1.ArtifactService", "ListArtifacts", "application/protobuf", data);
        return promise.then((data) => ListArtifactsResponse.fromBinary(data));
    }
    GetSignedArtifactURL(request) {
        const data = GetSignedArtifactURLRequest.toBinary(request);
        const promise = this.rpc.request("github.actions.results.api.v1.ArtifactService", "GetSignedArtifactURL", "application/protobuf", data);
        return promise.then((data) => GetSignedArtifactURLResponse.fromBinary(data));
    }
    DeleteArtifact(request) {
        const data = DeleteArtifactRequest.toBinary(request);
        const promise = this.rpc.request("github.actions.results.api.v1.ArtifactService", "DeleteArtifact", "application/protobuf", data);
        return promise.then((data) => DeleteArtifactResponse.fromBinary(data));
    }
}
//# sourceMappingURL=artifact.twirp-client.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/generated/index.js




//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/upload/retention.js


function getExpiration(retentionDays) {
    if (!retentionDays) {
        return undefined;
    }
    const maxRetentionDays = getRetentionDays();
    if (maxRetentionDays && maxRetentionDays < retentionDays) {
        warning(`Retention days cannot be greater than the maximum allowed retention set within the repository. Using ${maxRetentionDays} instead.`);
        retentionDays = maxRetentionDays;
    }
    const expirationDate = new Date();
    expirationDate.setDate(expirationDate.getDate() + retentionDays);
    return Timestamp.fromDate(expirationDate);
}
function getRetentionDays() {
    const retentionDays = process.env['GITHUB_RETENTION_DAYS'];
    if (!retentionDays) {
        return undefined;
    }
    const days = parseInt(retentionDays);
    if (isNaN(days)) {
        return undefined;
    }
    return days;
}
//# sourceMappingURL=retention.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/upload/path-and-artifact-name-validation.js

/**
 * Invalid characters that cannot be in the artifact name or an uploaded file. Will be rejected
 * from the server if attempted to be sent over. These characters are not allowed due to limitations with certain
 * file systems such as NTFS. To maintain platform-agnostic behavior, all characters that are not supported by an
 * individual filesystem/platform will not be supported on all fileSystems/platforms
 *
 * FilePaths can include characters such as \ and / which are not permitted in the artifact name alone
 */
const invalidArtifactFilePathCharacters = new Map([
    ['"', ' Double quote "'],
    [':', ' Colon :'],
    ['<', ' Less than <'],
    ['>', ' Greater than >'],
    ['|', ' Vertical bar |'],
    ['*', ' Asterisk *'],
    ['?', ' Question mark ?'],
    ['\r', ' Carriage return \\r'],
    ['\n', ' Line feed \\n']
]);
const invalidArtifactNameCharacters = new Map([
    ...invalidArtifactFilePathCharacters,
    ['\\', ' Backslash \\'],
    ['/', ' Forward slash /']
]);
/**
 * Validates the name of the artifact to check to make sure there are no illegal characters
 */
function validateArtifactName(name) {
    if (!name) {
        throw new Error(`Provided artifact name input during validation is empty`);
    }
    for (const [invalidCharacterKey, errorMessageForCharacter] of invalidArtifactNameCharacters) {
        if (name.includes(invalidCharacterKey)) {
            throw new Error(`The artifact name is not valid: ${name}. Contains the following character: ${errorMessageForCharacter}
          
Invalid characters include: ${Array.from(invalidArtifactNameCharacters.values()).toString()}
          
These characters are not allowed in the artifact name due to limitations with certain file systems such as NTFS. To maintain file system agnostic behavior, these characters are intentionally not allowed to prevent potential problems with downloads on different file systems.`);
        }
    }
    info(`Artifact name is valid!`);
}
/**
 * Validates file paths to check for any illegal characters that can cause problems on different file systems
 */
function validateFilePath(path) {
    if (!path) {
        throw new Error(`Provided file path input during validation is empty`);
    }
    for (const [invalidCharacterKey, errorMessageForCharacter] of invalidArtifactFilePathCharacters) {
        if (path.includes(invalidCharacterKey)) {
            throw new Error(`The path for one of the files in artifact is not valid: ${path}. Contains the following character: ${errorMessageForCharacter}
          
Invalid characters include: ${Array.from(invalidArtifactFilePathCharacters.values()).toString()}
          
The following characters are not allowed in files that are uploaded due to limitations with certain file systems such as NTFS. To maintain file system agnostic behavior, these characters are intentionally not allowed to prevent potential problems with downloads on different file systems.
          `);
        }
    }
}
//# sourceMappingURL=path-and-artifact-name-validation.js.map
// EXTERNAL MODULE: ./node_modules/@actions/artifact/lib/internal/shared/package-version.cjs
var package_version = __nccwpck_require__(9002);
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/shared/user-agent.js

/**
 * Ensure that this User Agent String is used in all HTTP calls so that we can monitor telemetry between different versions of this package
 */
function getUserAgentString() {
    return `@actions/artifact-${package_version.version}`;
}
//# sourceMappingURL=user-agent.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/shared/errors.js
class FilesNotFoundError extends Error {
    constructor(files = []) {
        let message = 'No files were found to upload';
        if (files.length > 0) {
            message += `: ${files.join(', ')}`;
        }
        super(message);
        this.files = files;
        this.name = 'FilesNotFoundError';
    }
}
class InvalidResponseError extends Error {
    constructor(message) {
        super(message);
        this.name = 'InvalidResponseError';
    }
}
class ArtifactNotFoundError extends Error {
    constructor(message = 'Artifact not found') {
        super(message);
        this.name = 'ArtifactNotFoundError';
    }
}
class GHESNotSupportedError extends Error {
    constructor(message = '@actions/artifact v2.0.0+, upload-artifact@v4+ and download-artifact@v4+ are not currently supported on GHES.') {
        super(message);
        this.name = 'GHESNotSupportedError';
    }
}
class NetworkError extends Error {
    constructor(code) {
        const message = `Unable to make request: ${code}\nIf you are using self-hosted runners, please make sure your runner has access to all GitHub endpoints: https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/about-self-hosted-runners#communication-between-self-hosted-runners-and-github`;
        super(message);
        this.code = code;
        this.name = 'NetworkError';
    }
}
NetworkError.isNetworkErrorCode = (code) => {
    if (!code)
        return false;
    return [
        'ECONNRESET',
        'ENOTFOUND',
        'ETIMEDOUT',
        'ECONNREFUSED',
        'EHOSTUNREACH'
    ].includes(code);
};
class UsageError extends Error {
    constructor() {
        const message = `Artifact storage quota has been hit. Unable to upload any new artifacts. Usage is recalculated every 6-12 hours.\nMore info on storage limits: https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions#calculating-minute-and-storage-spending`;
        super(message);
        this.name = 'UsageError';
    }
}
UsageError.isUsageErrorMessage = (msg) => {
    if (!msg)
        return false;
    return msg.includes('insufficient usage');
};
//# sourceMappingURL=errors.js.map
;// CONCATENATED MODULE: ./node_modules/jwt-decode/build/esm/index.js
class InvalidTokenError extends Error {
}
InvalidTokenError.prototype.name = "InvalidTokenError";
function b64DecodeUnicode(str) {
    return decodeURIComponent(atob(str).replace(/(.)/g, (m, p) => {
        let code = p.charCodeAt(0).toString(16).toUpperCase();
        if (code.length < 2) {
            code = "0" + code;
        }
        return "%" + code;
    }));
}
function base64UrlDecode(str) {
    let output = str.replace(/-/g, "+").replace(/_/g, "/");
    switch (output.length % 4) {
        case 0:
            break;
        case 2:
            output += "==";
            break;
        case 3:
            output += "=";
            break;
        default:
            throw new Error("base64 string is not of the correct length");
    }
    try {
        return b64DecodeUnicode(output);
    }
    catch (err) {
        return atob(output);
    }
}
function jwtDecode(token, options) {
    if (typeof token !== "string") {
        throw new InvalidTokenError("Invalid token specified: must be a string");
    }
    options || (options = {});
    const pos = options.header === true ? 0 : 1;
    const part = token.split(".")[pos];
    if (typeof part !== "string") {
        throw new InvalidTokenError(`Invalid token specified: missing part #${pos + 1}`);
    }
    let decoded;
    try {
        decoded = base64UrlDecode(part);
    }
    catch (e) {
        throw new InvalidTokenError(`Invalid token specified: invalid base64 for part #${pos + 1} (${e.message})`);
    }
    try {
        return JSON.parse(decoded);
    }
    catch (e) {
        throw new InvalidTokenError(`Invalid token specified: invalid json for part #${pos + 1} (${e.message})`);
    }
}

;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/shared/util.js




const InvalidJwtError = new Error('Failed to get backend IDs: The provided JWT token is invalid and/or missing claims');
// uses the JWT token claims to get the
// workflow run and workflow job run backend ids
function getBackendIdsFromToken() {
    const token = getRuntimeToken();
    const decoded = jwtDecode(token);
    if (!decoded.scp) {
        throw InvalidJwtError;
    }
    /*
     * example decoded:
     * {
     *   scp: "Actions.ExampleScope Actions.Results:ce7f54c7-61c7-4aae-887f-30da475f5f1a:ca395085-040a-526b-2ce8-bdc85f692774"
     * }
     */
    const scpParts = decoded.scp.split(' ');
    if (scpParts.length === 0) {
        throw InvalidJwtError;
    }
    /*
     * example scpParts:
     * ["Actions.ExampleScope", "Actions.Results:ce7f54c7-61c7-4aae-887f-30da475f5f1a:ca395085-040a-526b-2ce8-bdc85f692774"]
     */
    for (const scopes of scpParts) {
        const scopeParts = scopes.split(':');
        if ((scopeParts === null || scopeParts === void 0 ? void 0 : scopeParts[0]) !== 'Actions.Results') {
            // not the Actions.Results scope
            continue;
        }
        /*
         * example scopeParts:
         * ["Actions.Results", "ce7f54c7-61c7-4aae-887f-30da475f5f1a", "ca395085-040a-526b-2ce8-bdc85f692774"]
         */
        if (scopeParts.length !== 3) {
            // missing expected number of claims
            throw InvalidJwtError;
        }
        const ids = {
            workflowRunBackendId: scopeParts[1],
            workflowJobRunBackendId: scopeParts[2]
        };
        core_debug(`Workflow Run Backend ID: ${ids.workflowRunBackendId}`);
        core_debug(`Workflow Job Run Backend ID: ${ids.workflowJobRunBackendId}`);
        return ids;
    }
    throw InvalidJwtError;
}
/**
 * Masks the `sig` parameter in a URL and sets it as a secret.
 *
 * @param url - The URL containing the signature parameter to mask
 * @remarks
 * This function attempts to parse the provided URL and identify the 'sig' query parameter.
 * If found, it registers both the raw and URL-encoded signature values as secrets using
 * the Actions `setSecret` API, which prevents them from being displayed in logs.
 *
 * The function handles errors gracefully if URL parsing fails, logging them as debug messages.
 *
 * @example
 * ```typescript
 * // Mask a signature in an Azure SAS token URL
 * maskSigUrl('https://example.blob.core.windows.net/container/file.txt?sig=abc123&se=2023-01-01');
 * ```
 */
function maskSigUrl(url) {
    if (!url)
        return;
    try {
        const parsedUrl = new URL(url);
        const signature = parsedUrl.searchParams.get('sig');
        if (signature) {
            core_setSecret(signature);
            core_setSecret(encodeURIComponent(signature));
        }
    }
    catch (error) {
        core_debug(`Failed to parse URL: ${url} ${error instanceof Error ? error.message : String(error)}`);
    }
}
/**
 * Masks sensitive information in URLs containing signature parameters.
 * Currently supports masking 'sig' parameters in the 'signed_upload_url'
 * and 'signed_download_url' properties of the provided object.
 *
 * @param body - The object should contain a signature
 * @remarks
 * This function extracts URLs from the object properties and calls maskSigUrl
 * on each one to redact sensitive signature information. The function doesn't
 * modify the original object; it only marks the signatures as secrets for
 * logging purposes.
 *
 * @example
 * ```typescript
 * const responseBody = {
 *   signed_upload_url: 'https://example.com?sig=abc123',
 *   signed_download_url: 'https://example.com?sig=def456'
 * };
 * maskSecretUrls(responseBody);
 * ```
 */
function maskSecretUrls(body) {
    if (typeof body !== 'object' || body === null) {
        core_debug('body is not an object or is null');
        return;
    }
    if ('signed_upload_url' in body &&
        typeof body.signed_upload_url === 'string') {
        maskSigUrl(body.signed_upload_url);
    }
    if ('signed_url' in body && typeof body.signed_url === 'string') {
        maskSigUrl(body.signed_url);
    }
}
//# sourceMappingURL=util.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/shared/artifact-twirp-client.js
var artifact_twirp_client_awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};








class ArtifactHttpClient {
    constructor(userAgent, maxAttempts, baseRetryIntervalMilliseconds, retryMultiplier) {
        this.maxAttempts = 5;
        this.baseRetryIntervalMilliseconds = 3000;
        this.retryMultiplier = 1.5;
        const token = getRuntimeToken();
        this.baseUrl = getResultsServiceUrl();
        if (maxAttempts) {
            this.maxAttempts = maxAttempts;
        }
        if (baseRetryIntervalMilliseconds) {
            this.baseRetryIntervalMilliseconds = baseRetryIntervalMilliseconds;
        }
        if (retryMultiplier) {
            this.retryMultiplier = retryMultiplier;
        }
        this.httpClient = new lib_HttpClient(userAgent, [
            new auth_BearerCredentialHandler(token)
        ]);
    }
    // This function satisfies the Rpc interface. It is compatible with the JSON
    // JSON generated client.
    request(service, method, contentType, data) {
        return artifact_twirp_client_awaiter(this, void 0, void 0, function* () {
            const url = new URL(`/twirp/${service}/${method}`, this.baseUrl).href;
            core_debug(`[Request] ${method} ${url}`);
            const headers = {
                'Content-Type': contentType
            };
            try {
                const { body } = yield this.retryableRequest(() => artifact_twirp_client_awaiter(this, void 0, void 0, function* () { return this.httpClient.post(url, JSON.stringify(data), headers); }));
                return body;
            }
            catch (error) {
                throw new Error(`Failed to ${method}: ${error.message}`);
            }
        });
    }
    retryableRequest(operation) {
        return artifact_twirp_client_awaiter(this, void 0, void 0, function* () {
            let attempt = 0;
            let errorMessage = '';
            let rawBody = '';
            while (attempt < this.maxAttempts) {
                let isRetryable = false;
                try {
                    const response = yield operation();
                    const statusCode = response.message.statusCode;
                    rawBody = yield response.readBody();
                    core_debug(`[Response] - ${response.message.statusCode}`);
                    core_debug(`Headers: ${JSON.stringify(response.message.headers, null, 2)}`);
                    const body = JSON.parse(rawBody);
                    maskSecretUrls(body);
                    core_debug(`Body: ${JSON.stringify(body, null, 2)}`);
                    if (this.isSuccessStatusCode(statusCode)) {
                        return { response, body };
                    }
                    isRetryable = this.isRetryableHttpStatusCode(statusCode);
                    errorMessage = `Failed request: (${statusCode}) ${response.message.statusMessage}`;
                    if (body.msg) {
                        if (UsageError.isUsageErrorMessage(body.msg)) {
                            throw new UsageError();
                        }
                        errorMessage = `${errorMessage}: ${body.msg}`;
                    }
                }
                catch (error) {
                    if (error instanceof SyntaxError) {
                        core_debug(`Raw Body: ${rawBody}`);
                    }
                    if (error instanceof UsageError) {
                        throw error;
                    }
                    if (NetworkError.isNetworkErrorCode(error === null || error === void 0 ? void 0 : error.code)) {
                        throw new NetworkError(error === null || error === void 0 ? void 0 : error.code);
                    }
                    isRetryable = true;
                    errorMessage = error.message;
                }
                if (!isRetryable) {
                    throw new Error(`Received non-retryable error: ${errorMessage}`);
                }
                if (attempt + 1 === this.maxAttempts) {
                    throw new Error(`Failed to make request after ${this.maxAttempts} attempts: ${errorMessage}`);
                }
                const retryTimeMilliseconds = this.getExponentialRetryTimeMilliseconds(attempt);
                info(`Attempt ${attempt + 1} of ${this.maxAttempts} failed with error: ${errorMessage}. Retrying request in ${retryTimeMilliseconds} ms...`);
                yield this.sleep(retryTimeMilliseconds);
                attempt++;
            }
            throw new Error(`Request failed`);
        });
    }
    isSuccessStatusCode(statusCode) {
        if (!statusCode)
            return false;
        return statusCode >= 200 && statusCode < 300;
    }
    isRetryableHttpStatusCode(statusCode) {
        if (!statusCode)
            return false;
        const retryableStatusCodes = [
            HttpCodes.BadGateway,
            HttpCodes.GatewayTimeout,
            HttpCodes.InternalServerError,
            HttpCodes.ServiceUnavailable,
            HttpCodes.TooManyRequests
        ];
        return retryableStatusCodes.includes(statusCode);
    }
    sleep(milliseconds) {
        return artifact_twirp_client_awaiter(this, void 0, void 0, function* () {
            return new Promise(resolve => setTimeout(resolve, milliseconds));
        });
    }
    getExponentialRetryTimeMilliseconds(attempt) {
        if (attempt < 0) {
            throw new Error('attempt should be a positive integer');
        }
        if (attempt === 0) {
            return this.baseRetryIntervalMilliseconds;
        }
        const minTime = this.baseRetryIntervalMilliseconds * Math.pow(this.retryMultiplier, attempt);
        const maxTime = minTime * this.retryMultiplier;
        // returns a random number between minTime and maxTime (exclusive)
        return Math.trunc(Math.random() * (maxTime - minTime) + minTime);
    }
}
function internalArtifactTwirpClient(options) {
    const client = new ArtifactHttpClient(getUserAgentString(), options === null || options === void 0 ? void 0 : options.maxAttempts, options === null || options === void 0 ? void 0 : options.retryIntervalMs, options === null || options === void 0 ? void 0 : options.retryMultiplier);
    return new ArtifactServiceClientJSON(client);
}
//# sourceMappingURL=artifact-twirp-client.js.map
;// CONCATENATED MODULE: ./node_modules/@actions/artifact/lib/internal/upload/upload-zip-specification.js




/**
 * Checks if a root directory exists and is valid
 * @param rootDirectory an absolute root directory path common to all input files that that will be trimmed from the final zip structure
 */
function validateRootDirectory(rootDirectory) {
    if (!external_fs_.existsSync(rootDirectory)) {
        throw new Error(`The provided rootDirectory ${rootDirectory} does not exist`);
    }
    if (!external_fs_.statSync(rootDirectory).isDirectory()) {
        throw new Error(`The provided rootDirectory ${rootDirectory} is not a valid directory`);
    }
    info(`Root directory input is valid!`);
}
/**
 * Creates a specification that describes how a zip file will be created for a set of input files
 * @param filesToZip a list of file that should be included in the zip
 * @param rootDirectory an absolute root directory path common to all input files that that will be trimmed from the final zip structure
 */
function getUploadZipSpecification(filesToZip, rootDirectory) {
    const specification = [];
    // Normalize and resolve, this allows for either absolute or relative paths to be used
    rootDirectory = (0,external_path_.normalize)(rootDirectory);
    rootDirectory = (0,external_path_.resolve)(rootDirectory);
    /*
       Example
       
       Input:
         rootDirectory: '/home/user/files/plz-upload'
         artifactFiles: [
           '/home/user/files/plz-upload/file1.txt',
           '/home/user/files/plz-upload/file2.txt',
           '/home/user/files/plz-upload/dir/file3.txt'
         ]
       
       Output:
         specifications: [
           ['/home/user/files/plz-upload/file1.txt', '/file1.txt'],
           ['/home/user/files/plz-upload/file1.txt', '/file2.txt'],
           ['/home/user/files/plz-upload/file1.txt', '/dir/file3.txt']
         ]
  
        The final zip that is later uploaded will look like this:
  
        my-artifact.zip
          - file.txt
          - file2.txt
          - dir/
            - file3.txt
    */
    for (let file of filesToZip) {
        const stats = external_fs_.lstatSync(file, { throwIfNoEntry: false });
        if (!stats) {
            throw new Error(`File ${file} does not exist`);
        }
        if (!stats.isDirectory()) {
            // Normalize and resolve, this allows for either absolute or relative paths to be used
            file = (0,external_path_.normalize)(file);
            file = (0,external_path_.resolve)(file);
            if (!file.startsWith(rootDirectory)) {
                throw new Error(`The rootDirectory: ${rootDirectory} is not a parent directory of the file: ${file}`);
            }
            // Check for forbidden characters in file paths that may cause ambiguous behavior if downloaded on different file systems
            const uploadPath = file.replace(rootDirectory, '');
            validateFilePath(uploadPath);
            specification.push({
                sourcePath: file,
                destinationPath: uploadPath,
                stats
            });
        }
        else {
            // Empty directory
            const directoryPath = file.replace(rootDirectory, '');
            validateFilePath(directoryPath);
            specification.push({
                sourcePath: null,
                destinationPath: directoryPath,
                stats
            });
        }
    }
    return specification;
}
//# sourceMappingURL=upload-zip-specification.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/abort-controller/AbortError.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * This error is thrown when an asynchronous operation has been aborted.
 * Check for this error by testing the `name` that the name property of the
 * error matches `"AbortError"`.
 *
 * @example
 * ```ts snippet:ReadmeSampleAbortError
 * import { AbortError } from "@typespec/ts-http-runtime";
 *
 * async function doAsyncWork(options: { abortSignal: AbortSignal }): Promise<void> {
 *   if (options.abortSignal.aborted) {
 *     throw new AbortError();
 *   }
 *
 *   // do async work
 * }
 *
 * const controller = new AbortController();
 * controller.abort();
 *
 * try {
 *   doAsyncWork({ abortSignal: controller.signal });
 * } catch (e) {
 *   if (e instanceof Error && e.name === "AbortError") {
 *     // handle abort error here.
 *   }
 * }
 * ```
 */
class AbortError extends Error {
    constructor(message) {
        super(message);
        this.name = "AbortError";
    }
}
//# sourceMappingURL=AbortError.js.map
;// CONCATENATED MODULE: external "node:os"
const external_node_os_namespaceObject = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:os");
// EXTERNAL MODULE: external "node:util"
var external_node_util_ = __nccwpck_require__(7975);
;// CONCATENATED MODULE: external "node:process"
const external_node_process_namespaceObject = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:process");
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/logger/log.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



function log(message, ...args) {
    external_node_process_namespaceObject.stderr.write(`${external_node_util_.format(message, ...args)}${external_node_os_namespaceObject.EOL}`);
}
//# sourceMappingURL=log.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/logger/debug.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const debugEnvVariable = (typeof process !== "undefined" && process.env && process.env.DEBUG) || undefined;
let enabledString;
let enabledNamespaces = [];
let skippedNamespaces = [];
const debuggers = [];
if (debugEnvVariable) {
    enable(debugEnvVariable);
}
const debugObj = Object.assign((namespace) => {
    return createDebugger(namespace);
}, {
    enable,
    enabled,
    disable,
    log: log,
});
function enable(namespaces) {
    enabledString = namespaces;
    enabledNamespaces = [];
    skippedNamespaces = [];
    const namespaceList = namespaces.split(",").map((ns) => ns.trim());
    for (const ns of namespaceList) {
        if (ns.startsWith("-")) {
            skippedNamespaces.push(ns.substring(1));
        }
        else {
            enabledNamespaces.push(ns);
        }
    }
    for (const instance of debuggers) {
        instance.enabled = enabled(instance.namespace);
    }
}
function enabled(namespace) {
    if (namespace.endsWith("*")) {
        return true;
    }
    for (const skipped of skippedNamespaces) {
        if (namespaceMatches(namespace, skipped)) {
            return false;
        }
    }
    for (const enabledNamespace of enabledNamespaces) {
        if (namespaceMatches(namespace, enabledNamespace)) {
            return true;
        }
    }
    return false;
}
/**
 * Given a namespace, check if it matches a pattern.
 * Patterns only have a single wildcard character which is *.
 * The behavior of * is that it matches zero or more other characters.
 */
function namespaceMatches(namespace, patternToMatch) {
    // simple case, no pattern matching required
    if (patternToMatch.indexOf("*") === -1) {
        return namespace === patternToMatch;
    }
    let pattern = patternToMatch;
    // normalize successive * if needed
    if (patternToMatch.indexOf("**") !== -1) {
        const patternParts = [];
        let lastCharacter = "";
        for (const character of patternToMatch) {
            if (character === "*" && lastCharacter === "*") {
                continue;
            }
            else {
                lastCharacter = character;
                patternParts.push(character);
            }
        }
        pattern = patternParts.join("");
    }
    let namespaceIndex = 0;
    let patternIndex = 0;
    const patternLength = pattern.length;
    const namespaceLength = namespace.length;
    let lastWildcard = -1;
    let lastWildcardNamespace = -1;
    while (namespaceIndex < namespaceLength && patternIndex < patternLength) {
        if (pattern[patternIndex] === "*") {
            lastWildcard = patternIndex;
            patternIndex++;
            if (patternIndex === patternLength) {
                // if wildcard is the last character, it will match the remaining namespace string
                return true;
            }
            // now we let the wildcard eat characters until we match the next literal in the pattern
            while (namespace[namespaceIndex] !== pattern[patternIndex]) {
                namespaceIndex++;
                // reached the end of the namespace without a match
                if (namespaceIndex === namespaceLength) {
                    return false;
                }
            }
            // now that we have a match, let's try to continue on
            // however, it's possible we could find a later match
            // so keep a reference in case we have to backtrack
            lastWildcardNamespace = namespaceIndex;
            namespaceIndex++;
            patternIndex++;
            continue;
        }
        else if (pattern[patternIndex] === namespace[namespaceIndex]) {
            // simple case: literal pattern matches so keep going
            patternIndex++;
            namespaceIndex++;
        }
        else if (lastWildcard >= 0) {
            // special case: we don't have a literal match, but there is a previous wildcard
            // which we can backtrack to and try having the wildcard eat the match instead
            patternIndex = lastWildcard + 1;
            namespaceIndex = lastWildcardNamespace + 1;
            // we've reached the end of the namespace without a match
            if (namespaceIndex === namespaceLength) {
                return false;
            }
            // similar to the previous logic, let's keep going until we find the next literal match
            while (namespace[namespaceIndex] !== pattern[patternIndex]) {
                namespaceIndex++;
                if (namespaceIndex === namespaceLength) {
                    return false;
                }
            }
            lastWildcardNamespace = namespaceIndex;
            namespaceIndex++;
            patternIndex++;
            continue;
        }
        else {
            return false;
        }
    }
    const namespaceDone = namespaceIndex === namespace.length;
    const patternDone = patternIndex === pattern.length;
    // this is to detect the case of an unneeded final wildcard
    // e.g. the pattern `ab*` should match the string `ab`
    const trailingWildCard = patternIndex === pattern.length - 1 && pattern[patternIndex] === "*";
    return namespaceDone && (patternDone || trailingWildCard);
}
function disable() {
    const result = enabledString || "";
    enable("");
    return result;
}
function createDebugger(namespace) {
    const newDebugger = Object.assign(debug, {
        enabled: enabled(namespace),
        destroy,
        log: debugObj.log,
        namespace,
        extend,
    });
    function debug(...args) {
        if (!newDebugger.enabled) {
            return;
        }
        if (args.length > 0) {
            args[0] = `${namespace} ${args[0]}`;
        }
        newDebugger.log(...args);
    }
    debuggers.push(newDebugger);
    return newDebugger;
}
function destroy() {
    const index = debuggers.indexOf(this);
    if (index >= 0) {
        debuggers.splice(index, 1);
        return true;
    }
    return false;
}
function extend(namespace) {
    const newDebugger = createDebugger(`${this.namespace}:${namespace}`);
    newDebugger.log = this.log;
    return newDebugger;
}
/* harmony default export */ const logger_debug = (debugObj);
//# sourceMappingURL=debug.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/logger/logger.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const TYPESPEC_RUNTIME_LOG_LEVELS = ["verbose", "info", "warning", "error"];
const levelMap = {
    verbose: 400,
    info: 300,
    warning: 200,
    error: 100,
};
function patchLogMethod(parent, child) {
    child.log = (...args) => {
        parent.log(...args);
    };
}
function isTypeSpecRuntimeLogLevel(level) {
    return TYPESPEC_RUNTIME_LOG_LEVELS.includes(level);
}
/**
 * Creates a logger context base on the provided options.
 * @param options - The options for creating a logger context.
 * @returns The logger context.
 */
function createLoggerContext(options) {
    const registeredLoggers = new Set();
    const logLevelFromEnv = (typeof process !== "undefined" && process.env && process.env[options.logLevelEnvVarName]) ||
        undefined;
    let logLevel;
    const clientLogger = logger_debug(options.namespace);
    clientLogger.log = (...args) => {
        logger_debug.log(...args);
    };
    function contextSetLogLevel(level) {
        if (level && !isTypeSpecRuntimeLogLevel(level)) {
            throw new Error(`Unknown log level '${level}'. Acceptable values: ${TYPESPEC_RUNTIME_LOG_LEVELS.join(",")}`);
        }
        logLevel = level;
        const enabledNamespaces = [];
        for (const logger of registeredLoggers) {
            if (shouldEnable(logger)) {
                enabledNamespaces.push(logger.namespace);
            }
        }
        logger_debug.enable(enabledNamespaces.join(","));
    }
    if (logLevelFromEnv) {
        // avoid calling setLogLevel because we don't want a mis-set environment variable to crash
        if (isTypeSpecRuntimeLogLevel(logLevelFromEnv)) {
            contextSetLogLevel(logLevelFromEnv);
        }
        else {
            console.error(`${options.logLevelEnvVarName} set to unknown log level '${logLevelFromEnv}'; logging is not enabled. Acceptable values: ${TYPESPEC_RUNTIME_LOG_LEVELS.join(", ")}.`);
        }
    }
    function shouldEnable(logger) {
        return Boolean(logLevel && levelMap[logger.level] <= levelMap[logLevel]);
    }
    function createLogger(parent, level) {
        const logger = Object.assign(parent.extend(level), {
            level,
        });
        patchLogMethod(parent, logger);
        if (shouldEnable(logger)) {
            const enabledNamespaces = logger_debug.disable();
            logger_debug.enable(enabledNamespaces + "," + logger.namespace);
        }
        registeredLoggers.add(logger);
        return logger;
    }
    function contextGetLogLevel() {
        return logLevel;
    }
    function contextCreateClientLogger(namespace) {
        const clientRootLogger = clientLogger.extend(namespace);
        patchLogMethod(clientLogger, clientRootLogger);
        return {
            error: createLogger(clientRootLogger, "error"),
            warning: createLogger(clientRootLogger, "warning"),
            info: createLogger(clientRootLogger, "info"),
            verbose: createLogger(clientRootLogger, "verbose"),
        };
    }
    return {
        setLogLevel: contextSetLogLevel,
        getLogLevel: contextGetLogLevel,
        createClientLogger: contextCreateClientLogger,
        logger: clientLogger,
    };
}
const context = createLoggerContext({
    logLevelEnvVarName: "TYPESPEC_RUNTIME_LOG_LEVEL",
    namespace: "typeSpecRuntime",
});
/**
 * Immediately enables logging at the specified log level. If no level is specified, logging is disabled.
 * @param level - The log level to enable for logging.
 * Options from most verbose to least verbose are:
 * - verbose
 * - info
 * - warning
 * - error
 */
// eslint-disable-next-line @typescript-eslint/no-redeclare
const TypeSpecRuntimeLogger = context.logger;
/**
 * Retrieves the currently specified log level.
 */
function setLogLevel(logLevel) {
    context.setLogLevel(logLevel);
}
/**
 * Retrieves the currently specified log level.
 */
function getLogLevel() {
    return context.getLogLevel();
}
/**
 * Creates a logger for use by the SDKs that inherits from `TypeSpecRuntimeLogger`.
 * @param namespace - The name of the SDK package.
 * @hidden
 */
function createClientLogger(namespace) {
    return context.createClientLogger(namespace);
}
//# sourceMappingURL=logger.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/httpHeaders.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
function normalizeName(name) {
    return name.toLowerCase();
}
function* headerIterator(map) {
    for (const entry of map.values()) {
        yield [entry.name, entry.value];
    }
}
class HttpHeadersImpl {
    _headersMap;
    constructor(rawHeaders) {
        this._headersMap = new Map();
        if (rawHeaders) {
            for (const headerName of Object.keys(rawHeaders)) {
                this.set(headerName, rawHeaders[headerName]);
            }
        }
    }
    /**
     * Set a header in this collection with the provided name and value. The name is
     * case-insensitive.
     * @param name - The name of the header to set. This value is case-insensitive.
     * @param value - The value of the header to set.
     */
    set(name, value) {
        this._headersMap.set(normalizeName(name), { name, value: String(value).trim() });
    }
    /**
     * Get the header value for the provided header name, or undefined if no header exists in this
     * collection with the provided name.
     * @param name - The name of the header. This value is case-insensitive.
     */
    get(name) {
        return this._headersMap.get(normalizeName(name))?.value;
    }
    /**
     * Get whether or not this header collection contains a header entry for the provided header name.
     * @param name - The name of the header to set. This value is case-insensitive.
     */
    has(name) {
        return this._headersMap.has(normalizeName(name));
    }
    /**
     * Remove the header with the provided headerName.
     * @param name - The name of the header to remove.
     */
    delete(name) {
        this._headersMap.delete(normalizeName(name));
    }
    /**
     * Get the JSON object representation of this HTTP header collection.
     */
    toJSON(options = {}) {
        const result = {};
        if (options.preserveCase) {
            for (const entry of this._headersMap.values()) {
                result[entry.name] = entry.value;
            }
        }
        else {
            for (const [normalizedName, entry] of this._headersMap) {
                result[normalizedName] = entry.value;
            }
        }
        return result;
    }
    /**
     * Get the string representation of this HTTP header collection.
     */
    toString() {
        return JSON.stringify(this.toJSON({ preserveCase: true }));
    }
    /**
     * Iterate over tuples of header [name, value] pairs.
     */
    [Symbol.iterator]() {
        return headerIterator(this._headersMap);
    }
}
/**
 * Creates an object that satisfies the `HttpHeaders` interface.
 * @param rawHeaders - A simple object representing initial headers
 */
function httpHeaders_createHttpHeaders(rawHeaders) {
    return new HttpHeadersImpl(rawHeaders);
}
//# sourceMappingURL=httpHeaders.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/uuidUtils.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Generated Universally Unique Identifier
 *
 * @returns RFC4122 v4 UUID.
 */
function randomUUID() {
    return crypto.randomUUID();
}
//# sourceMappingURL=uuidUtils.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/pipelineRequest.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


class PipelineRequestImpl {
    url;
    method;
    headers;
    timeout;
    withCredentials;
    body;
    multipartBody;
    formData;
    streamResponseStatusCodes;
    enableBrowserStreams;
    proxySettings;
    disableKeepAlive;
    abortSignal;
    requestId;
    allowInsecureConnection;
    onUploadProgress;
    onDownloadProgress;
    requestOverrides;
    authSchemes;
    constructor(options) {
        this.url = options.url;
        this.body = options.body;
        this.headers = options.headers ?? httpHeaders_createHttpHeaders();
        this.method = options.method ?? "GET";
        this.timeout = options.timeout ?? 0;
        this.multipartBody = options.multipartBody;
        this.formData = options.formData;
        this.disableKeepAlive = options.disableKeepAlive ?? false;
        this.proxySettings = options.proxySettings;
        this.streamResponseStatusCodes = options.streamResponseStatusCodes;
        this.withCredentials = options.withCredentials ?? false;
        this.abortSignal = options.abortSignal;
        this.onUploadProgress = options.onUploadProgress;
        this.onDownloadProgress = options.onDownloadProgress;
        this.requestId = options.requestId || randomUUID();
        this.allowInsecureConnection = options.allowInsecureConnection ?? false;
        this.enableBrowserStreams = options.enableBrowserStreams ?? false;
        this.requestOverrides = options.requestOverrides;
        this.authSchemes = options.authSchemes;
    }
}
/**
 * Creates a new pipeline request with the given options.
 * This method is to allow for the easy setting of default values and not required.
 * @param options - The options to create the request with.
 */
function pipelineRequest_createPipelineRequest(options) {
    return new PipelineRequestImpl(options);
}
//# sourceMappingURL=pipelineRequest.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/pipeline.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
const ValidPhaseNames = new Set(["Deserialize", "Serialize", "Retry", "Sign"]);
/**
 * A private implementation of Pipeline.
 * Do not export this class from the package.
 * @internal
 */
class HttpPipeline {
    _policies = [];
    _orderedPolicies;
    constructor(policies) {
        this._policies = policies?.slice(0) ?? [];
        this._orderedPolicies = undefined;
    }
    addPolicy(policy, options = {}) {
        if (options.phase && options.afterPhase) {
            throw new Error("Policies inside a phase cannot specify afterPhase.");
        }
        if (options.phase && !ValidPhaseNames.has(options.phase)) {
            throw new Error(`Invalid phase name: ${options.phase}`);
        }
        if (options.afterPhase && !ValidPhaseNames.has(options.afterPhase)) {
            throw new Error(`Invalid afterPhase name: ${options.afterPhase}`);
        }
        this._policies.push({
            policy,
            options,
        });
        this._orderedPolicies = undefined;
    }
    removePolicy(options) {
        const removedPolicies = [];
        this._policies = this._policies.filter((policyDescriptor) => {
            if ((options.name && policyDescriptor.policy.name === options.name) ||
                (options.phase && policyDescriptor.options.phase === options.phase)) {
                removedPolicies.push(policyDescriptor.policy);
                return false;
            }
            else {
                return true;
            }
        });
        this._orderedPolicies = undefined;
        return removedPolicies;
    }
    sendRequest(httpClient, request) {
        const policies = this.getOrderedPolicies();
        const pipeline = policies.reduceRight((next, policy) => {
            return (req) => {
                return policy.sendRequest(req, next);
            };
        }, (req) => httpClient.sendRequest(req));
        return pipeline(request);
    }
    getOrderedPolicies() {
        if (!this._orderedPolicies) {
            this._orderedPolicies = this.orderPolicies();
        }
        return this._orderedPolicies;
    }
    clone() {
        return new HttpPipeline(this._policies);
    }
    static create() {
        return new HttpPipeline();
    }
    orderPolicies() {
        /**
         * The goal of this method is to reliably order pipeline policies
         * based on their declared requirements when they were added.
         *
         * Order is first determined by phase:
         *
         * 1. Serialize Phase
         * 2. Policies not in a phase
         * 3. Deserialize Phase
         * 4. Retry Phase
         * 5. Sign Phase
         *
         * Within each phase, policies are executed in the order
         * they were added unless they were specified to execute
         * before/after other policies or after a particular phase.
         *
         * To determine the final order, we will walk the policy list
         * in phase order multiple times until all dependencies are
         * satisfied.
         *
         * `afterPolicies` are the set of policies that must be
         * executed before a given policy. This requirement is
         * considered satisfied when each of the listed policies
         * have been scheduled.
         *
         * `beforePolicies` are the set of policies that must be
         * executed after a given policy. Since this dependency
         * can be expressed by converting it into a equivalent
         * `afterPolicies` declarations, they are normalized
         * into that form for simplicity.
         *
         * An `afterPhase` dependency is considered satisfied when all
         * policies in that phase have scheduled.
         *
         */
        const result = [];
        // Track all policies we know about.
        const policyMap = new Map();
        function createPhase(name) {
            return {
                name,
                policies: new Set(),
                hasRun: false,
                hasAfterPolicies: false,
            };
        }
        // Track policies for each phase.
        const serializePhase = createPhase("Serialize");
        const noPhase = createPhase("None");
        const deserializePhase = createPhase("Deserialize");
        const retryPhase = createPhase("Retry");
        const signPhase = createPhase("Sign");
        // a list of phases in order
        const orderedPhases = [serializePhase, noPhase, deserializePhase, retryPhase, signPhase];
        // Small helper function to map phase name to each Phase
        function getPhase(phase) {
            if (phase === "Retry") {
                return retryPhase;
            }
            else if (phase === "Serialize") {
                return serializePhase;
            }
            else if (phase === "Deserialize") {
                return deserializePhase;
            }
            else if (phase === "Sign") {
                return signPhase;
            }
            else {
                return noPhase;
            }
        }
        // First walk each policy and create a node to track metadata.
        for (const descriptor of this._policies) {
            const policy = descriptor.policy;
            const options = descriptor.options;
            const policyName = policy.name;
            if (policyMap.has(policyName)) {
                throw new Error("Duplicate policy names not allowed in pipeline");
            }
            const node = {
                policy,
                dependsOn: new Set(),
                dependants: new Set(),
            };
            if (options.afterPhase) {
                node.afterPhase = getPhase(options.afterPhase);
                node.afterPhase.hasAfterPolicies = true;
            }
            policyMap.set(policyName, node);
            const phase = getPhase(options.phase);
            phase.policies.add(node);
        }
        // Now that each policy has a node, connect dependency references.
        for (const descriptor of this._policies) {
            const { policy, options } = descriptor;
            const policyName = policy.name;
            const node = policyMap.get(policyName);
            if (!node) {
                throw new Error(`Missing node for policy ${policyName}`);
            }
            if (options.afterPolicies) {
                for (const afterPolicyName of options.afterPolicies) {
                    const afterNode = policyMap.get(afterPolicyName);
                    if (afterNode) {
                        // Linking in both directions helps later
                        // when we want to notify dependants.
                        node.dependsOn.add(afterNode);
                        afterNode.dependants.add(node);
                    }
                }
            }
            if (options.beforePolicies) {
                for (const beforePolicyName of options.beforePolicies) {
                    const beforeNode = policyMap.get(beforePolicyName);
                    if (beforeNode) {
                        // To execute before another node, make it
                        // depend on the current node.
                        beforeNode.dependsOn.add(node);
                        node.dependants.add(beforeNode);
                    }
                }
            }
        }
        function walkPhase(phase) {
            phase.hasRun = true;
            // Sets iterate in insertion order
            for (const node of phase.policies) {
                if (node.afterPhase && (!node.afterPhase.hasRun || node.afterPhase.policies.size)) {
                    // If this node is waiting on a phase to complete,
                    // we need to skip it for now.
                    // Even if the phase is empty, we should wait for it
                    // to be walked to avoid re-ordering policies.
                    continue;
                }
                if (node.dependsOn.size === 0) {
                    // If there's nothing else we're waiting for, we can
                    // add this policy to the result list.
                    result.push(node.policy);
                    // Notify anything that depends on this policy that
                    // the policy has been scheduled.
                    for (const dependant of node.dependants) {
                        dependant.dependsOn.delete(node);
                    }
                    policyMap.delete(node.policy.name);
                    phase.policies.delete(node);
                }
            }
        }
        function walkPhases() {
            for (const phase of orderedPhases) {
                walkPhase(phase);
                // if the phase isn't complete
                if (phase.policies.size > 0 && phase !== noPhase) {
                    if (!noPhase.hasRun) {
                        // Try running noPhase to see if that unblocks this phase next tick.
                        // This can happen if a phase that happens before noPhase
                        // is waiting on a noPhase policy to complete.
                        walkPhase(noPhase);
                    }
                    // Don't proceed to the next phase until this phase finishes.
                    return;
                }
                if (phase.hasAfterPolicies) {
                    // Run any policies unblocked by this phase
                    walkPhase(noPhase);
                }
            }
        }
        // Iterate until we've put every node in the result list.
        let iteration = 0;
        while (policyMap.size > 0) {
            iteration++;
            const initialResultLength = result.length;
            // Keep walking each phase in order until we can order every node.
            walkPhases();
            // The result list *should* get at least one larger each time
            // after the first full pass.
            // Otherwise, we're going to loop forever.
            if (result.length <= initialResultLength && iteration > 1) {
                throw new Error("Cannot satisfy policy dependencies due to requirements cycle.");
            }
        }
        return result;
    }
}
/**
 * Creates a totally empty pipeline.
 * Useful for testing or creating a custom one.
 */
function pipeline_createEmptyPipeline() {
    return HttpPipeline.create();
}
//# sourceMappingURL=pipeline.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/object.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Helper to determine when an input is a generic JS object.
 * @returns true when input is an object type that is not null, Array, RegExp, or Date.
 */
function isObject(input) {
    return (typeof input === "object" &&
        input !== null &&
        !Array.isArray(input) &&
        !(input instanceof RegExp) &&
        !(input instanceof Date));
}
//# sourceMappingURL=object.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/error.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Typeguard for an error object shape (has name and message)
 * @param e - Something caught by a catch clause.
 */
function isError(e) {
    if (isObject(e)) {
        const hasName = typeof e.name === "string";
        const hasMessage = typeof e.message === "string";
        return hasName && hasMessage;
    }
    return false;
}
//# sourceMappingURL=error.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/inspect.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const custom = external_node_util_.inspect.custom;
//# sourceMappingURL=inspect.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/sanitizer.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const RedactedString = "REDACTED";
// Make sure this list is up-to-date with the one under core/logger/Readme#Keyconcepts
const defaultAllowedHeaderNames = [
    "x-ms-client-request-id",
    "x-ms-return-client-request-id",
    "x-ms-useragent",
    "x-ms-correlation-request-id",
    "x-ms-request-id",
    "client-request-id",
    "ms-cv",
    "return-client-request-id",
    "traceparent",
    "Access-Control-Allow-Credentials",
    "Access-Control-Allow-Headers",
    "Access-Control-Allow-Methods",
    "Access-Control-Allow-Origin",
    "Access-Control-Expose-Headers",
    "Access-Control-Max-Age",
    "Access-Control-Request-Headers",
    "Access-Control-Request-Method",
    "Origin",
    "Accept",
    "Accept-Encoding",
    "Cache-Control",
    "Connection",
    "Content-Length",
    "Content-Type",
    "Date",
    "ETag",
    "Expires",
    "If-Match",
    "If-Modified-Since",
    "If-None-Match",
    "If-Unmodified-Since",
    "Last-Modified",
    "Pragma",
    "Request-Id",
    "Retry-After",
    "Server",
    "Transfer-Encoding",
    "User-Agent",
    "WWW-Authenticate",
];
const defaultAllowedQueryParameters = ["api-version"];
/**
 * A utility class to sanitize objects for logging.
 */
class Sanitizer {
    allowedHeaderNames;
    allowedQueryParameters;
    constructor({ additionalAllowedHeaderNames: allowedHeaderNames = [], additionalAllowedQueryParameters: allowedQueryParameters = [], } = {}) {
        allowedHeaderNames = defaultAllowedHeaderNames.concat(allowedHeaderNames);
        allowedQueryParameters = defaultAllowedQueryParameters.concat(allowedQueryParameters);
        this.allowedHeaderNames = new Set(allowedHeaderNames.map((n) => n.toLowerCase()));
        this.allowedQueryParameters = new Set(allowedQueryParameters.map((p) => p.toLowerCase()));
    }
    /**
     * Sanitizes an object for logging.
     * @param obj - The object to sanitize
     * @returns - The sanitized object as a string
     */
    sanitize(obj) {
        const seen = new Set();
        return JSON.stringify(obj, (key, value) => {
            // Ensure Errors include their interesting non-enumerable members
            if (value instanceof Error) {
                return {
                    ...value,
                    name: value.name,
                    message: value.message,
                };
            }
            if (key === "headers" && isObject(value)) {
                return this.sanitizeHeaders(value);
            }
            else if (key === "url" && typeof value === "string") {
                return this.sanitizeUrl(value);
            }
            else if (key === "query" && isObject(value)) {
                return this.sanitizeQuery(value);
            }
            else if (key === "body") {
                // Don't log the request body
                return undefined;
            }
            else if (key === "response") {
                // Don't log response again
                return undefined;
            }
            else if (key === "operationSpec") {
                // When using sendOperationRequest, the request carries a massive
                // field with the autorest spec. No need to log it.
                return undefined;
            }
            else if (Array.isArray(value) || isObject(value)) {
                if (seen.has(value)) {
                    return "[Circular]";
                }
                seen.add(value);
            }
            return value;
        }, 2);
    }
    /**
     * Sanitizes a URL for logging.
     * @param value - The URL to sanitize
     * @returns - The sanitized URL as a string
     */
    sanitizeUrl(value) {
        if (typeof value !== "string" || value === null || value === "") {
            return value;
        }
        const url = new URL(value);
        if (!url.search) {
            return value;
        }
        for (const [key] of url.searchParams) {
            if (!this.allowedQueryParameters.has(key.toLowerCase())) {
                url.searchParams.set(key, RedactedString);
            }
        }
        return url.toString();
    }
    sanitizeHeaders(obj) {
        const sanitized = {};
        for (const key of Object.keys(obj)) {
            if (this.allowedHeaderNames.has(key.toLowerCase())) {
                sanitized[key] = obj[key];
            }
            else {
                sanitized[key] = RedactedString;
            }
        }
        return sanitized;
    }
    sanitizeQuery(value) {
        if (typeof value !== "object" || value === null) {
            return value;
        }
        const sanitized = {};
        for (const k of Object.keys(value)) {
            if (this.allowedQueryParameters.has(k.toLowerCase())) {
                sanitized[k] = value[k];
            }
            else {
                sanitized[k] = RedactedString;
            }
        }
        return sanitized;
    }
}
//# sourceMappingURL=sanitizer.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/restError.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



const errorSanitizer = new Sanitizer();
/**
 * A custom error type for failed pipeline requests.
 */
class restError_RestError extends Error {
    /**
     * Something went wrong when making the request.
     * This means the actual request failed for some reason,
     * such as a DNS issue or the connection being lost.
     */
    static REQUEST_SEND_ERROR = "REQUEST_SEND_ERROR";
    /**
     * This means that parsing the response from the server failed.
     * It may have been malformed.
     */
    static PARSE_ERROR = "PARSE_ERROR";
    /**
     * The code of the error itself (use statics on RestError if possible.)
     */
    code;
    /**
     * The HTTP status code of the request (if applicable.)
     */
    statusCode;
    /**
     * The request that was made.
     * This property is non-enumerable.
     */
    request;
    /**
     * The response received (if any.)
     * This property is non-enumerable.
     */
    response;
    /**
     * Bonus property set by the throw site.
     */
    details;
    constructor(message, options = {}) {
        super(message);
        this.name = "RestError";
        this.code = options.code;
        this.statusCode = options.statusCode;
        // The request and response may contain sensitive information in the headers or body.
        // To help prevent this sensitive information being accidentally logged, the request and response
        // properties are marked as non-enumerable here. This prevents them showing up in the output of
        // JSON.stringify and console.log.
        Object.defineProperty(this, "request", { value: options.request, enumerable: false });
        Object.defineProperty(this, "response", { value: options.response, enumerable: false });
        // Only include useful agent information in the request for logging, as the full agent object
        // may contain large binary data.
        const agent = this.request?.agent
            ? {
                maxFreeSockets: this.request.agent.maxFreeSockets,
                maxSockets: this.request.agent.maxSockets,
            }
            : undefined;
        // Logging method for util.inspect in Node
        Object.defineProperty(this, custom, {
            value: () => {
                // Extract non-enumerable properties and add them back. This is OK since in this output the request and
                // response get sanitized.
                return `RestError: ${this.message} \n ${errorSanitizer.sanitize({
                    ...this,
                    request: { ...this.request, agent },
                    response: this.response,
                })}`;
            },
            enumerable: false,
        });
        Object.setPrototypeOf(this, restError_RestError.prototype);
    }
}
/**
 * Typeguard for RestError
 * @param e - Something caught by a catch clause.
 */
function restError_isRestError(e) {
    if (e instanceof restError_RestError) {
        return true;
    }
    return isError(e) && e.name === "RestError";
}
//# sourceMappingURL=restError.js.map
// EXTERNAL MODULE: external "node:http"
var external_node_http_ = __nccwpck_require__(7067);
;// CONCATENATED MODULE: external "node:https"
const external_node_https_namespaceObject = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:https");
// EXTERNAL MODULE: external "node:zlib"
var external_node_zlib_ = __nccwpck_require__(8522);
// EXTERNAL MODULE: external "node:stream"
var external_node_stream_ = __nccwpck_require__(7075);
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/log.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const log_logger = createClientLogger("ts-http-runtime");
//# sourceMappingURL=log.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/nodeHttpClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.









const DEFAULT_TLS_SETTINGS = {};
function nodeHttpClient_isReadableStream(body) {
    return body && typeof body.pipe === "function";
}
function isStreamComplete(stream) {
    if (stream.readable === false) {
        return Promise.resolve();
    }
    return new Promise((resolve) => {
        const handler = () => {
            resolve();
            stream.removeListener("close", handler);
            stream.removeListener("end", handler);
            stream.removeListener("error", handler);
        };
        stream.on("close", handler);
        stream.on("end", handler);
        stream.on("error", handler);
    });
}
function isArrayBuffer(body) {
    return body && typeof body.byteLength === "number";
}
class ReportTransform extends external_node_stream_.Transform {
    loadedBytes = 0;
    progressCallback;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
    _transform(chunk, _encoding, callback) {
        this.push(chunk);
        this.loadedBytes += chunk.length;
        try {
            this.progressCallback({ loadedBytes: this.loadedBytes });
            callback();
        }
        catch (e) {
            callback(e);
        }
    }
    constructor(progressCallback) {
        super();
        this.progressCallback = progressCallback;
    }
}
/**
 * A HttpClient implementation that uses Node's "https" module to send HTTPS requests.
 * @internal
 */
class NodeHttpClient {
    cachedHttpAgent;
    cachedHttpsAgents = new WeakMap();
    /**
     * Makes a request over an underlying transport layer and returns the response.
     * @param request - The request to be made.
     */
    async sendRequest(request) {
        const abortController = new AbortController();
        let abortListener;
        if (request.abortSignal) {
            if (request.abortSignal.aborted) {
                throw new AbortError("The operation was aborted. Request has already been canceled.");
            }
            abortListener = (event) => {
                if (event.type === "abort") {
                    abortController.abort();
                }
            };
            request.abortSignal.addEventListener("abort", abortListener);
        }
        let timeoutId;
        if (request.timeout > 0) {
            timeoutId = setTimeout(() => {
                const sanitizer = new Sanitizer();
                log_logger.info(`request to '${sanitizer.sanitizeUrl(request.url)}' timed out. canceling...`);
                abortController.abort();
            }, request.timeout);
        }
        const acceptEncoding = request.headers.get("Accept-Encoding");
        const shouldDecompress = acceptEncoding?.includes("gzip") || acceptEncoding?.includes("deflate");
        let body = typeof request.body === "function" ? request.body() : request.body;
        if (body && !request.headers.has("Content-Length")) {
            const bodyLength = getBodyLength(body);
            if (bodyLength !== null) {
                request.headers.set("Content-Length", bodyLength);
            }
        }
        let responseStream;
        try {
            if (body && request.onUploadProgress) {
                const onUploadProgress = request.onUploadProgress;
                const uploadReportStream = new ReportTransform(onUploadProgress);
                uploadReportStream.on("error", (e) => {
                    log_logger.error("Error in upload progress", e);
                });
                if (nodeHttpClient_isReadableStream(body)) {
                    body.pipe(uploadReportStream);
                }
                else {
                    uploadReportStream.end(body);
                }
                body = uploadReportStream;
            }
            const res = await this.makeRequest(request, abortController, body);
            if (timeoutId !== undefined) {
                clearTimeout(timeoutId);
            }
            const headers = getResponseHeaders(res);
            const status = res.statusCode ?? 0;
            const response = {
                status,
                headers,
                request,
            };
            // Responses to HEAD must not have a body.
            // If they do return a body, that body must be ignored.
            if (request.method === "HEAD") {
                // call resume() and not destroy() to avoid closing the socket
                // and losing keep alive
                res.resume();
                return response;
            }
            responseStream = shouldDecompress ? getDecodedResponseStream(res, headers) : res;
            const onDownloadProgress = request.onDownloadProgress;
            if (onDownloadProgress) {
                const downloadReportStream = new ReportTransform(onDownloadProgress);
                downloadReportStream.on("error", (e) => {
                    log_logger.error("Error in download progress", e);
                });
                responseStream.pipe(downloadReportStream);
                responseStream = downloadReportStream;
            }
            if (
            // Value of POSITIVE_INFINITY in streamResponseStatusCodes is considered as any status code
            request.streamResponseStatusCodes?.has(Number.POSITIVE_INFINITY) ||
                request.streamResponseStatusCodes?.has(response.status)) {
                response.readableStreamBody = responseStream;
            }
            else {
                response.bodyAsText = await streamToText(responseStream);
            }
            return response;
        }
        finally {
            // clean up event listener
            if (request.abortSignal && abortListener) {
                let uploadStreamDone = Promise.resolve();
                if (nodeHttpClient_isReadableStream(body)) {
                    uploadStreamDone = isStreamComplete(body);
                }
                let downloadStreamDone = Promise.resolve();
                if (nodeHttpClient_isReadableStream(responseStream)) {
                    downloadStreamDone = isStreamComplete(responseStream);
                }
                Promise.all([uploadStreamDone, downloadStreamDone])
                    .then(() => {
                    // eslint-disable-next-line promise/always-return
                    if (abortListener) {
                        request.abortSignal?.removeEventListener("abort", abortListener);
                    }
                })
                    .catch((e) => {
                    log_logger.warning("Error when cleaning up abortListener on httpRequest", e);
                });
            }
        }
    }
    makeRequest(request, abortController, body) {
        const url = new URL(request.url);
        const isInsecure = url.protocol !== "https:";
        if (isInsecure && !request.allowInsecureConnection) {
            throw new Error(`Cannot connect to ${request.url} while allowInsecureConnection is false.`);
        }
        const agent = request.agent ?? this.getOrCreateAgent(request, isInsecure);
        const options = {
            agent,
            hostname: url.hostname,
            path: `${url.pathname}${url.search}`,
            port: url.port,
            method: request.method,
            headers: request.headers.toJSON({ preserveCase: true }),
            ...request.requestOverrides,
        };
        return new Promise((resolve, reject) => {
            const req = isInsecure ? external_node_http_.request(options, resolve) : external_node_https_namespaceObject.request(options, resolve);
            req.once("error", (err) => {
                reject(new restError_RestError(err.message, { code: err.code ?? restError_RestError.REQUEST_SEND_ERROR, request }));
            });
            abortController.signal.addEventListener("abort", () => {
                const abortError = new AbortError("The operation was aborted. Rejecting from abort signal callback while making request.");
                req.destroy(abortError);
                reject(abortError);
            });
            if (body && nodeHttpClient_isReadableStream(body)) {
                body.pipe(req);
            }
            else if (body) {
                if (typeof body === "string" || Buffer.isBuffer(body)) {
                    req.end(body);
                }
                else if (isArrayBuffer(body)) {
                    req.end(ArrayBuffer.isView(body) ? Buffer.from(body.buffer) : Buffer.from(body));
                }
                else {
                    log_logger.error("Unrecognized body type", body);
                    reject(new restError_RestError("Unrecognized body type"));
                }
            }
            else {
                // streams don't like "undefined" being passed as data
                req.end();
            }
        });
    }
    getOrCreateAgent(request, isInsecure) {
        const disableKeepAlive = request.disableKeepAlive;
        // Handle Insecure requests first
        if (isInsecure) {
            if (disableKeepAlive) {
                // keepAlive:false is the default so we don't need a custom Agent
                return external_node_http_.globalAgent;
            }
            if (!this.cachedHttpAgent) {
                // If there is no cached agent create a new one and cache it.
                this.cachedHttpAgent = new external_node_http_.Agent({ keepAlive: true });
            }
            return this.cachedHttpAgent;
        }
        else {
            if (disableKeepAlive && !request.tlsSettings) {
                // When there are no tlsSettings and keepAlive is false
                // we don't need a custom agent
                return external_node_https_namespaceObject.globalAgent;
            }
            // We use the tlsSettings to index cached clients
            const tlsSettings = request.tlsSettings ?? DEFAULT_TLS_SETTINGS;
            // Get the cached agent or create a new one with the
            // provided values for keepAlive and tlsSettings
            let agent = this.cachedHttpsAgents.get(tlsSettings);
            if (agent && agent.options.keepAlive === !disableKeepAlive) {
                return agent;
            }
            log_logger.info("No cached TLS Agent exist, creating a new Agent");
            agent = new external_node_https_namespaceObject.Agent({
                // keepAlive is true if disableKeepAlive is false.
                keepAlive: !disableKeepAlive,
                // Since we are spreading, if no tslSettings were provided, nothing is added to the agent options.
                ...tlsSettings,
            });
            this.cachedHttpsAgents.set(tlsSettings, agent);
            return agent;
        }
    }
}
function getResponseHeaders(res) {
    const headers = httpHeaders_createHttpHeaders();
    for (const header of Object.keys(res.headers)) {
        const value = res.headers[header];
        if (Array.isArray(value)) {
            if (value.length > 0) {
                headers.set(header, value[0]);
            }
        }
        else if (value) {
            headers.set(header, value);
        }
    }
    return headers;
}
function getDecodedResponseStream(stream, headers) {
    const contentEncoding = headers.get("Content-Encoding");
    if (contentEncoding === "gzip") {
        const unzip = external_node_zlib_.createGunzip();
        stream.pipe(unzip);
        return unzip;
    }
    else if (contentEncoding === "deflate") {
        const inflate = external_node_zlib_.createInflate();
        stream.pipe(inflate);
        return inflate;
    }
    return stream;
}
function streamToText(stream) {
    return new Promise((resolve, reject) => {
        const buffer = [];
        stream.on("data", (chunk) => {
            if (Buffer.isBuffer(chunk)) {
                buffer.push(chunk);
            }
            else {
                buffer.push(Buffer.from(chunk));
            }
        });
        stream.on("end", () => {
            resolve(Buffer.concat(buffer).toString("utf8"));
        });
        stream.on("error", (e) => {
            if (e && e?.name === "AbortError") {
                reject(e);
            }
            else {
                reject(new restError_RestError(`Error reading response as text: ${e.message}`, {
                    code: restError_RestError.PARSE_ERROR,
                }));
            }
        });
    });
}
/** @internal */
function getBodyLength(body) {
    if (!body) {
        return 0;
    }
    else if (Buffer.isBuffer(body)) {
        return body.length;
    }
    else if (nodeHttpClient_isReadableStream(body)) {
        return null;
    }
    else if (isArrayBuffer(body)) {
        return body.byteLength;
    }
    else if (typeof body === "string") {
        return Buffer.from(body).length;
    }
    else {
        return null;
    }
}
/**
 * Create a new HttpClient instance for the NodeJS environment.
 * @internal
 */
function createNodeHttpClient() {
    return new NodeHttpClient();
}
//# sourceMappingURL=nodeHttpClient.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/defaultHttpClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Create the correct HttpClient for the current environment.
 */
function defaultHttpClient_createDefaultHttpClient() {
    return createNodeHttpClient();
}
//# sourceMappingURL=defaultHttpClient.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/logPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * The programmatic identifier of the logPolicy.
 */
const logPolicyName = "logPolicy";
/**
 * A policy that logs all requests and responses.
 * @param options - Options to configure logPolicy.
 */
function logPolicy_logPolicy(options = {}) {
    const logger = options.logger ?? log_logger.info;
    const sanitizer = new Sanitizer({
        additionalAllowedHeaderNames: options.additionalAllowedHeaderNames,
        additionalAllowedQueryParameters: options.additionalAllowedQueryParameters,
    });
    return {
        name: logPolicyName,
        async sendRequest(request, next) {
            if (!logger.enabled) {
                return next(request);
            }
            logger(`Request: ${sanitizer.sanitize(request)}`);
            const response = await next(request);
            logger(`Response status code: ${response.status}`);
            logger(`Headers: ${sanitizer.sanitize(response.headers)}`);
            return response;
        },
    };
}
//# sourceMappingURL=logPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/redirectPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * The programmatic identifier of the redirectPolicy.
 */
const redirectPolicyName = "redirectPolicy";
/**
 * Methods that are allowed to follow redirects 301 and 302
 */
const allowedRedirect = ["GET", "HEAD"];
/**
 * A policy to follow Location headers from the server in order
 * to support server-side redirection.
 * In the browser, this policy is not used.
 * @param options - Options to control policy behavior.
 */
function redirectPolicy_redirectPolicy(options = {}) {
    const { maxRetries = 20, allowCrossOriginRedirects = false } = options;
    return {
        name: redirectPolicyName,
        async sendRequest(request, next) {
            const response = await next(request);
            return handleRedirect(next, response, maxRetries, allowCrossOriginRedirects);
        },
    };
}
async function handleRedirect(next, response, maxRetries, allowCrossOriginRedirects, currentRetries = 0) {
    const { request, status, headers } = response;
    const locationHeader = headers.get("location");
    if (locationHeader &&
        (status === 300 ||
            (status === 301 && allowedRedirect.includes(request.method)) ||
            (status === 302 && allowedRedirect.includes(request.method)) ||
            (status === 303 && request.method === "POST") ||
            status === 307) &&
        currentRetries < maxRetries) {
        const url = new URL(locationHeader, request.url);
        // Only follow redirects to the same origin by default.
        if (!allowCrossOriginRedirects) {
            const originalUrl = new URL(request.url);
            if (url.origin !== originalUrl.origin) {
                log_logger.verbose(`Skipping cross-origin redirect from ${originalUrl.origin} to ${url.origin}.`);
                return response;
            }
        }
        request.url = url.toString();
        // POST request with Status code 303 should be converted into a
        // redirected GET request if the redirect url is present in the location header
        if (status === 303) {
            request.method = "GET";
            request.headers.delete("Content-Length");
            delete request.body;
        }
        request.headers.delete("Authorization");
        const res = await next(request);
        return handleRedirect(next, res, maxRetries, allowCrossOriginRedirects, currentRetries + 1);
    }
    return response;
}
//# sourceMappingURL=redirectPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/userAgentPlatform.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * @internal
 */
function getHeaderName() {
    return "User-Agent";
}
/**
 * @internal
 */
async function userAgentPlatform_setPlatformSpecificData(map) {
    if (process && process.versions) {
        const osInfo = `${os.type()} ${os.release()}; ${os.arch()}`;
        if (process.versions.bun) {
            map.set("Bun", `${process.versions.bun} (${osInfo})`);
        }
        else if (process.versions.deno) {
            map.set("Deno", `${process.versions.deno} (${osInfo})`);
        }
        else if (process.versions.node) {
            map.set("Node", `${process.versions.node} (${osInfo})`);
        }
    }
}
//# sourceMappingURL=userAgentPlatform.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/userAgent.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


function userAgent_getUserAgentString(telemetryInfo) {
    const parts = [];
    for (const [key, value] of telemetryInfo) {
        const token = value ? `${key}/${value}` : key;
        parts.push(token);
    }
    return parts.join(" ");
}
/**
 * @internal
 */
function getUserAgentHeaderName() {
    return getHeaderName();
}
/**
 * @internal
 */
async function userAgent_getUserAgentValue(prefix) {
    const runtimeInfo = new Map();
    runtimeInfo.set("ts-http-runtime", SDK_VERSION);
    await setPlatformSpecificData(runtimeInfo);
    const defaultAgent = userAgent_getUserAgentString(runtimeInfo);
    const userAgentValue = prefix ? `${prefix} ${defaultAgent}` : defaultAgent;
    return userAgentValue;
}
//# sourceMappingURL=userAgent.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/userAgentPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const UserAgentHeaderName = getUserAgentHeaderName();
/**
 * The programmatic identifier of the userAgentPolicy.
 */
const userAgentPolicyName = "userAgentPolicy";
/**
 * A policy that sets the User-Agent header (or equivalent) to reflect
 * the library version.
 * @param options - Options to customize the user agent value.
 */
function userAgentPolicy_userAgentPolicy(options = {}) {
    const userAgentValue = getUserAgentValue(options.userAgentPrefix);
    return {
        name: userAgentPolicyName,
        async sendRequest(request, next) {
            if (!request.headers.has(UserAgentHeaderName)) {
                request.headers.set(UserAgentHeaderName, await userAgentValue);
            }
            return next(request);
        },
    };
}
//# sourceMappingURL=userAgentPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/random.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Returns a random integer value between a lower and upper bound,
 * inclusive of both bounds.
 * Note that this uses Math.random and isn't secure. If you need to use
 * this for any kind of security purpose, find a better source of random.
 * @param min - The smallest integer value allowed.
 * @param max - The largest integer value allowed.
 */
function random_getRandomIntegerInclusive(min, max) {
    // Make sure inputs are integers.
    min = Math.ceil(min);
    max = Math.floor(max);
    // Pick a random offset from zero to the size of the range.
    // Since Math.random() can never return 1, we have to make the range one larger
    // in order to be inclusive of the maximum value after we take the floor.
    const offset = Math.floor(Math.random() * (max - min + 1));
    return offset + min;
}
//# sourceMappingURL=random.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/delay.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Calculates the delay interval for retry attempts using exponential delay with jitter.
 * @param retryAttempt - The current retry attempt number.
 * @param config - The exponential retry configuration.
 * @returns An object containing the calculated retry delay.
 */
function calculateRetryDelay(retryAttempt, config) {
    // Exponentially increase the delay each time
    const exponentialDelay = config.retryDelayInMs * Math.pow(2, retryAttempt);
    // Don't let the delay exceed the maximum
    const clampedDelay = Math.min(config.maxRetryDelayInMs, exponentialDelay);
    // Allow the final value to have some "jitter" (within 50% of the delay size) so
    // that retries across multiple clients don't occur simultaneously.
    const retryAfterInMs = clampedDelay / 2 + random_getRandomIntegerInclusive(0, clampedDelay / 2);
    return { retryAfterInMs };
}
//# sourceMappingURL=delay.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/helpers.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const StandardAbortMessage = "The operation was aborted.";
/**
 * A wrapper for setTimeout that resolves a promise after delayInMs milliseconds.
 * @param delayInMs - The number of milliseconds to be delayed.
 * @param value - The value to be resolved with after a timeout of t milliseconds.
 * @param options - The options for delay - currently abort options
 *                  - abortSignal - The abortSignal associated with containing operation.
 *                  - abortErrorMsg - The abort error message associated with containing operation.
 * @returns Resolved promise
 */
function helpers_delay(delayInMs, value, options) {
    return new Promise((resolve, reject) => {
        let timer = undefined;
        let onAborted = undefined;
        const rejectOnAbort = () => {
            return reject(new AbortError(options?.abortErrorMsg ? options?.abortErrorMsg : StandardAbortMessage));
        };
        const removeListeners = () => {
            if (options?.abortSignal && onAborted) {
                options.abortSignal.removeEventListener("abort", onAborted);
            }
        };
        onAborted = () => {
            if (timer) {
                clearTimeout(timer);
            }
            removeListeners();
            return rejectOnAbort();
        };
        if (options?.abortSignal && options.abortSignal.aborted) {
            return rejectOnAbort();
        }
        timer = setTimeout(() => {
            removeListeners();
            resolve(value);
        }, delayInMs);
        if (options?.abortSignal) {
            options.abortSignal.addEventListener("abort", onAborted);
        }
    });
}
/**
 * @internal
 * @returns the parsed value or undefined if the parsed value is invalid.
 */
function parseHeaderValueAsNumber(response, headerName) {
    const value = response.headers.get(headerName);
    if (!value)
        return;
    const valueAsNum = Number(value);
    if (Number.isNaN(valueAsNum))
        return;
    return valueAsNum;
}
//# sourceMappingURL=helpers.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/retryStrategies/throttlingRetryStrategy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * The header that comes back from services representing
 * the amount of time (minimum) to wait to retry (in seconds or timestamp after which we can retry).
 */
const RetryAfterHeader = "Retry-After";
/**
 * The headers that come back from services representing
 * the amount of time (minimum) to wait to retry.
 *
 * "retry-after-ms", "x-ms-retry-after-ms" : milliseconds
 * "Retry-After" : seconds or timestamp
 */
const AllRetryAfterHeaders = ["retry-after-ms", "x-ms-retry-after-ms", RetryAfterHeader];
/**
 * A response is a throttling retry response if it has a throttling status code (429 or 503),
 * as long as one of the [ "Retry-After" or "retry-after-ms" or "x-ms-retry-after-ms" ] headers has a valid value.
 *
 * Returns the `retryAfterInMs` value if the response is a throttling retry response.
 * If not throttling retry response, returns `undefined`.
 *
 * @internal
 */
function getRetryAfterInMs(response) {
    if (!(response && [429, 503].includes(response.status)))
        return undefined;
    try {
        // Headers: "retry-after-ms", "x-ms-retry-after-ms", "Retry-After"
        for (const header of AllRetryAfterHeaders) {
            const retryAfterValue = parseHeaderValueAsNumber(response, header);
            if (retryAfterValue === 0 || retryAfterValue) {
                // "Retry-After" header ==> seconds
                // "retry-after-ms", "x-ms-retry-after-ms" headers ==> milli-seconds
                const multiplyingFactor = header === RetryAfterHeader ? 1000 : 1;
                return retryAfterValue * multiplyingFactor; // in milli-seconds
            }
        }
        // RetryAfterHeader ("Retry-After") has a special case where it might be formatted as a date instead of a number of seconds
        const retryAfterHeader = response.headers.get(RetryAfterHeader);
        if (!retryAfterHeader)
            return;
        const date = Date.parse(retryAfterHeader);
        const diff = date - Date.now();
        // negative diff would mean a date in the past, so retry asap with 0 milliseconds
        return Number.isFinite(diff) ? Math.max(0, diff) : undefined;
    }
    catch {
        return undefined;
    }
}
/**
 * A response is a retry response if it has a throttling status code (429 or 503),
 * as long as one of the [ "Retry-After" or "retry-after-ms" or "x-ms-retry-after-ms" ] headers has a valid value.
 */
function isThrottlingRetryResponse(response) {
    return Number.isFinite(getRetryAfterInMs(response));
}
function throttlingRetryStrategy_throttlingRetryStrategy() {
    return {
        name: "throttlingRetryStrategy",
        retry({ response }) {
            const retryAfterInMs = getRetryAfterInMs(response);
            if (!Number.isFinite(retryAfterInMs)) {
                return { skipStrategy: true };
            }
            return {
                retryAfterInMs,
            };
        },
    };
}
//# sourceMappingURL=throttlingRetryStrategy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/retryStrategies/exponentialRetryStrategy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


// intervals are in milliseconds
const DEFAULT_CLIENT_RETRY_INTERVAL = 1000;
const DEFAULT_CLIENT_MAX_RETRY_INTERVAL = 1000 * 64;
/**
 * A retry strategy that retries with an exponentially increasing delay in these two cases:
 * - When there are errors in the underlying transport layer (e.g. DNS lookup failures).
 * - Or otherwise if the outgoing request fails (408, greater or equal than 500, except for 501 and 505).
 */
function exponentialRetryStrategy_exponentialRetryStrategy(options = {}) {
    const retryInterval = options.retryDelayInMs ?? DEFAULT_CLIENT_RETRY_INTERVAL;
    const maxRetryInterval = options.maxRetryDelayInMs ?? DEFAULT_CLIENT_MAX_RETRY_INTERVAL;
    return {
        name: "exponentialRetryStrategy",
        retry({ retryCount, response, responseError }) {
            const matchedSystemError = isSystemError(responseError);
            const ignoreSystemErrors = matchedSystemError && options.ignoreSystemErrors;
            const isExponential = isExponentialRetryResponse(response);
            const ignoreExponentialResponse = isExponential && options.ignoreHttpStatusCodes;
            const unknownResponse = response && (isThrottlingRetryResponse(response) || !isExponential);
            if (unknownResponse || ignoreExponentialResponse || ignoreSystemErrors) {
                return { skipStrategy: true };
            }
            if (responseError && !matchedSystemError && !isExponential) {
                return { errorToThrow: responseError };
            }
            return calculateRetryDelay(retryCount, {
                retryDelayInMs: retryInterval,
                maxRetryDelayInMs: maxRetryInterval,
            });
        },
    };
}
/**
 * A response is a retry response if it has status codes:
 * - 408, or
 * - Greater or equal than 500, except for 501 and 505.
 */
function isExponentialRetryResponse(response) {
    return Boolean(response &&
        response.status !== undefined &&
        (response.status >= 500 || response.status === 408) &&
        response.status !== 501 &&
        response.status !== 505);
}
/**
 * Determines whether an error from a pipeline response was triggered in the network layer.
 */
function isSystemError(err) {
    if (!err) {
        return false;
    }
    return (err.code === "ETIMEDOUT" ||
        err.code === "ESOCKETTIMEDOUT" ||
        err.code === "ECONNREFUSED" ||
        err.code === "ECONNRESET" ||
        err.code === "ENOENT" ||
        err.code === "ENOTFOUND");
}
//# sourceMappingURL=exponentialRetryStrategy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/constants.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
const constants_SDK_VERSION = "0.3.5";
const constants_DEFAULT_RETRY_POLICY_COUNT = 3;
//# sourceMappingURL=constants.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/retryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.





const retryPolicyLogger = createClientLogger("ts-http-runtime retryPolicy");
/**
 * The programmatic identifier of the retryPolicy.
 */
const retryPolicyName = "retryPolicy";
/**
 * retryPolicy is a generic policy to enable retrying requests when certain conditions are met
 */
function retryPolicy_retryPolicy(strategies, options = { maxRetries: constants_DEFAULT_RETRY_POLICY_COUNT }) {
    const logger = options.logger || retryPolicyLogger;
    return {
        name: retryPolicyName,
        async sendRequest(request, next) {
            let response;
            let responseError;
            let retryCount = -1;
            retryRequest: while (true) {
                retryCount += 1;
                response = undefined;
                responseError = undefined;
                try {
                    logger.info(`Retry ${retryCount}: Attempting to send request`, request.requestId);
                    response = await next(request);
                    logger.info(`Retry ${retryCount}: Received a response from request`, request.requestId);
                }
                catch (e) {
                    logger.error(`Retry ${retryCount}: Received an error from request`, request.requestId);
                    // RestErrors are valid targets for the retry strategies.
                    // If none of the retry strategies can work with them, they will be thrown later in this policy.
                    // If the received error is not a RestError, it is immediately thrown.
                    if (!restError_isRestError(e)) {
                        throw e;
                    }
                    responseError = e;
                    response = e.response;
                }
                if (request.abortSignal?.aborted) {
                    logger.error(`Retry ${retryCount}: Request aborted.`);
                    const abortError = new AbortError();
                    throw abortError;
                }
                if (retryCount >= (options.maxRetries ?? constants_DEFAULT_RETRY_POLICY_COUNT)) {
                    logger.info(`Retry ${retryCount}: Maximum retries reached. Returning the last received response, or throwing the last received error.`);
                    if (responseError) {
                        throw responseError;
                    }
                    else if (response) {
                        return response;
                    }
                    else {
                        throw new Error("Maximum retries reached with no response or error to throw");
                    }
                }
                logger.info(`Retry ${retryCount}: Processing ${strategies.length} retry strategies.`);
                strategiesLoop: for (const strategy of strategies) {
                    const strategyLogger = strategy.logger || logger;
                    strategyLogger.info(`Retry ${retryCount}: Processing retry strategy ${strategy.name}.`);
                    const modifiers = strategy.retry({
                        retryCount,
                        response,
                        responseError,
                    });
                    if (modifiers.skipStrategy) {
                        strategyLogger.info(`Retry ${retryCount}: Skipped.`);
                        continue strategiesLoop;
                    }
                    const { errorToThrow, retryAfterInMs, redirectTo } = modifiers;
                    if (errorToThrow) {
                        strategyLogger.error(`Retry ${retryCount}: Retry strategy ${strategy.name} throws error:`, errorToThrow);
                        throw errorToThrow;
                    }
                    if (retryAfterInMs || retryAfterInMs === 0) {
                        strategyLogger.info(`Retry ${retryCount}: Retry strategy ${strategy.name} retries after ${retryAfterInMs}`);
                        await helpers_delay(retryAfterInMs, undefined, { abortSignal: request.abortSignal });
                        continue retryRequest;
                    }
                    if (redirectTo) {
                        strategyLogger.info(`Retry ${retryCount}: Retry strategy ${strategy.name} redirects to ${redirectTo}`);
                        request.url = redirectTo;
                        continue retryRequest;
                    }
                }
                if (responseError) {
                    logger.info(`None of the retry strategies could work with the received error. Throwing it.`);
                    throw responseError;
                }
                if (response) {
                    logger.info(`None of the retry strategies could work with the received response. Returning it.`);
                    return response;
                }
                // If all the retries skip and there's no response,
                // we're still in the retry loop, so a new request will be sent
                // until `maxRetries` is reached.
            }
        },
    };
}
//# sourceMappingURL=retryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/defaultRetryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




/**
 * Name of the {@link defaultRetryPolicy}
 */
const defaultRetryPolicyName = "defaultRetryPolicy";
/**
 * A policy that retries according to three strategies:
 * - When the server sends a 429 response with a Retry-After header.
 * - When there are errors in the underlying transport layer (e.g. DNS lookup failures).
 * - Or otherwise if the outgoing request fails, it will retry with an exponentially increasing delay.
 */
function defaultRetryPolicy_defaultRetryPolicy(options = {}) {
    return {
        name: defaultRetryPolicyName,
        sendRequest: retryPolicy_retryPolicy([throttlingRetryStrategy_throttlingRetryStrategy(), exponentialRetryStrategy_exponentialRetryStrategy(options)], {
            maxRetries: options.maxRetries ?? constants_DEFAULT_RETRY_POLICY_COUNT,
        }).sendRequest,
    };
}
//# sourceMappingURL=defaultRetryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/bytesEncoding.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * The helper that transforms bytes with specific character encoding into string
 * @param bytes - the uint8array bytes
 * @param format - the format we use to encode the byte
 * @returns a string of the encoded string
 */
function bytesEncoding_uint8ArrayToString(bytes, format) {
    return Buffer.from(bytes).toString(format);
}
/**
 * The helper that transforms string to specific character encoded bytes array.
 * @param value - the string to be converted
 * @param format - the format we use to decode the value
 * @returns a uint8array
 */
function bytesEncoding_stringToUint8Array(value, format) {
    return Buffer.from(value, format);
}
//# sourceMappingURL=bytesEncoding.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/checkEnvironment.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * A constant that indicates whether the environment the code is running is a Web Browser.
 */
// eslint-disable-next-line @azure/azure-sdk/ts-no-window
const isBrowser = typeof window !== "undefined" && typeof window.document !== "undefined";
/**
 * A constant that indicates whether the environment the code is running is a Web Worker.
 */
const isWebWorker = typeof self === "object" &&
    typeof self?.importScripts === "function" &&
    (self.constructor?.name === "DedicatedWorkerGlobalScope" ||
        self.constructor?.name === "ServiceWorkerGlobalScope" ||
        self.constructor?.name === "SharedWorkerGlobalScope");
/**
 * A constant that indicates whether the environment the code is running is Deno.
 */
const isDeno = typeof Deno !== "undefined" &&
    typeof Deno.version !== "undefined" &&
    typeof Deno.version.deno !== "undefined";
/**
 * A constant that indicates whether the environment the code is running is Bun.sh.
 */
const isBun = typeof Bun !== "undefined" && typeof Bun.version !== "undefined";
/**
 * A constant that indicates whether the environment the code is running is a Node.js compatible environment.
 */
const checkEnvironment_isNodeLike = typeof globalThis.process !== "undefined" &&
    Boolean(globalThis.process.version) &&
    Boolean(globalThis.process.versions?.node);
/**
 * A constant that indicates whether the environment the code is running is Node.JS.
 */
const isNodeRuntime = checkEnvironment_isNodeLike && !isBun && !isDeno;
/**
 * A constant that indicates whether the environment the code is running is in React-Native.
 */
// https://github.com/facebook/react-native/blob/main/packages/react-native/Libraries/Core/setUpNavigator.js
const isReactNative = typeof navigator !== "undefined" && navigator?.product === "ReactNative";
//# sourceMappingURL=checkEnvironment.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/formDataPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * The programmatic identifier of the formDataPolicy.
 */
const formDataPolicyName = "formDataPolicy";
function formDataToFormDataMap(formData) {
    const formDataMap = {};
    for (const [key, value] of formData.entries()) {
        formDataMap[key] ??= [];
        formDataMap[key].push(value);
    }
    return formDataMap;
}
/**
 * A policy that encodes FormData on the request into the body.
 */
function formDataPolicy_formDataPolicy() {
    return {
        name: formDataPolicyName,
        async sendRequest(request, next) {
            if (checkEnvironment_isNodeLike && typeof FormData !== "undefined" && request.body instanceof FormData) {
                request.formData = formDataToFormDataMap(request.body);
                request.body = undefined;
            }
            if (request.formData) {
                const contentType = request.headers.get("Content-Type");
                if (contentType && contentType.indexOf("application/x-www-form-urlencoded") !== -1) {
                    request.body = wwwFormUrlEncode(request.formData);
                }
                else {
                    await prepareFormData(request.formData, request);
                }
                request.formData = undefined;
            }
            return next(request);
        },
    };
}
function wwwFormUrlEncode(formData) {
    const urlSearchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(formData)) {
        if (Array.isArray(value)) {
            for (const subValue of value) {
                urlSearchParams.append(key, subValue.toString());
            }
        }
        else {
            urlSearchParams.append(key, value.toString());
        }
    }
    return urlSearchParams.toString();
}
async function prepareFormData(formData, request) {
    // validate content type (multipart/form-data)
    const contentType = request.headers.get("Content-Type");
    if (contentType && !contentType.startsWith("multipart/form-data")) {
        // content type is specified and is not multipart/form-data. Exit.
        return;
    }
    request.headers.set("Content-Type", contentType ?? "multipart/form-data");
    // set body to MultipartRequestBody using content from FormDataMap
    const parts = [];
    for (const [fieldName, values] of Object.entries(formData)) {
        for (const value of Array.isArray(values) ? values : [values]) {
            if (typeof value === "string") {
                parts.push({
                    headers: httpHeaders_createHttpHeaders({
                        "Content-Disposition": `form-data; name="${fieldName}"`,
                    }),
                    body: bytesEncoding_stringToUint8Array(value, "utf-8"),
                });
            }
            else if (value === undefined || value === null || typeof value !== "object") {
                throw new Error(`Unexpected value for key ${fieldName}: ${value}. Value should be serialized to string first.`);
            }
            else {
                // using || instead of ?? here since if value.name is empty we should create a file name
                const fileName = value.name || "blob";
                const headers = httpHeaders_createHttpHeaders();
                headers.set("Content-Disposition", `form-data; name="${fieldName}"; filename="${fileName}"`);
                // again, || is used since an empty value.type means the content type is unset
                headers.set("Content-Type", value.type || "application/octet-stream");
                parts.push({
                    headers,
                    body: value,
                });
            }
        }
    }
    request.multipartBody = { parts };
}
//# sourceMappingURL=formDataPolicy.js.map
// EXTERNAL MODULE: ./node_modules/https-proxy-agent/dist/index.js
var dist = __nccwpck_require__(3669);
// EXTERNAL MODULE: ./node_modules/http-proxy-agent/dist/index.js
var http_proxy_agent_dist = __nccwpck_require__(1970);
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/proxyPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



const HTTPS_PROXY = "HTTPS_PROXY";
const HTTP_PROXY = "HTTP_PROXY";
const ALL_PROXY = "ALL_PROXY";
const NO_PROXY = "NO_PROXY";
/**
 * The programmatic identifier of the proxyPolicy.
 */
const proxyPolicyName = "proxyPolicy";
/**
 * Stores the patterns specified in NO_PROXY environment variable.
 * @internal
 */
const globalNoProxyList = [];
let noProxyListLoaded = false;
/** A cache of whether a host should bypass the proxy. */
const globalBypassedMap = new Map();
function getEnvironmentValue(name) {
    if (process.env[name]) {
        return process.env[name];
    }
    else if (process.env[name.toLowerCase()]) {
        return process.env[name.toLowerCase()];
    }
    return undefined;
}
function loadEnvironmentProxyValue() {
    if (!process) {
        return undefined;
    }
    const httpsProxy = getEnvironmentValue(HTTPS_PROXY);
    const allProxy = getEnvironmentValue(ALL_PROXY);
    const httpProxy = getEnvironmentValue(HTTP_PROXY);
    return httpsProxy || allProxy || httpProxy;
}
/**
 * Check whether the host of a given `uri` matches any pattern in the no proxy list.
 * If there's a match, any request sent to the same host shouldn't have the proxy settings set.
 * This implementation is a port of https://github.com/Azure/azure-sdk-for-net/blob/8cca811371159e527159c7eb65602477898683e2/sdk/core/Azure.Core/src/Pipeline/Internal/HttpEnvironmentProxy.cs#L210
 */
function isBypassed(uri, noProxyList, bypassedMap) {
    if (noProxyList.length === 0) {
        return false;
    }
    const host = new URL(uri).hostname;
    if (bypassedMap?.has(host)) {
        return bypassedMap.get(host);
    }
    let isBypassedFlag = false;
    for (const pattern of noProxyList) {
        if (pattern[0] === ".") {
            // This should match either domain it self or any subdomain or host
            // .foo.com will match foo.com it self or *.foo.com
            if (host.endsWith(pattern)) {
                isBypassedFlag = true;
            }
            else {
                if (host.length === pattern.length - 1 && host === pattern.slice(1)) {
                    isBypassedFlag = true;
                }
            }
        }
        else {
            if (host === pattern) {
                isBypassedFlag = true;
            }
        }
    }
    bypassedMap?.set(host, isBypassedFlag);
    return isBypassedFlag;
}
function loadNoProxy() {
    const noProxy = getEnvironmentValue(NO_PROXY);
    noProxyListLoaded = true;
    if (noProxy) {
        return noProxy
            .split(",")
            .map((item) => item.trim())
            .filter((item) => item.length);
    }
    return [];
}
/**
 * This method converts a proxy url into `ProxySettings` for use with ProxyPolicy.
 * If no argument is given, it attempts to parse a proxy URL from the environment
 * variables `HTTPS_PROXY` or `HTTP_PROXY`.
 * @param proxyUrl - The url of the proxy to use. May contain authentication information.
 * @deprecated - Internally this method is no longer necessary when setting proxy information.
 */
function getDefaultProxySettings(proxyUrl) {
    if (!proxyUrl) {
        proxyUrl = loadEnvironmentProxyValue();
        if (!proxyUrl) {
            return undefined;
        }
    }
    const parsedUrl = new URL(proxyUrl);
    const schema = parsedUrl.protocol ? parsedUrl.protocol + "//" : "";
    return {
        host: schema + parsedUrl.hostname,
        port: Number.parseInt(parsedUrl.port || "80"),
        username: parsedUrl.username,
        password: parsedUrl.password,
    };
}
/**
 * This method attempts to parse a proxy URL from the environment
 * variables `HTTPS_PROXY` or `HTTP_PROXY`.
 */
function getDefaultProxySettingsInternal() {
    const envProxy = loadEnvironmentProxyValue();
    return envProxy ? new URL(envProxy) : undefined;
}
function getUrlFromProxySettings(settings) {
    let parsedProxyUrl;
    try {
        parsedProxyUrl = new URL(settings.host);
    }
    catch {
        throw new Error(`Expecting a valid host string in proxy settings, but found "${settings.host}".`);
    }
    parsedProxyUrl.port = String(settings.port);
    if (settings.username) {
        parsedProxyUrl.username = settings.username;
    }
    if (settings.password) {
        parsedProxyUrl.password = settings.password;
    }
    return parsedProxyUrl;
}
function setProxyAgentOnRequest(request, cachedAgents, proxyUrl) {
    // Custom Agent should take precedence so if one is present
    // we should skip to avoid overwriting it.
    if (request.agent) {
        return;
    }
    const url = new URL(request.url);
    const isInsecure = url.protocol !== "https:";
    if (request.tlsSettings) {
        log_logger.warning("TLS settings are not supported in combination with custom Proxy, certificates provided to the client will be ignored.");
    }
    if (isInsecure) {
        if (!cachedAgents.httpProxyAgent) {
            cachedAgents.httpProxyAgent = new http_proxy_agent_dist.HttpProxyAgent(proxyUrl);
        }
        request.agent = cachedAgents.httpProxyAgent;
    }
    else {
        if (!cachedAgents.httpsProxyAgent) {
            cachedAgents.httpsProxyAgent = new dist.HttpsProxyAgent(proxyUrl);
        }
        request.agent = cachedAgents.httpsProxyAgent;
    }
}
/**
 * A policy that allows one to apply proxy settings to all requests.
 * If not passed static settings, they will be retrieved from the HTTPS_PROXY
 * or HTTP_PROXY environment variables.
 * @param proxySettings - ProxySettings to use on each request.
 * @param options - additional settings, for example, custom NO_PROXY patterns
 */
function proxyPolicy_proxyPolicy(proxySettings, options) {
    if (!noProxyListLoaded) {
        globalNoProxyList.push(...loadNoProxy());
    }
    const defaultProxy = proxySettings
        ? getUrlFromProxySettings(proxySettings)
        : getDefaultProxySettingsInternal();
    const cachedAgents = {};
    return {
        name: proxyPolicyName,
        async sendRequest(request, next) {
            if (!request.proxySettings &&
                defaultProxy &&
                !isBypassed(request.url, options?.customNoProxyList ?? globalNoProxyList, options?.customNoProxyList ? undefined : globalBypassedMap)) {
                setProxyAgentOnRequest(request, cachedAgents, defaultProxy);
            }
            else if (request.proxySettings) {
                setProxyAgentOnRequest(request, cachedAgents, getUrlFromProxySettings(request.proxySettings));
            }
            return next(request);
        },
    };
}
//# sourceMappingURL=proxyPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/typeGuards.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
function isNodeReadableStream(x) {
    return Boolean(x && typeof x["pipe"] === "function");
}
function isWebReadableStream(x) {
    return Boolean(x &&
        typeof x.getReader === "function" &&
        typeof x.tee === "function");
}
function typeGuards_isBinaryBody(body) {
    return (body !== undefined &&
        (body instanceof Uint8Array ||
            typeGuards_isReadableStream(body) ||
            typeof body === "function" ||
            (typeof Blob !== "undefined" && body instanceof Blob)));
}
function typeGuards_isReadableStream(x) {
    return isNodeReadableStream(x) || isWebReadableStream(x);
}
function typeGuards_isBlob(x) {
    return typeof Blob !== "undefined" && x instanceof Blob;
}
//# sourceMappingURL=typeGuards.js.map
// EXTERNAL MODULE: external "stream"
var external_stream_ = __nccwpck_require__(2203);
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/concat.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


async function* streamAsyncIterator() {
    const reader = this.getReader();
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                return;
            }
            yield value;
        }
    }
    finally {
        reader.releaseLock();
    }
}
function makeAsyncIterable(webStream) {
    if (!webStream[Symbol.asyncIterator]) {
        webStream[Symbol.asyncIterator] = streamAsyncIterator.bind(webStream);
    }
    if (!webStream.values) {
        webStream.values = streamAsyncIterator.bind(webStream);
    }
}
function ensureNodeStream(stream) {
    if (stream instanceof ReadableStream) {
        makeAsyncIterable(stream);
        return external_stream_.Readable.fromWeb(stream);
    }
    else {
        return stream;
    }
}
function toStream(source) {
    if (source instanceof Uint8Array) {
        return external_stream_.Readable.from(Buffer.from(source));
    }
    else if (typeGuards_isBlob(source)) {
        return ensureNodeStream(source.stream());
    }
    else {
        return ensureNodeStream(source);
    }
}
/**
 * Utility function that concatenates a set of binary inputs into one combined output.
 *
 * @param sources - array of sources for the concatenation
 * @returns - in Node, a (() =\> NodeJS.ReadableStream) which, when read, produces a concatenation of all the inputs.
 *           In browser, returns a `Blob` representing all the concatenated inputs.
 *
 * @internal
 */
async function concat(sources) {
    return function () {
        const streams = sources.map((x) => (typeof x === "function" ? x() : x)).map(toStream);
        return external_stream_.Readable.from((async function* () {
            for (const stream of streams) {
                for await (const chunk of stream) {
                    yield chunk;
                }
            }
        })());
    };
}
//# sourceMappingURL=concat.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/multipartPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




function generateBoundary() {
    return `----AzSDKFormBoundary${randomUUID()}`;
}
function encodeHeaders(headers) {
    let result = "";
    for (const [key, value] of headers) {
        result += `${key}: ${value}\r\n`;
    }
    return result;
}
function getLength(source) {
    if (source instanceof Uint8Array) {
        return source.byteLength;
    }
    else if (typeGuards_isBlob(source)) {
        // if was created using createFile then -1 means we have an unknown size
        return source.size === -1 ? undefined : source.size;
    }
    else {
        return undefined;
    }
}
function getTotalLength(sources) {
    let total = 0;
    for (const source of sources) {
        const partLength = getLength(source);
        if (partLength === undefined) {
            return undefined;
        }
        else {
            total += partLength;
        }
    }
    return total;
}
async function buildRequestBody(request, parts, boundary) {
    const sources = [
        bytesEncoding_stringToUint8Array(`--${boundary}`, "utf-8"),
        ...parts.flatMap((part) => [
            bytesEncoding_stringToUint8Array("\r\n", "utf-8"),
            bytesEncoding_stringToUint8Array(encodeHeaders(part.headers), "utf-8"),
            bytesEncoding_stringToUint8Array("\r\n", "utf-8"),
            part.body,
            bytesEncoding_stringToUint8Array(`\r\n--${boundary}`, "utf-8"),
        ]),
        bytesEncoding_stringToUint8Array("--\r\n\r\n", "utf-8"),
    ];
    const contentLength = getTotalLength(sources);
    if (contentLength) {
        request.headers.set("Content-Length", contentLength);
    }
    request.body = await concat(sources);
}
/**
 * Name of multipart policy
 */
const multipartPolicy_multipartPolicyName = "multipartPolicy";
const maxBoundaryLength = 70;
const validBoundaryCharacters = new Set(`abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'()+,-./:=?`);
function assertValidBoundary(boundary) {
    if (boundary.length > maxBoundaryLength) {
        throw new Error(`Multipart boundary "${boundary}" exceeds maximum length of 70 characters`);
    }
    if (Array.from(boundary).some((x) => !validBoundaryCharacters.has(x))) {
        throw new Error(`Multipart boundary "${boundary}" contains invalid characters`);
    }
}
/**
 * Pipeline policy for multipart requests
 */
function multipartPolicy_multipartPolicy() {
    return {
        name: multipartPolicy_multipartPolicyName,
        async sendRequest(request, next) {
            if (!request.multipartBody) {
                return next(request);
            }
            if (request.body) {
                throw new Error("multipartBody and regular body cannot be set at the same time");
            }
            let boundary = request.multipartBody.boundary;
            const contentTypeHeader = request.headers.get("Content-Type") ?? "multipart/mixed";
            const parsedHeader = contentTypeHeader.match(/^(multipart\/[^ ;]+)(?:; *boundary=(.+))?$/);
            if (!parsedHeader) {
                throw new Error(`Got multipart request body, but content-type header was not multipart: ${contentTypeHeader}`);
            }
            const [, contentType, parsedBoundary] = parsedHeader;
            if (parsedBoundary && boundary && parsedBoundary !== boundary) {
                throw new Error(`Multipart boundary was specified as ${parsedBoundary} in the header, but got ${boundary} in the request body`);
            }
            boundary ??= parsedBoundary;
            if (boundary) {
                assertValidBoundary(boundary);
            }
            else {
                boundary = generateBoundary();
            }
            request.headers.set("Content-Type", `${contentType}; boundary=${boundary}`);
            await buildRequestBody(request, request.multipartBody.parts, boundary);
            request.multipartBody = undefined;
            return next(request);
        },
    };
}
//# sourceMappingURL=multipartPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/createPipelineFromOptions.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.












/**
 * Create a new pipeline with a default set of customizable policies.
 * @param options - Options to configure a custom pipeline.
 */
function createPipelineFromOptions_createPipelineFromOptions(options) {
    const pipeline = createEmptyPipeline();
    if (isNodeLike) {
        if (options.agent) {
            pipeline.addPolicy(agentPolicy(options.agent));
        }
        if (options.tlsOptions) {
            pipeline.addPolicy(tlsPolicy(options.tlsOptions));
        }
        pipeline.addPolicy(proxyPolicy(options.proxyOptions));
        pipeline.addPolicy(decompressResponsePolicy());
    }
    pipeline.addPolicy(formDataPolicy(), { beforePolicies: [multipartPolicyName] });
    pipeline.addPolicy(userAgentPolicy(options.userAgentOptions));
    // The multipart policy is added after policies with no phase, so that
    // policies can be added between it and formDataPolicy to modify
    // properties (e.g., making the boundary constant in recorded tests).
    pipeline.addPolicy(multipartPolicy(), { afterPhase: "Deserialize" });
    pipeline.addPolicy(defaultRetryPolicy(options.retryOptions), { phase: "Retry" });
    if (isNodeLike) {
        // Both XHR and Fetch expect to handle redirects automatically,
        // so only include this policy when we're in Node.
        pipeline.addPolicy(redirectPolicy(options.redirectOptions), { afterPhase: "Retry" });
    }
    pipeline.addPolicy(logPolicy(options.loggingOptions), { afterPhase: "Sign" });
    return pipeline;
}
//# sourceMappingURL=createPipelineFromOptions.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/auth/checkInsecureConnection.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

// Ensure the warining is only emitted once
let insecureConnectionWarningEmmitted = false;
/**
 * Checks if the request is allowed to be sent over an insecure connection.
 *
 * A request is allowed to be sent over an insecure connection when:
 * - The `allowInsecureConnection` option is set to `true`.
 * - The request has the `allowInsecureConnection` property set to `true`.
 * - The request is being sent to `localhost` or `127.0.0.1`
 */
function allowInsecureConnection(request, options) {
    if (options.allowInsecureConnection && request.allowInsecureConnection) {
        const url = new URL(request.url);
        if (url.hostname === "localhost" || url.hostname === "127.0.0.1") {
            return true;
        }
    }
    return false;
}
/**
 * Logs a warning about sending a token over an insecure connection.
 *
 * This function will emit a node warning once, but log the warning every time.
 */
function emitInsecureConnectionWarning() {
    const warning = "Sending token over insecure transport. Assume any token issued is compromised.";
    logger.warning(warning);
    if (typeof process?.emitWarning === "function" && !insecureConnectionWarningEmmitted) {
        insecureConnectionWarningEmmitted = true;
        process.emitWarning(warning);
    }
}
/**
 * Ensures that authentication is only allowed over HTTPS unless explicitly allowed.
 * Throws an error if the connection is not secure and not explicitly allowed.
 */
function checkInsecureConnection_ensureSecureConnection(request, options) {
    if (!request.url.toLowerCase().startsWith("https://")) {
        if (allowInsecureConnection(request, options)) {
            emitInsecureConnectionWarning();
        }
        else {
            throw new Error("Authentication is not permitted for non-TLS protected (non-https) URLs when allowInsecureConnection is false.");
        }
    }
}
//# sourceMappingURL=checkInsecureConnection.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/auth/apiKeyAuthenticationPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Name of the API Key Authentication Policy
 */
const apiKeyAuthenticationPolicyName = "apiKeyAuthenticationPolicy";
/**
 * Gets a pipeline policy that adds API key authentication to requests
 */
function apiKeyAuthenticationPolicy_apiKeyAuthenticationPolicy(options) {
    return {
        name: apiKeyAuthenticationPolicyName,
        async sendRequest(request, next) {
            // Ensure allowInsecureConnection is explicitly set when sending request to non-https URLs
            ensureSecureConnection(request, options);
            const scheme = (request.authSchemes ?? options.authSchemes)?.find((x) => x.kind === "apiKey");
            // Skip adding authentication header if no API key authentication scheme is found
            if (!scheme) {
                return next(request);
            }
            if (scheme.apiKeyLocation !== "header") {
                throw new Error(`Unsupported API key location: ${scheme.apiKeyLocation}`);
            }
            request.headers.set(scheme.name, options.credential.key);
            return next(request);
        },
    };
}
//# sourceMappingURL=apiKeyAuthenticationPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/auth/basicAuthenticationPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * Name of the Basic Authentication Policy
 */
const basicAuthenticationPolicyName = "bearerAuthenticationPolicy";
/**
 * Gets a pipeline policy that adds basic authentication to requests
 */
function basicAuthenticationPolicy_basicAuthenticationPolicy(options) {
    return {
        name: basicAuthenticationPolicyName,
        async sendRequest(request, next) {
            // Ensure allowInsecureConnection is explicitly set when sending request to non-https URLs
            ensureSecureConnection(request, options);
            const scheme = (request.authSchemes ?? options.authSchemes)?.find((x) => x.kind === "http" && x.scheme === "basic");
            // Skip adding authentication header if no basic authentication scheme is found
            if (!scheme) {
                return next(request);
            }
            const { username, password } = options.credential;
            const headerValue = uint8ArrayToString(stringToUint8Array(`${username}:${password}`, "utf-8"), "base64");
            request.headers.set("Authorization", `Basic ${headerValue}`);
            return next(request);
        },
    };
}
//# sourceMappingURL=basicAuthenticationPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/auth/bearerAuthenticationPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Name of the Bearer Authentication Policy
 */
const bearerAuthenticationPolicyName = "bearerAuthenticationPolicy";
/**
 * Gets a pipeline policy that adds bearer token authentication to requests
 */
function bearerAuthenticationPolicy_bearerAuthenticationPolicy(options) {
    return {
        name: bearerAuthenticationPolicyName,
        async sendRequest(request, next) {
            // Ensure allowInsecureConnection is explicitly set when sending request to non-https URLs
            ensureSecureConnection(request, options);
            const scheme = (request.authSchemes ?? options.authSchemes)?.find((x) => x.kind === "http" && x.scheme === "bearer");
            // Skip adding authentication header if no bearer authentication scheme is found
            if (!scheme) {
                return next(request);
            }
            const token = await options.credential.getBearerToken({
                abortSignal: request.abortSignal,
            });
            request.headers.set("Authorization", `Bearer ${token}`);
            return next(request);
        },
    };
}
//# sourceMappingURL=bearerAuthenticationPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/auth/oauth2AuthenticationPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Name of the OAuth2 Authentication Policy
 */
const oauth2AuthenticationPolicyName = "oauth2AuthenticationPolicy";
/**
 * Gets a pipeline policy that adds authorization header from OAuth2 schemes
 */
function oauth2AuthenticationPolicy_oauth2AuthenticationPolicy(options) {
    return {
        name: oauth2AuthenticationPolicyName,
        async sendRequest(request, next) {
            // Ensure allowInsecureConnection is explicitly set when sending request to non-https URLs
            ensureSecureConnection(request, options);
            const scheme = (request.authSchemes ?? options.authSchemes)?.find((x) => x.kind === "oauth2");
            // Skip adding authentication header if no OAuth2 authentication scheme is found
            if (!scheme) {
                return next(request);
            }
            const token = await options.credential.getOAuth2Token(scheme.flows, {
                abortSignal: request.abortSignal,
            });
            request.headers.set("Authorization", `Bearer ${token}`);
            return next(request);
        },
    };
}
//# sourceMappingURL=oauth2AuthenticationPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/client/clientHelpers.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.








let cachedHttpClient;
/**
 * Creates a default rest pipeline to re-use accross Rest Level Clients
 */
function clientHelpers_createDefaultPipeline(options = {}) {
    const pipeline = createPipelineFromOptions(options);
    pipeline.addPolicy(apiVersionPolicy(options));
    const { credential, authSchemes, allowInsecureConnection } = options;
    if (credential) {
        if (isApiKeyCredential(credential)) {
            pipeline.addPolicy(apiKeyAuthenticationPolicy({ authSchemes, credential, allowInsecureConnection }));
        }
        else if (isBasicCredential(credential)) {
            pipeline.addPolicy(basicAuthenticationPolicy({ authSchemes, credential, allowInsecureConnection }));
        }
        else if (isBearerTokenCredential(credential)) {
            pipeline.addPolicy(bearerAuthenticationPolicy({ authSchemes, credential, allowInsecureConnection }));
        }
        else if (isOAuth2TokenCredential(credential)) {
            pipeline.addPolicy(oauth2AuthenticationPolicy({ authSchemes, credential, allowInsecureConnection }));
        }
    }
    return pipeline;
}
function clientHelpers_getCachedDefaultHttpsClient() {
    if (!cachedHttpClient) {
        cachedHttpClient = createDefaultHttpClient();
    }
    return cachedHttpClient;
}
//# sourceMappingURL=clientHelpers.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/client/multipart.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




/**
 * Get value of a header in the part descriptor ignoring case
 */
function getHeaderValue(descriptor, headerName) {
    if (descriptor.headers) {
        const actualHeaderName = Object.keys(descriptor.headers).find((x) => x.toLowerCase() === headerName.toLowerCase());
        if (actualHeaderName) {
            return descriptor.headers[actualHeaderName];
        }
    }
    return undefined;
}
function getPartContentType(descriptor) {
    const contentTypeHeader = getHeaderValue(descriptor, "content-type");
    if (contentTypeHeader) {
        return contentTypeHeader;
    }
    // Special value of null means content type is to be omitted
    if (descriptor.contentType === null) {
        return undefined;
    }
    if (descriptor.contentType) {
        return descriptor.contentType;
    }
    const { body } = descriptor;
    if (body === null || body === undefined) {
        return undefined;
    }
    if (typeof body === "string" || typeof body === "number" || typeof body === "boolean") {
        return "text/plain; charset=UTF-8";
    }
    if (body instanceof Blob) {
        return body.type || "application/octet-stream";
    }
    if (isBinaryBody(body)) {
        return "application/octet-stream";
    }
    // arbitrary non-text object -> generic JSON content type by default. We will try to JSON.stringify the body.
    return "application/json";
}
/**
 * Enclose value in quotes and escape special characters, for use in the Content-Disposition header
 */
function escapeDispositionField(value) {
    return JSON.stringify(value);
}
function getContentDisposition(descriptor) {
    const contentDispositionHeader = getHeaderValue(descriptor, "content-disposition");
    if (contentDispositionHeader) {
        return contentDispositionHeader;
    }
    if (descriptor.dispositionType === undefined &&
        descriptor.name === undefined &&
        descriptor.filename === undefined) {
        return undefined;
    }
    const dispositionType = descriptor.dispositionType ?? "form-data";
    let disposition = dispositionType;
    if (descriptor.name) {
        disposition += `; name=${escapeDispositionField(descriptor.name)}`;
    }
    let filename = undefined;
    if (descriptor.filename) {
        filename = descriptor.filename;
    }
    else if (typeof File !== "undefined" && descriptor.body instanceof File) {
        const filenameFromFile = descriptor.body.name;
        if (filenameFromFile !== "") {
            filename = filenameFromFile;
        }
    }
    if (filename) {
        disposition += `; filename=${escapeDispositionField(filename)}`;
    }
    return disposition;
}
function normalizeBody(body, contentType) {
    if (body === undefined) {
        // zero-length body
        return new Uint8Array([]);
    }
    // binary and primitives should go straight on the wire regardless of content type
    if (isBinaryBody(body)) {
        return body;
    }
    if (typeof body === "string" || typeof body === "number" || typeof body === "boolean") {
        return stringToUint8Array(String(body), "utf-8");
    }
    // stringify objects for JSON-ish content types e.g. application/json, application/merge-patch+json, application/vnd.oci.manifest.v1+json, application.json; charset=UTF-8
    if (contentType && /application\/(.+\+)?json(;.+)?/i.test(String(contentType))) {
        return stringToUint8Array(JSON.stringify(body), "utf-8");
    }
    throw new RestError(`Unsupported body/content-type combination: ${body}, ${contentType}`);
}
function buildBodyPart(descriptor) {
    const contentType = getPartContentType(descriptor);
    const contentDisposition = getContentDisposition(descriptor);
    const headers = createHttpHeaders(descriptor.headers ?? {});
    if (contentType) {
        headers.set("content-type", contentType);
    }
    if (contentDisposition) {
        headers.set("content-disposition", contentDisposition);
    }
    const body = normalizeBody(descriptor.body, contentType);
    return {
        headers,
        body,
    };
}
function multipart_buildMultipartBody(parts) {
    return { parts: parts.map(buildBodyPart) };
}
//# sourceMappingURL=multipart.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/client/sendRequest.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.






/**
 * Helper function to send request used by the client
 * @param method - method to use to send the request
 * @param url - url to send the request to
 * @param pipeline - pipeline with the policies to run when sending the request
 * @param options - request options
 * @param customHttpClient - a custom HttpClient to use when making the request
 * @returns returns and HttpResponse
 */
async function sendRequest_sendRequest(method, url, pipeline, options = {}, customHttpClient) {
    const httpClient = customHttpClient ?? getCachedDefaultHttpsClient();
    const request = buildPipelineRequest(method, url, options);
    try {
        const response = await pipeline.sendRequest(httpClient, request);
        const headers = response.headers.toJSON();
        const stream = response.readableStreamBody ?? response.browserStreamBody;
        const parsedBody = options.responseAsStream || stream !== undefined ? undefined : getResponseBody(response);
        const body = stream ?? parsedBody;
        if (options?.onResponse) {
            options.onResponse({ ...response, request, rawHeaders: headers, parsedBody });
        }
        return {
            request,
            headers,
            status: `${response.status}`,
            body,
        };
    }
    catch (e) {
        if (isRestError(e) && e.response && options.onResponse) {
            const { response } = e;
            const rawHeaders = response.headers.toJSON();
            // UNBRANDED DIFFERENCE: onResponse callback does not have a second __legacyError property
            options?.onResponse({ ...response, request, rawHeaders }, e);
        }
        throw e;
    }
}
/**
 * Function to determine the request content type
 * @param options - request options InternalRequestParameters
 * @returns returns the content-type
 */
function getRequestContentType(options = {}) {
    if (options.contentType) {
        return options.contentType;
    }
    const headerContentType = options.headers?.["content-type"];
    if (typeof headerContentType === "string") {
        return headerContentType;
    }
    return getContentType(options.body);
}
/**
 * Function to determine the content-type of a body
 * this is used if an explicit content-type is not provided
 * @param body - body in the request
 * @returns returns the content-type
 */
function getContentType(body) {
    if (body === undefined) {
        return undefined;
    }
    if (ArrayBuffer.isView(body)) {
        return "application/octet-stream";
    }
    if (isBlob(body) && body.type) {
        return body.type;
    }
    if (typeof body === "string") {
        try {
            JSON.parse(body);
            return "application/json";
        }
        catch (error) {
            // If we fail to parse the body, it is not json
            return undefined;
        }
    }
    // By default return json
    return "application/json";
}
function buildPipelineRequest(method, url, options = {}) {
    const requestContentType = getRequestContentType(options);
    const { body, multipartBody } = getRequestBody(options.body, requestContentType);
    const headers = createHttpHeaders({
        ...(options.headers ? options.headers : {}),
        accept: options.accept ?? options.headers?.accept ?? "application/json",
        ...(requestContentType && {
            "content-type": requestContentType,
        }),
    });
    return createPipelineRequest({
        url,
        method,
        body,
        multipartBody,
        headers,
        allowInsecureConnection: options.allowInsecureConnection,
        abortSignal: options.abortSignal,
        onUploadProgress: options.onUploadProgress,
        onDownloadProgress: options.onDownloadProgress,
        timeout: options.timeout,
        enableBrowserStreams: true,
        streamResponseStatusCodes: options.responseAsStream
            ? new Set([Number.POSITIVE_INFINITY])
            : undefined,
    });
}
/**
 * Prepares the body before sending the request
 */
function getRequestBody(body, contentType = "") {
    if (body === undefined) {
        return { body: undefined };
    }
    if (typeof FormData !== "undefined" && body instanceof FormData) {
        return { body };
    }
    if (isBlob(body)) {
        return { body };
    }
    if (isReadableStream(body)) {
        return { body };
    }
    if (typeof body === "function") {
        return { body: body };
    }
    if (ArrayBuffer.isView(body)) {
        return { body: body instanceof Uint8Array ? body : JSON.stringify(body) };
    }
    const firstType = contentType.split(";")[0];
    switch (firstType) {
        case "application/json":
            return { body: JSON.stringify(body) };
        case "multipart/form-data":
            if (Array.isArray(body)) {
                return { multipartBody: buildMultipartBody(body) };
            }
            return { body: JSON.stringify(body) };
        case "text/plain":
            return { body: String(body) };
        default:
            if (typeof body === "string") {
                return { body };
            }
            return { body: JSON.stringify(body) };
    }
}
/**
 * Prepares the response body
 */
function getResponseBody(response) {
    // Set the default response type
    const contentType = response.headers.get("content-type") ?? "";
    const firstType = contentType.split(";")[0];
    const bodyToParse = response.bodyAsText ?? "";
    if (firstType === "text/plain") {
        return String(bodyToParse);
    }
    // Default to "application/json" and fallback to string;
    try {
        return bodyToParse ? JSON.parse(bodyToParse) : undefined;
    }
    catch (error) {
        // If we were supposed to get a JSON object and failed to
        // parse, throw a parse error
        if (firstType === "application/json") {
            throw createParseError(response, error);
        }
        // We are not sure how to handle the response so we return it as
        // plain text.
        return String(bodyToParse);
    }
}
function createParseError(response, err) {
    const msg = `Error "${err}" occurred while parsing the response body - ${response.bodyAsText}.`;
    const errCode = err.code ?? RestError.PARSE_ERROR;
    return new RestError(msg, {
        code: errCode,
        statusCode: response.status,
        request: response.request,
        response: response,
    });
}
//# sourceMappingURL=sendRequest.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/client/getClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




/**
 * Creates a client with a default pipeline
 * @param endpoint - Base endpoint for the client
 * @param credentials - Credentials to authenticate the requests
 * @param options - Client options
 */
function getClient(endpoint, clientOptions = {}) {
    const pipeline = clientOptions.pipeline ?? createDefaultPipeline(clientOptions);
    if (clientOptions.additionalPolicies?.length) {
        for (const { policy, position } of clientOptions.additionalPolicies) {
            // Sign happens after Retry and is commonly needed to occur
            // before policies that intercept post-retry.
            const afterPhase = position === "perRetry" ? "Sign" : undefined;
            pipeline.addPolicy(policy, {
                afterPhase,
            });
        }
    }
    const { allowInsecureConnection, httpClient } = clientOptions;
    const endpointUrl = clientOptions.endpoint ?? endpoint;
    const client = (path, ...args) => {
        const getUrl = (requestOptions) => buildRequestUrl(endpointUrl, path, args, { allowInsecureConnection, ...requestOptions });
        return {
            get: (requestOptions = {}) => {
                return buildOperation("GET", getUrl(requestOptions), pipeline, requestOptions, allowInsecureConnection, httpClient);
            },
            post: (requestOptions = {}) => {
                return buildOperation("POST", getUrl(requestOptions), pipeline, requestOptions, allowInsecureConnection, httpClient);
            },
            put: (requestOptions = {}) => {
                return buildOperation("PUT", getUrl(requestOptions), pipeline, requestOptions, allowInsecureConnection, httpClient);
            },
            patch: (requestOptions = {}) => {
                return buildOperation("PATCH", getUrl(requestOptions), pipeline, requestOptions, allowInsecureConnection, httpClient);
            },
            delete: (requestOptions = {}) => {
                return buildOperation("DELETE", getUrl(requestOptions), pipeline, requestOptions, allowInsecureConnection, httpClient);
            },
            head: (requestOptions = {}) => {
                return buildOperation("HEAD", getUrl(requestOptions), pipeline, requestOptions, allowInsecureConnection, httpClient);
            },
            options: (requestOptions = {}) => {
                return buildOperation("OPTIONS", getUrl(requestOptions), pipeline, requestOptions, allowInsecureConnection, httpClient);
            },
            trace: (requestOptions = {}) => {
                return buildOperation("TRACE", getUrl(requestOptions), pipeline, requestOptions, allowInsecureConnection, httpClient);
            },
        };
    };
    return {
        path: client,
        pathUnchecked: client,
        pipeline,
    };
}
function buildOperation(method, url, pipeline, options, allowInsecureConnection, httpClient) {
    allowInsecureConnection = options.allowInsecureConnection ?? allowInsecureConnection;
    return {
        then: function (onFulfilled, onrejected) {
            return sendRequest(method, url, pipeline, { ...options, allowInsecureConnection }, httpClient).then(onFulfilled, onrejected);
        },
        async asBrowserStream() {
            if (isNodeLike) {
                throw new Error("`asBrowserStream` is supported only in the browser environment. Use `asNodeStream` instead to obtain the response body stream. If you require a Web stream of the response in Node, consider using `Readable.toWeb` on the result of `asNodeStream`.");
            }
            else {
                return sendRequest(method, url, pipeline, { ...options, allowInsecureConnection, responseAsStream: true }, httpClient);
            }
        },
        async asNodeStream() {
            if (isNodeLike) {
                return sendRequest(method, url, pipeline, { ...options, allowInsecureConnection, responseAsStream: true }, httpClient);
            }
            else {
                throw new Error("`isNodeStream` is not supported in the browser environment. Use `asBrowserStream` to obtain the response body stream.");
            }
        },
    };
}
//# sourceMappingURL=getClient.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/client/restError.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


function createRestError(messageOrResponse, response) {
    const resp = typeof messageOrResponse === "string" ? response : messageOrResponse;
    const internalError = resp.body?.error ?? resp.body;
    const message = typeof messageOrResponse === "string"
        ? messageOrResponse
        : (internalError?.message ?? `Unexpected status code: ${resp.status}`);
    return new RestError(message, {
        statusCode: statusCodeToNumber(resp.status),
        code: internalError?.code,
        request: resp.request,
        response: toPipelineResponse(resp),
    });
}
function toPipelineResponse(response) {
    return {
        headers: createHttpHeaders(response.headers),
        request: response.request,
        status: statusCodeToNumber(response.status) ?? -1,
    };
}
function statusCodeToNumber(statusCode) {
    const status = Number.parseInt(statusCode);
    return Number.isNaN(status) ? undefined : status;
}
//# sourceMappingURL=restError.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.











//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/pipeline.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Creates a totally empty pipeline.
 * Useful for testing or creating a custom one.
 */
function esm_pipeline_createEmptyPipeline() {
    return pipeline_createEmptyPipeline();
}
//# sourceMappingURL=pipeline.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/logger/internal.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//# sourceMappingURL=internal.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/logger/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const esm_context = createLoggerContext({
    logLevelEnvVarName: "AZURE_LOG_LEVEL",
    namespace: "azure",
});
/**
 * The AzureLogger provides a mechanism for overriding where logs are output to.
 * By default, logs are sent to stderr.
 * Override the `log` method to redirect logs to another location.
 */
const AzureLogger = esm_context.logger;
/**
 * Immediately enables logging at the specified log level. If no level is specified, logging is disabled.
 * @param level - The log level to enable for logging.
 * Options from most verbose to least verbose are:
 * - verbose
 * - info
 * - warning
 * - error
 */
function esm_setLogLevel(level) {
    esm_context.setLogLevel(level);
}
/**
 * Retrieves the currently specified log level.
 */
function esm_getLogLevel() {
    return esm_context.getLogLevel();
}
/**
 * Creates a logger for use by the Azure SDKs that inherits from `AzureLogger`.
 * @param namespace - The name of the SDK package.
 * @hidden
 */
function esm_createClientLogger(namespace) {
    return esm_context.createClientLogger(namespace);
}
//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/log.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const esm_log_logger = esm_createClientLogger("core-rest-pipeline");
//# sourceMappingURL=log.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/agentPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Name of the Agent Policy
 */
const agentPolicyName = "agentPolicy";
/**
 * Gets a pipeline policy that sets http.agent
 */
function agentPolicy_agentPolicy(agent) {
    return {
        name: agentPolicyName,
        sendRequest: async (req, next) => {
            // Users may define an agent on the request, honor it over the client level one
            if (!req.agent) {
                req.agent = agent;
            }
            return next(req);
        },
    };
}
//# sourceMappingURL=agentPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/decompressResponsePolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * The programmatic identifier of the decompressResponsePolicy.
 */
const decompressResponsePolicyName = "decompressResponsePolicy";
/**
 * A policy to enable response decompression according to Accept-Encoding header
 * https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Encoding
 */
function decompressResponsePolicy_decompressResponsePolicy() {
    return {
        name: decompressResponsePolicyName,
        async sendRequest(request, next) {
            // HEAD requests have no body
            if (request.method !== "HEAD") {
                request.headers.set("Accept-Encoding", "gzip,deflate");
            }
            return next(request);
        },
    };
}
//# sourceMappingURL=decompressResponsePolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/exponentialRetryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * The programmatic identifier of the exponentialRetryPolicy.
 */
const exponentialRetryPolicyName = "exponentialRetryPolicy";
/**
 * A policy that attempts to retry requests while introducing an exponentially increasing delay.
 * @param options - Options that configure retry logic.
 */
function exponentialRetryPolicy(options = {}) {
    return retryPolicy([
        exponentialRetryStrategy({
            ...options,
            ignoreSystemErrors: true,
        }),
    ], {
        maxRetries: options.maxRetries ?? DEFAULT_RETRY_POLICY_COUNT,
    });
}
//# sourceMappingURL=exponentialRetryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/systemErrorRetryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * Name of the {@link systemErrorRetryPolicy}
 */
const systemErrorRetryPolicyName = "systemErrorRetryPolicy";
/**
 * A retry policy that specifically seeks to handle errors in the
 * underlying transport layer (e.g. DNS lookup failures) rather than
 * retryable error codes from the server itself.
 * @param options - Options that customize the policy.
 */
function systemErrorRetryPolicy(options = {}) {
    return {
        name: systemErrorRetryPolicyName,
        sendRequest: retryPolicy([
            exponentialRetryStrategy({
                ...options,
                ignoreHttpStatusCodes: true,
            }),
        ], {
            maxRetries: options.maxRetries ?? DEFAULT_RETRY_POLICY_COUNT,
        }).sendRequest,
    };
}
//# sourceMappingURL=systemErrorRetryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/throttlingRetryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * Name of the {@link throttlingRetryPolicy}
 */
const throttlingRetryPolicyName = "throttlingRetryPolicy";
/**
 * A policy that retries when the server sends a 429 response with a Retry-After header.
 *
 * To learn more, please refer to
 * https://learn.microsoft.com/azure/azure-resource-manager/resource-manager-request-limits,
 * https://learn.microsoft.com/azure/azure-subscription-service-limits and
 * https://learn.microsoft.com/azure/virtual-machines/troubleshooting/troubleshooting-throttling-errors
 *
 * @param options - Options that configure retry logic.
 */
function throttlingRetryPolicy(options = {}) {
    return {
        name: throttlingRetryPolicyName,
        sendRequest: retryPolicy([throttlingRetryStrategy()], {
            maxRetries: options.maxRetries ?? DEFAULT_RETRY_POLICY_COUNT,
        }).sendRequest,
    };
}
//# sourceMappingURL=throttlingRetryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/tlsPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Name of the TLS Policy
 */
const tlsPolicyName = "tlsPolicy";
/**
 * Gets a pipeline policy that adds the client certificate to the HttpClient agent for authentication.
 */
function tlsPolicy_tlsPolicy(tlsSettings) {
    return {
        name: tlsPolicyName,
        sendRequest: async (req, next) => {
            // Users may define a request tlsSettings, honor those over the client level one
            if (!req.tlsSettings) {
                req.tlsSettings = tlsSettings;
            }
            return next(req);
        },
    };
}
//# sourceMappingURL=tlsPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/policies/internal.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.














//# sourceMappingURL=internal.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/logPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * The programmatic identifier of the logPolicy.
 */
const logPolicy_logPolicyName = (/* unused pure expression or super */ null && (tspLogPolicyName));
/**
 * A policy that logs all requests and responses.
 * @param options - Options to configure logPolicy.
 */
function policies_logPolicy_logPolicy(options = {}) {
    return logPolicy_logPolicy({
        logger: esm_log_logger.info,
        ...options,
    });
}
//# sourceMappingURL=logPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/redirectPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * The programmatic identifier of the redirectPolicy.
 */
const redirectPolicy_redirectPolicyName = redirectPolicyName;
/**
 * A policy to follow Location headers from the server in order
 * to support server-side redirection.
 * In the browser, this policy is not used.
 * @param options - Options to control policy behavior.
 */
function policies_redirectPolicy_redirectPolicy(options = {}) {
    return redirectPolicy_redirectPolicy(options);
}
//# sourceMappingURL=redirectPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/util/userAgentPlatform.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * @internal
 */
function userAgentPlatform_getHeaderName() {
    return "User-Agent";
}
/**
 * @internal
 */
async function util_userAgentPlatform_setPlatformSpecificData(map) {
    if (external_node_process_namespaceObject && external_node_process_namespaceObject.versions) {
        const osInfo = `${external_node_os_namespaceObject.type()} ${external_node_os_namespaceObject.release()}; ${external_node_os_namespaceObject.arch()}`;
        const versions = external_node_process_namespaceObject.versions;
        if (versions.bun) {
            map.set("Bun", `${versions.bun} (${osInfo})`);
        }
        else if (versions.deno) {
            map.set("Deno", `${versions.deno} (${osInfo})`);
        }
        else if (versions.node) {
            map.set("Node", `${versions.node} (${osInfo})`);
        }
    }
}
//# sourceMappingURL=userAgentPlatform.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/constants.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
const esm_constants_SDK_VERSION = "1.22.2";
const esm_constants_DEFAULT_RETRY_POLICY_COUNT = 3;
//# sourceMappingURL=constants.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/util/userAgent.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


function util_userAgent_getUserAgentString(telemetryInfo) {
    const parts = [];
    for (const [key, value] of telemetryInfo) {
        const token = value ? `${key}/${value}` : key;
        parts.push(token);
    }
    return parts.join(" ");
}
/**
 * @internal
 */
function userAgent_getUserAgentHeaderName() {
    return userAgentPlatform_getHeaderName();
}
/**
 * @internal
 */
async function util_userAgent_getUserAgentValue(prefix) {
    const runtimeInfo = new Map();
    runtimeInfo.set("core-rest-pipeline", esm_constants_SDK_VERSION);
    await util_userAgentPlatform_setPlatformSpecificData(runtimeInfo);
    const defaultAgent = util_userAgent_getUserAgentString(runtimeInfo);
    const userAgentValue = prefix ? `${prefix} ${defaultAgent}` : defaultAgent;
    return userAgentValue;
}
//# sourceMappingURL=userAgent.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/userAgentPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const userAgentPolicy_UserAgentHeaderName = userAgent_getUserAgentHeaderName();
/**
 * The programmatic identifier of the userAgentPolicy.
 */
const userAgentPolicy_userAgentPolicyName = "userAgentPolicy";
/**
 * A policy that sets the User-Agent header (or equivalent) to reflect
 * the library version.
 * @param options - Options to customize the user agent value.
 */
function policies_userAgentPolicy_userAgentPolicy(options = {}) {
    const userAgentValue = util_userAgent_getUserAgentValue(options.userAgentPrefix);
    return {
        name: userAgentPolicy_userAgentPolicyName,
        async sendRequest(request, next) {
            if (!request.headers.has(userAgentPolicy_UserAgentHeaderName)) {
                request.headers.set(userAgentPolicy_UserAgentHeaderName, await userAgentValue);
            }
            return next(request);
        },
    };
}
//# sourceMappingURL=userAgentPolicy.js.map
// EXTERNAL MODULE: external "node:crypto"
var external_node_crypto_ = __nccwpck_require__(7598);
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/sha256.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Generates a SHA-256 HMAC signature.
 * @param key - The HMAC key represented as a base64 string, used to generate the cryptographic HMAC hash.
 * @param stringToSign - The data to be signed.
 * @param encoding - The textual encoding to use for the returned HMAC digest.
 */
async function computeSha256Hmac(key, stringToSign, encoding) {
    const decodedKey = Buffer.from(key, "base64");
    return createHmac("sha256", decodedKey).update(stringToSign).digest(encoding);
}
/**
 * Generates a SHA-256 hash.
 * @param content - The data to be included in the hash.
 * @param encoding - The textual encoding to use for the returned hash.
 */
async function computeSha256Hash(content, encoding) {
    return createHash("sha256").update(content).digest(encoding);
}
//# sourceMappingURL=sha256.js.map
;// CONCATENATED MODULE: ./node_modules/@typespec/ts-http-runtime/dist/esm/util/internal.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.









//# sourceMappingURL=internal.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/abort-controller/dist/esm/AbortError.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.
/**
 * This error is thrown when an asynchronous operation has been aborted.
 * Check for this error by testing the `name` that the name property of the
 * error matches `"AbortError"`.
 *
 * @example
 * ```ts
 * const controller = new AbortController();
 * controller.abort();
 * try {
 *   doAsyncWork(controller.signal)
 * } catch (e) {
 *   if (e.name === 'AbortError') {
 *     // handle abort error here.
 *   }
 * }
 * ```
 */
class AbortError_AbortError extends Error {
    constructor(message) {
        super(message);
        this.name = "AbortError";
    }
}
//# sourceMappingURL=AbortError.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/abort-controller/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-util/dist/esm/createAbortablePromise.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Creates an abortable promise.
 * @param buildPromise - A function that takes the resolve and reject functions as parameters.
 * @param options - The options for the abortable promise.
 * @returns A promise that can be aborted.
 */
function createAbortablePromise(buildPromise, options) {
    const { cleanupBeforeAbort, abortSignal, abortErrorMsg } = options ?? {};
    return new Promise((resolve, reject) => {
        function rejectOnAbort() {
            reject(new AbortError_AbortError(abortErrorMsg ?? "The operation was aborted."));
        }
        function removeListeners() {
            abortSignal?.removeEventListener("abort", onAbort);
        }
        function onAbort() {
            cleanupBeforeAbort?.();
            removeListeners();
            rejectOnAbort();
        }
        if (abortSignal?.aborted) {
            return rejectOnAbort();
        }
        try {
            buildPromise((x) => {
                removeListeners();
                resolve(x);
            }, (x) => {
                removeListeners();
                reject(x);
            });
        }
        catch (err) {
            reject(err);
        }
        abortSignal?.addEventListener("abort", onAbort);
    });
}
//# sourceMappingURL=createAbortablePromise.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-util/dist/esm/delay.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


const delay_StandardAbortMessage = "The delay was aborted.";
/**
 * A wrapper for setTimeout that resolves a promise after timeInMs milliseconds.
 * @param timeInMs - The number of milliseconds to be delayed.
 * @param options - The options for delay - currently abort options
 * @returns Promise that is resolved after timeInMs
 */
function delay_delay(timeInMs, options) {
    let token;
    const { abortSignal, abortErrorMsg } = options ?? {};
    return createAbortablePromise((resolve) => {
        token = setTimeout(resolve, timeInMs);
    }, {
        cleanupBeforeAbort: () => clearTimeout(token),
        abortSignal,
        abortErrorMsg: abortErrorMsg ?? delay_StandardAbortMessage,
    });
}
/**
 * Calculates the delay interval for retry attempts using exponential delay with jitter.
 * @param retryAttempt - The current retry attempt number.
 * @param config - The exponential retry configuration.
 * @returns An object containing the calculated retry delay.
 */
function delay_calculateRetryDelay(retryAttempt, config) {
    // Exponentially increase the delay each time
    const exponentialDelay = config.retryDelayInMs * Math.pow(2, retryAttempt);
    // Don't let the delay exceed the maximum
    const clampedDelay = Math.min(config.maxRetryDelayInMs, exponentialDelay);
    // Allow the final value to have some "jitter" (within 50% of the delay size) so
    // that retries across multiple clients don't occur simultaneously.
    const retryAfterInMs = clampedDelay / 2 + getRandomIntegerInclusive(0, clampedDelay / 2);
    return { retryAfterInMs };
}
//# sourceMappingURL=delay.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-util/dist/esm/error.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Given what is thought to be an error object, return the message if possible.
 * If the message is missing, returns a stringified version of the input.
 * @param e - Something thrown from a try block
 * @returns The error message or a string of the input
 */
function getErrorMessage(e) {
    if (isError(e)) {
        return e.message;
    }
    else {
        let stringified;
        try {
            if (typeof e === "object" && e) {
                stringified = JSON.stringify(e);
            }
            else {
                stringified = String(e);
            }
        }
        catch (err) {
            stringified = "[unable to stringify input]";
        }
        return `Unknown error ${stringified}`;
    }
}
//# sourceMappingURL=error.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-util/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.






/**
 * Calculates the delay interval for retry attempts using exponential delay with jitter.
 *
 * @param retryAttempt - The current retry attempt number.
 *
 * @param config - The exponential retry configuration.
 *
 * @returns An object containing the calculated retry delay.
 */
function esm_calculateRetryDelay(retryAttempt, config) {
    return tspRuntime.calculateRetryDelay(retryAttempt, config);
}
/**
 * Generates a SHA-256 hash.
 *
 * @param content - The data to be included in the hash.
 *
 * @param encoding - The textual encoding to use for the returned hash.
 */
function esm_computeSha256Hash(content, encoding) {
    return tspRuntime.computeSha256Hash(content, encoding);
}
/**
 * Generates a SHA-256 HMAC signature.
 *
 * @param key - The HMAC key represented as a base64 string, used to generate the cryptographic HMAC hash.
 *
 * @param stringToSign - The data to be signed.
 *
 * @param encoding - The textual encoding to use for the returned HMAC digest.
 */
function esm_computeSha256Hmac(key, stringToSign, encoding) {
    return tspRuntime.computeSha256Hmac(key, stringToSign, encoding);
}
/**
 * Returns a random integer value between a lower and upper bound, inclusive of both bounds. Note that this uses Math.random and isn't secure. If you need to use this for any kind of security purpose, find a better source of random.
 *
 * @param min - The smallest integer value allowed.
 *
 * @param max - The largest integer value allowed.
 */
function esm_getRandomIntegerInclusive(min, max) {
    return tspRuntime.getRandomIntegerInclusive(min, max);
}
/**
 * Typeguard for an error object shape (has name and message)
 *
 * @param e - Something caught by a catch clause.
 */
function esm_isError(e) {
    return isError(e);
}
/**
 * Helper to determine when an input is a generic JS object.
 *
 * @returns true when input is an object type that is not null, Array, RegExp, or Date.
 */
function esm_isObject(input) {
    return tspRuntime.isObject(input);
}
/**
 * Generated Universally Unique Identifier
 *
 * @returns RFC4122 v4 UUID.
 */
function esm_randomUUID() {
    return randomUUID();
}
/**
 * A constant that indicates whether the environment the code is running is a Web Browser.
 */
const esm_isBrowser = isBrowser;
/**
 * A constant that indicates whether the environment the code is running is Bun.sh.
 */
const esm_isBun = isBun;
/**
 * A constant that indicates whether the environment the code is running is Deno.
 */
const esm_isDeno = isDeno;
/**
 * A constant that indicates whether the environment the code is running is a Node.js compatible environment.
 *
 * @deprecated
 *
 * Use `isNodeLike` instead.
 */
const isNode = checkEnvironment_isNodeLike;
/**
 * A constant that indicates whether the environment the code is running is a Node.js compatible environment.
 */
const esm_isNodeLike = checkEnvironment_isNodeLike;
/**
 * A constant that indicates whether the environment the code is running is Node.JS.
 */
const esm_isNodeRuntime = isNodeRuntime;
/**
 * A constant that indicates whether the environment the code is running is in React-Native.
 */
const esm_isReactNative = isReactNative;
/**
 * A constant that indicates whether the environment the code is running is a Web Worker.
 */
const esm_isWebWorker = isWebWorker;
/**
 * The helper that transforms bytes with specific character encoding into string
 * @param bytes - the uint8array bytes
 * @param format - the format we use to encode the byte
 * @returns a string of the encoded string
 */
function esm_uint8ArrayToString(bytes, format) {
    return tspRuntime.uint8ArrayToString(bytes, format);
}
/**
 * The helper that transforms string to specific character encoded bytes array.
 * @param value - the string to be converted
 * @param format - the format we use to decode the value
 * @returns a uint8array
 */
function esm_stringToUint8Array(value, format) {
    return tspRuntime.stringToUint8Array(value, format);
}
//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/util/file.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

function file_isNodeReadableStream(x) {
    return Boolean(x && typeof x["pipe"] === "function");
}
const unimplementedMethods = {
    arrayBuffer: () => {
        throw new Error("Not implemented");
    },
    bytes: () => {
        throw new Error("Not implemented");
    },
    slice: () => {
        throw new Error("Not implemented");
    },
    text: () => {
        throw new Error("Not implemented");
    },
};
/**
 * Private symbol used as key on objects created using createFile containing the
 * original source of the file object.
 *
 * This is used in Node to access the original Node stream without using Blob#stream, which
 * returns a web stream. This is done to avoid a couple of bugs to do with Blob#stream and
 * Readable#to/fromWeb in Node versions we support:
 * - https://github.com/nodejs/node/issues/42694 (fixed in Node 18.14)
 * - https://github.com/nodejs/node/issues/48916 (fixed in Node 20.6)
 *
 * Once these versions are no longer supported, we may be able to stop doing this.
 *
 * @internal
 */
const rawContent = Symbol("rawContent");
/**
 * Type guard to check if a given object is a blob-like object with a raw content property.
 */
function hasRawContent(x) {
    return typeof x[rawContent] === "function";
}
/**
 * Extract the raw content from a given blob-like object. If the input was created using createFile
 * or createFileFromStream, the exact content passed into createFile/createFileFromStream will be used.
 * For true instances of Blob and File, returns the actual blob.
 *
 * @internal
 */
function getRawContent(blob) {
    if (hasRawContent(blob)) {
        return blob[rawContent]();
    }
    else {
        return blob;
    }
}
/**
 * Create an object that implements the File interface. This object is intended to be
 * passed into RequestBodyType.formData, and is not guaranteed to work as expected in
 * other situations.
 *
 * Use this function to:
 * - Create a File object for use in RequestBodyType.formData in environments where the
 *   global File object is unavailable.
 * - Create a File-like object from a readable stream without reading the stream into memory.
 *
 * @param stream - the content of the file as a callback returning a stream. When a File object made using createFile is
 *                  passed in a request's form data map, the stream will not be read into memory
 *                  and instead will be streamed when the request is made. In the event of a retry, the
 *                  stream needs to be read again, so this callback SHOULD return a fresh stream if possible.
 * @param name - the name of the file.
 * @param options - optional metadata about the file, e.g. file name, file size, MIME type.
 */
function createFileFromStream(stream, name, options = {}) {
    return {
        ...unimplementedMethods,
        type: options.type ?? "",
        lastModified: options.lastModified ?? new Date().getTime(),
        webkitRelativePath: options.webkitRelativePath ?? "",
        size: options.size ?? -1,
        name,
        stream: () => {
            const s = stream();
            if (file_isNodeReadableStream(s)) {
                throw new Error("Not supported: a Node stream was provided as input to createFileFromStream.");
            }
            return s;
        },
        [rawContent]: stream,
    };
}
/**
 * Create an object that implements the File interface. This object is intended to be
 * passed into RequestBodyType.formData, and is not guaranteed to work as expected in
 * other situations.
 *
 * Use this function create a File object for use in RequestBodyType.formData in environments where the global File object is unavailable.
 *
 * @param content - the content of the file as a Uint8Array in memory.
 * @param name - the name of the file.
 * @param options - optional metadata about the file, e.g. file name, file size, MIME type.
 */
function createFile(content, name, options = {}) {
    if (isNodeLike) {
        return {
            ...unimplementedMethods,
            type: options.type ?? "",
            lastModified: options.lastModified ?? new Date().getTime(),
            webkitRelativePath: options.webkitRelativePath ?? "",
            size: content.byteLength,
            name,
            arrayBuffer: async () => content.buffer,
            stream: () => new Blob([toArrayBuffer(content)]).stream(),
            [rawContent]: () => content,
        };
    }
    else {
        return new File([toArrayBuffer(content)], name, options);
    }
}
function toArrayBuffer(source) {
    if ("resize" in source.buffer) {
        // ArrayBuffer
        return source;
    }
    // SharedArrayBuffer
    return source.map((x) => x);
}
//# sourceMappingURL=file.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/multipartPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * Name of multipart policy
 */
const policies_multipartPolicy_multipartPolicyName = multipartPolicy_multipartPolicyName;
/**
 * Pipeline policy for multipart requests
 */
function policies_multipartPolicy_multipartPolicy() {
    const tspPolicy = multipartPolicy_multipartPolicy();
    return {
        name: policies_multipartPolicy_multipartPolicyName,
        sendRequest: async (request, next) => {
            if (request.multipartBody) {
                for (const part of request.multipartBody.parts) {
                    if (hasRawContent(part.body)) {
                        part.body = getRawContent(part.body);
                    }
                }
            }
            return tspPolicy.sendRequest(request, next);
        },
    };
}
//# sourceMappingURL=multipartPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/decompressResponsePolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * The programmatic identifier of the decompressResponsePolicy.
 */
const decompressResponsePolicy_decompressResponsePolicyName = decompressResponsePolicyName;
/**
 * A policy to enable response decompression according to Accept-Encoding header
 * https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Encoding
 */
function policies_decompressResponsePolicy_decompressResponsePolicy() {
    return decompressResponsePolicy_decompressResponsePolicy();
}
//# sourceMappingURL=decompressResponsePolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/defaultRetryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Name of the {@link defaultRetryPolicy}
 */
const defaultRetryPolicy_defaultRetryPolicyName = (/* unused pure expression or super */ null && (tspDefaultRetryPolicyName));
/**
 * A policy that retries according to three strategies:
 * - When the server sends a 429 response with a Retry-After header.
 * - When there are errors in the underlying transport layer (e.g. DNS lookup failures).
 * - Or otherwise if the outgoing request fails, it will retry with an exponentially increasing delay.
 */
function policies_defaultRetryPolicy_defaultRetryPolicy(options = {}) {
    return defaultRetryPolicy_defaultRetryPolicy(options);
}
//# sourceMappingURL=defaultRetryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/formDataPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * The programmatic identifier of the formDataPolicy.
 */
const formDataPolicy_formDataPolicyName = (/* unused pure expression or super */ null && (tspFormDataPolicyName));
/**
 * A policy that encodes FormData on the request into the body.
 */
function policies_formDataPolicy_formDataPolicy() {
    return formDataPolicy_formDataPolicy();
}
//# sourceMappingURL=formDataPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/proxyPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * The programmatic identifier of the proxyPolicy.
 */
const proxyPolicy_proxyPolicyName = (/* unused pure expression or super */ null && (tspProxyPolicyName));
/**
 * This method converts a proxy url into `ProxySettings` for use with ProxyPolicy.
 * If no argument is given, it attempts to parse a proxy URL from the environment
 * variables `HTTPS_PROXY` or `HTTP_PROXY`.
 * @param proxyUrl - The url of the proxy to use. May contain authentication information.
 * @deprecated - Internally this method is no longer necessary when setting proxy information.
 */
function proxyPolicy_getDefaultProxySettings(proxyUrl) {
    return getDefaultProxySettings(proxyUrl);
}
/**
 * A policy that allows one to apply proxy settings to all requests.
 * If not passed static settings, they will be retrieved from the HTTPS_PROXY
 * or HTTP_PROXY environment variables.
 * @param proxySettings - ProxySettings to use on each request.
 * @param options - additional settings, for example, custom NO_PROXY patterns
 */
function policies_proxyPolicy_proxyPolicy(proxySettings, options) {
    return proxyPolicy_proxyPolicy(proxySettings, options);
}
//# sourceMappingURL=proxyPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/setClientRequestIdPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * The programmatic identifier of the setClientRequestIdPolicy.
 */
const setClientRequestIdPolicyName = "setClientRequestIdPolicy";
/**
 * Each PipelineRequest gets a unique id upon creation.
 * This policy passes that unique id along via an HTTP header to enable better
 * telemetry and tracing.
 * @param requestIdHeaderName - The name of the header to pass the request ID to.
 */
function setClientRequestIdPolicy(requestIdHeaderName = "x-ms-client-request-id") {
    return {
        name: setClientRequestIdPolicyName,
        async sendRequest(request, next) {
            if (!request.headers.has(requestIdHeaderName)) {
                request.headers.set(requestIdHeaderName, request.requestId);
            }
            return next(request);
        },
    };
}
//# sourceMappingURL=setClientRequestIdPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/agentPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Name of the Agent Policy
 */
const agentPolicy_agentPolicyName = (/* unused pure expression or super */ null && (tspAgentPolicyName));
/**
 * Gets a pipeline policy that sets http.agent
 */
function policies_agentPolicy_agentPolicy(agent) {
    return agentPolicy_agentPolicy(agent);
}
//# sourceMappingURL=agentPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/tlsPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Name of the TLS Policy
 */
const tlsPolicy_tlsPolicyName = (/* unused pure expression or super */ null && (tspTlsPolicyName));
/**
 * Gets a pipeline policy that adds the client certificate to the HttpClient agent for authentication.
 */
function policies_tlsPolicy_tlsPolicy(tlsSettings) {
    return tlsPolicy_tlsPolicy(tlsSettings);
}
//# sourceMappingURL=tlsPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-tracing/dist/esm/tracingContext.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/** @internal */
const knownContextKeys = {
    span: Symbol.for("@azure/core-tracing span"),
    namespace: Symbol.for("@azure/core-tracing namespace"),
};
/**
 * Creates a new {@link TracingContext} with the given options.
 * @param options - A set of known keys that may be set on the context.
 * @returns A new {@link TracingContext} with the given options.
 *
 * @internal
 */
function createTracingContext(options = {}) {
    let context = new TracingContextImpl(options.parentContext);
    if (options.span) {
        context = context.setValue(knownContextKeys.span, options.span);
    }
    if (options.namespace) {
        context = context.setValue(knownContextKeys.namespace, options.namespace);
    }
    return context;
}
/** @internal */
class TracingContextImpl {
    _contextMap;
    constructor(initialContext) {
        this._contextMap =
            initialContext instanceof TracingContextImpl
                ? new Map(initialContext._contextMap)
                : new Map();
    }
    setValue(key, value) {
        const newContext = new TracingContextImpl(this);
        newContext._contextMap.set(key, value);
        return newContext;
    }
    getValue(key) {
        return this._contextMap.get(key);
    }
    deleteValue(key) {
        const newContext = new TracingContextImpl(this);
        newContext._contextMap.delete(key);
        return newContext;
    }
}
//# sourceMappingURL=tracingContext.js.map
// EXTERNAL MODULE: ./node_modules/@azure/core-tracing/dist/commonjs/state.js
var commonjs_state = __nccwpck_require__(8914);
;// CONCATENATED MODULE: ./node_modules/@azure/core-tracing/dist/esm/state.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
// @ts-expect-error The recommended approach to sharing module state between ESM and CJS.
// See https://github.com/isaacs/tshy/blob/main/README.md#module-local-state for additional information.

/**
 * Defines the shared state between CJS and ESM by re-exporting the CJS state.
 */
const state_state = commonjs_state/* state */.w;
//# sourceMappingURL=state.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-tracing/dist/esm/instrumenter.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


function createDefaultTracingSpan() {
    return {
        end: () => {
            // noop
        },
        isRecording: () => false,
        recordException: () => {
            // noop
        },
        setAttribute: () => {
            // noop
        },
        setStatus: () => {
            // noop
        },
        addEvent: () => {
            // noop
        },
    };
}
function createDefaultInstrumenter() {
    return {
        createRequestHeaders: () => {
            return {};
        },
        parseTraceparentHeader: () => {
            return undefined;
        },
        startSpan: (_name, spanOptions) => {
            return {
                span: createDefaultTracingSpan(),
                tracingContext: createTracingContext({ parentContext: spanOptions.tracingContext }),
            };
        },
        withContext(_context, callback, ...callbackArgs) {
            return callback(...callbackArgs);
        },
    };
}
/**
 * Extends the Azure SDK with support for a given instrumenter implementation.
 *
 * @param instrumenter - The instrumenter implementation to use.
 */
function useInstrumenter(instrumenter) {
    state.instrumenterImplementation = instrumenter;
}
/**
 * Gets the currently set instrumenter, a No-Op instrumenter by default.
 *
 * @returns The currently set instrumenter
 */
function getInstrumenter() {
    if (!state_state.instrumenterImplementation) {
        state_state.instrumenterImplementation = createDefaultInstrumenter();
    }
    return state_state.instrumenterImplementation;
}
//# sourceMappingURL=instrumenter.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-tracing/dist/esm/tracingClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * Creates a new tracing client.
 *
 * @param options - Options used to configure the tracing client.
 * @returns - An instance of {@link TracingClient}.
 */
function createTracingClient(options) {
    const { namespace, packageName, packageVersion } = options;
    function startSpan(name, operationOptions, spanOptions) {
        const startSpanResult = getInstrumenter().startSpan(name, {
            ...spanOptions,
            packageName: packageName,
            packageVersion: packageVersion,
            tracingContext: operationOptions?.tracingOptions?.tracingContext,
        });
        let tracingContext = startSpanResult.tracingContext;
        const span = startSpanResult.span;
        if (!tracingContext.getValue(knownContextKeys.namespace)) {
            tracingContext = tracingContext.setValue(knownContextKeys.namespace, namespace);
        }
        span.setAttribute("az.namespace", tracingContext.getValue(knownContextKeys.namespace));
        const updatedOptions = Object.assign({}, operationOptions, {
            tracingOptions: { ...operationOptions?.tracingOptions, tracingContext },
        });
        return {
            span,
            updatedOptions,
        };
    }
    async function withSpan(name, operationOptions, callback, spanOptions) {
        const { span, updatedOptions } = startSpan(name, operationOptions, spanOptions);
        try {
            const result = await withContext(updatedOptions.tracingOptions.tracingContext, () => Promise.resolve(callback(updatedOptions, span)));
            span.setStatus({ status: "success" });
            return result;
        }
        catch (err) {
            span.setStatus({ status: "error", error: err });
            throw err;
        }
        finally {
            span.end();
        }
    }
    function withContext(context, callback, ...callbackArgs) {
        return getInstrumenter().withContext(context, callback, ...callbackArgs);
    }
    /**
     * Parses a traceparent header value into a span identifier.
     *
     * @param traceparentHeader - The traceparent header to parse.
     * @returns An implementation-specific identifier for the span.
     */
    function parseTraceparentHeader(traceparentHeader) {
        return getInstrumenter().parseTraceparentHeader(traceparentHeader);
    }
    /**
     * Creates a set of request headers to propagate tracing information to a backend.
     *
     * @param tracingContext - The context containing the span to serialize.
     * @returns The set of headers to add to a request.
     */
    function createRequestHeaders(tracingContext) {
        return getInstrumenter().createRequestHeaders(tracingContext);
    }
    return {
        startSpan,
        withSpan,
        withContext,
        parseTraceparentHeader,
        createRequestHeaders,
    };
}
//# sourceMappingURL=tracingClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-tracing/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/restError.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * A custom error type for failed pipeline requests.
 */
// eslint-disable-next-line @typescript-eslint/no-redeclare
const esm_restError_RestError = restError_RestError;
/**
 * Typeguard for RestError
 * @param e - Something caught by a catch clause.
 */
function esm_restError_isRestError(e) {
    return restError_isRestError(e);
}
//# sourceMappingURL=restError.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/tracingPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.







/**
 * The programmatic identifier of the tracingPolicy.
 */
const tracingPolicyName = "tracingPolicy";
/**
 * A simple policy to create OpenTelemetry Spans for each request made by the pipeline
 * that has SpanOptions with a parent.
 * Requests made without a parent Span will not be recorded.
 * @param options - Options to configure the telemetry logged by the tracing policy.
 */
function tracingPolicy(options = {}) {
    const userAgentPromise = util_userAgent_getUserAgentValue(options.userAgentPrefix);
    const sanitizer = new Sanitizer({
        additionalAllowedQueryParameters: options.additionalAllowedQueryParameters,
    });
    const tracingClient = tryCreateTracingClient();
    return {
        name: tracingPolicyName,
        async sendRequest(request, next) {
            if (!tracingClient) {
                return next(request);
            }
            const userAgent = await userAgentPromise;
            const spanAttributes = {
                "http.url": sanitizer.sanitizeUrl(request.url),
                "http.method": request.method,
                "http.user_agent": userAgent,
                requestId: request.requestId,
            };
            if (userAgent) {
                spanAttributes["http.user_agent"] = userAgent;
            }
            const { span, tracingContext } = tryCreateSpan(tracingClient, request, spanAttributes) ?? {};
            if (!span || !tracingContext) {
                return next(request);
            }
            try {
                const response = await tracingClient.withContext(tracingContext, next, request);
                tryProcessResponse(span, response);
                return response;
            }
            catch (err) {
                tryProcessError(span, err);
                throw err;
            }
        },
    };
}
function tryCreateTracingClient() {
    try {
        return createTracingClient({
            namespace: "",
            packageName: "@azure/core-rest-pipeline",
            packageVersion: esm_constants_SDK_VERSION,
        });
    }
    catch (e) {
        esm_log_logger.warning(`Error when creating the TracingClient: ${getErrorMessage(e)}`);
        return undefined;
    }
}
function tryCreateSpan(tracingClient, request, spanAttributes) {
    try {
        // As per spec, we do not need to differentiate between HTTP and HTTPS in span name.
        const { span, updatedOptions } = tracingClient.startSpan(`HTTP ${request.method}`, { tracingOptions: request.tracingOptions }, {
            spanKind: "client",
            spanAttributes,
        });
        // If the span is not recording, don't do any more work.
        if (!span.isRecording()) {
            span.end();
            return undefined;
        }
        // set headers
        const headers = tracingClient.createRequestHeaders(updatedOptions.tracingOptions.tracingContext);
        for (const [key, value] of Object.entries(headers)) {
            request.headers.set(key, value);
        }
        return { span, tracingContext: updatedOptions.tracingOptions.tracingContext };
    }
    catch (e) {
        esm_log_logger.warning(`Skipping creating a tracing span due to an error: ${getErrorMessage(e)}`);
        return undefined;
    }
}
function tryProcessError(span, error) {
    try {
        span.setStatus({
            status: "error",
            error: esm_isError(error) ? error : undefined,
        });
        if (esm_restError_isRestError(error) && error.statusCode) {
            span.setAttribute("http.status_code", error.statusCode);
        }
        span.end();
    }
    catch (e) {
        esm_log_logger.warning(`Skipping tracing span processing due to an error: ${getErrorMessage(e)}`);
    }
}
function tryProcessResponse(span, response) {
    try {
        span.setAttribute("http.status_code", response.status);
        const serviceRequestId = response.headers.get("x-ms-request-id");
        if (serviceRequestId) {
            span.setAttribute("serviceRequestId", serviceRequestId);
        }
        // Per semantic conventions, only set the status to error if the status code is 4xx or 5xx.
        // Otherwise, the status MUST remain unset.
        // https://opentelemetry.io/docs/specs/semconv/http/http-spans/#status
        if (response.status >= 400) {
            span.setStatus({
                status: "error",
            });
        }
        span.end();
    }
    catch (e) {
        esm_log_logger.warning(`Skipping tracing span processing due to an error: ${getErrorMessage(e)}`);
    }
}
//# sourceMappingURL=tracingPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/util/wrapAbortSignal.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Creates a native AbortSignal which reflects the state of the provided AbortSignalLike.
 * If the AbortSignalLike is already a native AbortSignal, it is returned as is.
 * @param abortSignalLike - The AbortSignalLike to wrap.
 * @returns - An object containing the native AbortSignal and an optional cleanup function. The cleanup function should be called when the AbortSignal is no longer needed.
 */
function wrapAbortSignalLike(abortSignalLike) {
    if (abortSignalLike instanceof AbortSignal) {
        return { abortSignal: abortSignalLike };
    }
    if (abortSignalLike.aborted) {
        return { abortSignal: AbortSignal.abort(abortSignalLike.reason) };
    }
    const controller = new AbortController();
    let needsCleanup = true;
    function cleanup() {
        if (needsCleanup) {
            abortSignalLike.removeEventListener("abort", listener);
            needsCleanup = false;
        }
    }
    function listener() {
        controller.abort(abortSignalLike.reason);
        cleanup();
    }
    abortSignalLike.addEventListener("abort", listener);
    return { abortSignal: controller.signal, cleanup };
}
//# sourceMappingURL=wrapAbortSignal.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/wrapAbortSignalLikePolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const wrapAbortSignalLikePolicyName = "wrapAbortSignalLikePolicy";
/**
 * Policy that ensure that any AbortSignalLike is wrapped in a native AbortSignal for processing by the pipeline.
 * Since the ts-http-runtime expects a native AbortSignal, this policy is used to ensure that any AbortSignalLike is wrapped in a native AbortSignal.
 *
 * @returns - created policy
 */
function wrapAbortSignalLikePolicy() {
    return {
        name: wrapAbortSignalLikePolicyName,
        sendRequest: async (request, next) => {
            if (!request.abortSignal) {
                return next(request);
            }
            const { abortSignal, cleanup } = wrapAbortSignalLike(request.abortSignal);
            request.abortSignal = abortSignal;
            try {
                return await next(request);
            }
            finally {
                cleanup?.();
            }
        },
    };
}
//# sourceMappingURL=wrapAbortSignalLikePolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/createPipelineFromOptions.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.















/**
 * Create a new pipeline with a default set of customizable policies.
 * @param options - Options to configure a custom pipeline.
 */
function esm_createPipelineFromOptions_createPipelineFromOptions(options) {
    const pipeline = esm_pipeline_createEmptyPipeline();
    if (esm_isNodeLike) {
        if (options.agent) {
            pipeline.addPolicy(policies_agentPolicy_agentPolicy(options.agent));
        }
        if (options.tlsOptions) {
            pipeline.addPolicy(policies_tlsPolicy_tlsPolicy(options.tlsOptions));
        }
        pipeline.addPolicy(policies_proxyPolicy_proxyPolicy(options.proxyOptions));
        pipeline.addPolicy(policies_decompressResponsePolicy_decompressResponsePolicy());
    }
    pipeline.addPolicy(wrapAbortSignalLikePolicy());
    pipeline.addPolicy(policies_formDataPolicy_formDataPolicy(), { beforePolicies: [policies_multipartPolicy_multipartPolicyName] });
    pipeline.addPolicy(policies_userAgentPolicy_userAgentPolicy(options.userAgentOptions));
    pipeline.addPolicy(setClientRequestIdPolicy(options.telemetryOptions?.clientRequestIdHeaderName));
    // The multipart policy is added after policies with no phase, so that
    // policies can be added between it and formDataPolicy to modify
    // properties (e.g., making the boundary constant in recorded tests).
    pipeline.addPolicy(policies_multipartPolicy_multipartPolicy(), { afterPhase: "Deserialize" });
    pipeline.addPolicy(policies_defaultRetryPolicy_defaultRetryPolicy(options.retryOptions), { phase: "Retry" });
    pipeline.addPolicy(tracingPolicy({ ...options.userAgentOptions, ...options.loggingOptions }), {
        afterPhase: "Retry",
    });
    if (esm_isNodeLike) {
        // Both XHR and Fetch expect to handle redirects automatically,
        // so only include this policy when we're in Node.
        pipeline.addPolicy(policies_redirectPolicy_redirectPolicy(options.redirectOptions), { afterPhase: "Retry" });
    }
    pipeline.addPolicy(policies_logPolicy_logPolicy(options.loggingOptions), { afterPhase: "Sign" });
    return pipeline;
}
//# sourceMappingURL=createPipelineFromOptions.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/defaultHttpClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * Create the correct HttpClient for the current environment.
 */
function esm_defaultHttpClient_createDefaultHttpClient() {
    const client = defaultHttpClient_createDefaultHttpClient();
    return {
        async sendRequest(request) {
            // we wrap any AbortSignalLike here since the TypeSpec runtime expects a native AbortSignal.
            // 99% of the time, this should be a no-op since a native AbortSignal is passed in.
            const { abortSignal, cleanup } = request.abortSignal
                ? wrapAbortSignalLike(request.abortSignal)
                : {};
            try {
                request.abortSignal = abortSignal;
                return await client.sendRequest(request);
            }
            finally {
                cleanup?.();
            }
        },
    };
}
//# sourceMappingURL=defaultHttpClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/httpHeaders.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Creates an object that satisfies the `HttpHeaders` interface.
 * @param rawHeaders - A simple object representing initial headers
 */
function esm_httpHeaders_createHttpHeaders(rawHeaders) {
    return httpHeaders_createHttpHeaders(rawHeaders);
}
//# sourceMappingURL=httpHeaders.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/pipelineRequest.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Creates a new pipeline request with the given options.
 * This method is to allow for the easy setting of default values and not required.
 * @param options - The options to create the request with.
 */
function esm_pipelineRequest_createPipelineRequest(options) {
    // Cast required due to difference between ts-http-runtime requiring AbortSignal while core-rest-pipeline allows
    // the more generic AbortSignalLike. The wrapAbortSignalLike pipeline policy will take care of ensuring that any AbortSignalLike in the request
    // is converted into a true AbortSignal.
    return pipelineRequest_createPipelineRequest(options);
}
//# sourceMappingURL=pipelineRequest.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/exponentialRetryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * The programmatic identifier of the exponentialRetryPolicy.
 */
const exponentialRetryPolicy_exponentialRetryPolicyName = (/* unused pure expression or super */ null && (tspExponentialRetryPolicyName));
/**
 * A policy that attempts to retry requests while introducing an exponentially increasing delay.
 * @param options - Options that configure retry logic.
 */
function exponentialRetryPolicy_exponentialRetryPolicy(options = {}) {
    return tspExponentialRetryPolicy(options);
}
//# sourceMappingURL=exponentialRetryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/systemErrorRetryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Name of the {@link systemErrorRetryPolicy}
 */
const systemErrorRetryPolicy_systemErrorRetryPolicyName = (/* unused pure expression or super */ null && (tspSystemErrorRetryPolicyName));
/**
 * A retry policy that specifically seeks to handle errors in the
 * underlying transport layer (e.g. DNS lookup failures) rather than
 * retryable error codes from the server itself.
 * @param options - Options that customize the policy.
 */
function systemErrorRetryPolicy_systemErrorRetryPolicy(options = {}) {
    return tspSystemErrorRetryPolicy(options);
}
//# sourceMappingURL=systemErrorRetryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/throttlingRetryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Name of the {@link throttlingRetryPolicy}
 */
const throttlingRetryPolicy_throttlingRetryPolicyName = (/* unused pure expression or super */ null && (tspThrottlingRetryPolicyName));
/**
 * A policy that retries when the server sends a 429 response with a Retry-After header.
 *
 * To learn more, please refer to
 * https://learn.microsoft.com/azure/azure-resource-manager/resource-manager-request-limits,
 * https://learn.microsoft.com/azure/azure-subscription-service-limits and
 * https://learn.microsoft.com/azure/virtual-machines/troubleshooting/troubleshooting-throttling-errors
 *
 * @param options - Options that configure retry logic.
 */
function throttlingRetryPolicy_throttlingRetryPolicy(options = {}) {
    return tspThrottlingRetryPolicy(options);
}
//# sourceMappingURL=throttlingRetryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/retryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



const retryPolicy_retryPolicyLogger = esm_createClientLogger("core-rest-pipeline retryPolicy");
/**
 * retryPolicy is a generic policy to enable retrying requests when certain conditions are met
 */
function policies_retryPolicy_retryPolicy(strategies, options = { maxRetries: DEFAULT_RETRY_POLICY_COUNT }) {
    // Cast is required since the TSP runtime retry strategy type is slightly different
    // very deep down (using real AbortSignal vs. AbortSignalLike in RestError).
    // In practice the difference doesn't actually matter.
    return tspRetryPolicy(strategies, {
        logger: retryPolicy_retryPolicyLogger,
        ...options,
    });
}
//# sourceMappingURL=retryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/util/tokenCycler.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

// Default options for the cycler if none are provided
const DEFAULT_CYCLER_OPTIONS = {
    forcedRefreshWindowInMs: 1000, // Force waiting for a refresh 1s before the token expires
    retryIntervalInMs: 3000, // Allow refresh attempts every 3s
    refreshWindowInMs: 1000 * 60 * 2, // Start refreshing 2m before expiry
};
/**
 * Converts an an unreliable access token getter (which may resolve with null)
 * into an AccessTokenGetter by retrying the unreliable getter in a regular
 * interval.
 *
 * @param getAccessToken - A function that produces a promise of an access token that may fail by returning null.
 * @param retryIntervalInMs - The time (in milliseconds) to wait between retry attempts.
 * @param refreshTimeout - The timestamp after which the refresh attempt will fail, throwing an exception.
 * @returns - A promise that, if it resolves, will resolve with an access token.
 */
async function beginRefresh(getAccessToken, retryIntervalInMs, refreshTimeout) {
    // This wrapper handles exceptions gracefully as long as we haven't exceeded
    // the timeout.
    async function tryGetAccessToken() {
        if (Date.now() < refreshTimeout) {
            try {
                return await getAccessToken();
            }
            catch {
                return null;
            }
        }
        else {
            const finalToken = await getAccessToken();
            // Timeout is up, so throw if it's still null
            if (finalToken === null) {
                throw new Error("Failed to refresh access token.");
            }
            return finalToken;
        }
    }
    let token = await tryGetAccessToken();
    while (token === null) {
        await delay_delay(retryIntervalInMs);
        token = await tryGetAccessToken();
    }
    return token;
}
/**
 * Creates a token cycler from a credential, scopes, and optional settings.
 *
 * A token cycler represents a way to reliably retrieve a valid access token
 * from a TokenCredential. It will handle initializing the token, refreshing it
 * when it nears expiration, and synchronizes refresh attempts to avoid
 * concurrency hazards.
 *
 * @param credential - the underlying TokenCredential that provides the access
 * token
 * @param tokenCyclerOptions - optionally override default settings for the cycler
 *
 * @returns - a function that reliably produces a valid access token
 */
function tokenCycler_createTokenCycler(credential, tokenCyclerOptions) {
    let refreshWorker = null;
    let token = null;
    let tenantId;
    const options = {
        ...DEFAULT_CYCLER_OPTIONS,
        ...tokenCyclerOptions,
    };
    /**
     * This little holder defines several predicates that we use to construct
     * the rules of refreshing the token.
     */
    const cycler = {
        /**
         * Produces true if a refresh job is currently in progress.
         */
        get isRefreshing() {
            return refreshWorker !== null;
        },
        /**
         * Produces true if the cycler SHOULD refresh (we are within the refresh
         * window and not already refreshing)
         */
        get shouldRefresh() {
            if (cycler.isRefreshing) {
                return false;
            }
            if (token?.refreshAfterTimestamp && token.refreshAfterTimestamp < Date.now()) {
                return true;
            }
            return (token?.expiresOnTimestamp ?? 0) - options.refreshWindowInMs < Date.now();
        },
        /**
         * Produces true if the cycler MUST refresh (null or nearly-expired
         * token).
         */
        get mustRefresh() {
            return (token === null || token.expiresOnTimestamp - options.forcedRefreshWindowInMs < Date.now());
        },
    };
    /**
     * Starts a refresh job or returns the existing job if one is already
     * running.
     */
    function refresh(scopes, getTokenOptions) {
        if (!cycler.isRefreshing) {
            // We bind `scopes` here to avoid passing it around a lot
            const tryGetAccessToken = () => credential.getToken(scopes, getTokenOptions);
            // Take advantage of promise chaining to insert an assignment to `token`
            // before the refresh can be considered done.
            refreshWorker = beginRefresh(tryGetAccessToken, options.retryIntervalInMs, 
            // If we don't have a token, then we should timeout immediately
            token?.expiresOnTimestamp ?? Date.now())
                .then((_token) => {
                refreshWorker = null;
                token = _token;
                tenantId = getTokenOptions.tenantId;
                return token;
            })
                .catch((reason) => {
                // We also should reset the refresher if we enter a failed state.  All
                // existing awaiters will throw, but subsequent requests will start a
                // new retry chain.
                refreshWorker = null;
                token = null;
                tenantId = undefined;
                throw reason;
            });
        }
        return refreshWorker;
    }
    return async (scopes, tokenOptions) => {
        //
        // Simple rules:
        // - If we MUST refresh, then return the refresh task, blocking
        //   the pipeline until a token is available.
        // - If we SHOULD refresh, then run refresh but don't return it
        //   (we can still use the cached token).
        // - Return the token, since it's fine if we didn't return in
        //   step 1.
        //
        const hasClaimChallenge = Boolean(tokenOptions.claims);
        const tenantIdChanged = tenantId !== tokenOptions.tenantId;
        if (hasClaimChallenge) {
            // If we've received a claim, we know the existing token isn't valid
            // We want to clear it so that that refresh worker won't use the old expiration time as a timeout
            token = null;
        }
        // If the tenantId passed in token options is different to the one we have
        // Or if we are in claim challenge and the token was rejected and a new access token need to be issued, we need to
        // refresh the token with the new tenantId or token.
        const mustRefresh = tenantIdChanged || hasClaimChallenge || cycler.mustRefresh;
        if (mustRefresh) {
            return refresh(scopes, tokenOptions);
        }
        if (cycler.shouldRefresh) {
            refresh(scopes, tokenOptions);
        }
        return token;
    };
}
//# sourceMappingURL=tokenCycler.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/bearerTokenAuthenticationPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * The programmatic identifier of the bearerTokenAuthenticationPolicy.
 */
const bearerTokenAuthenticationPolicyName = "bearerTokenAuthenticationPolicy";
/**
 * Try to send the given request.
 *
 * When a response is received, returns a tuple of the response received and, if the response was received
 * inside a thrown RestError, the RestError that was thrown.
 *
 * Otherwise, if an error was thrown while sending the request that did not provide an underlying response, it
 * will be rethrown.
 */
async function trySendRequest(request, next) {
    try {
        return [await next(request), undefined];
    }
    catch (e) {
        if (esm_restError_isRestError(e) && e.response) {
            return [e.response, e];
        }
        else {
            throw e;
        }
    }
}
/**
 * Default authorize request handler
 */
async function defaultAuthorizeRequest(options) {
    const { scopes, getAccessToken, request } = options;
    // Enable CAE true by default
    const getTokenOptions = {
        abortSignal: request.abortSignal,
        tracingOptions: request.tracingOptions,
        enableCae: true,
    };
    const accessToken = await getAccessToken(scopes, getTokenOptions);
    if (accessToken) {
        options.request.headers.set("Authorization", `Bearer ${accessToken.token}`);
    }
}
/**
 * We will retrieve the challenge only if the response status code was 401,
 * and if the response contained the header "WWW-Authenticate" with a non-empty value.
 */
function isChallengeResponse(response) {
    return response.status === 401 && response.headers.has("WWW-Authenticate");
}
/**
 * Re-authorize the request for CAE challenge.
 * The response containing the challenge is `options.response`.
 * If this method returns true, the underlying request will be sent once again.
 */
async function authorizeRequestOnCaeChallenge(onChallengeOptions, caeClaims) {
    const { scopes } = onChallengeOptions;
    const accessToken = await onChallengeOptions.getAccessToken(scopes, {
        enableCae: true,
        claims: caeClaims,
    });
    if (!accessToken) {
        return false;
    }
    onChallengeOptions.request.headers.set("Authorization", `${accessToken.tokenType ?? "Bearer"} ${accessToken.token}`);
    return true;
}
/**
 * A policy that can request a token from a TokenCredential implementation and
 * then apply it to the Authorization header of a request as a Bearer token.
 */
function bearerTokenAuthenticationPolicy(options) {
    const { credential, scopes, challengeCallbacks } = options;
    const logger = options.logger || esm_log_logger;
    const callbacks = {
        authorizeRequest: challengeCallbacks?.authorizeRequest?.bind(challengeCallbacks) ?? defaultAuthorizeRequest,
        authorizeRequestOnChallenge: challengeCallbacks?.authorizeRequestOnChallenge?.bind(challengeCallbacks),
    };
    // This function encapsulates the entire process of reliably retrieving the token
    // The options are left out of the public API until there's demand to configure this.
    // Remember to extend `BearerTokenAuthenticationPolicyOptions` with `TokenCyclerOptions`
    // in order to pass through the `options` object.
    const getAccessToken = credential
        ? tokenCycler_createTokenCycler(credential /* , options */)
        : () => Promise.resolve(null);
    return {
        name: bearerTokenAuthenticationPolicyName,
        /**
         * If there's no challenge parameter:
         * - It will try to retrieve the token using the cache, or the credential's getToken.
         * - Then it will try the next policy with or without the retrieved token.
         *
         * It uses the challenge parameters to:
         * - Skip a first attempt to get the token from the credential if there's no cached token,
         *   since it expects the token to be retrievable only after the challenge.
         * - Prepare the outgoing request if the `prepareRequest` method has been provided.
         * - Send an initial request to receive the challenge if it fails.
         * - Process a challenge if the response contains it.
         * - Retrieve a token with the challenge information, then re-send the request.
         */
        async sendRequest(request, next) {
            if (!request.url.toLowerCase().startsWith("https://")) {
                throw new Error("Bearer token authentication is not permitted for non-TLS protected (non-https) URLs.");
            }
            await callbacks.authorizeRequest({
                scopes: Array.isArray(scopes) ? scopes : [scopes],
                request,
                getAccessToken,
                logger,
            });
            let response;
            let error;
            let shouldSendRequest;
            [response, error] = await trySendRequest(request, next);
            if (isChallengeResponse(response)) {
                let claims = getCaeChallengeClaims(response.headers.get("WWW-Authenticate"));
                // Handle CAE by default when receive CAE claim
                if (claims) {
                    let parsedClaim;
                    // Return the response immediately if claims is not a valid base64 encoded string
                    try {
                        parsedClaim = atob(claims);
                    }
                    catch (e) {
                        logger.warning(`The WWW-Authenticate header contains "claims" that cannot be parsed. Unable to perform the Continuous Access Evaluation authentication flow. Unparsable claims: ${claims}`);
                        return response;
                    }
                    shouldSendRequest = await authorizeRequestOnCaeChallenge({
                        scopes: Array.isArray(scopes) ? scopes : [scopes],
                        response,
                        request,
                        getAccessToken,
                        logger,
                    }, parsedClaim);
                    // Send updated request and handle response for RestError
                    if (shouldSendRequest) {
                        [response, error] = await trySendRequest(request, next);
                    }
                }
                else if (callbacks.authorizeRequestOnChallenge) {
                    // Handle custom challenges when client provides custom callback
                    shouldSendRequest = await callbacks.authorizeRequestOnChallenge({
                        scopes: Array.isArray(scopes) ? scopes : [scopes],
                        request,
                        response,
                        getAccessToken,
                        logger,
                    });
                    // Send updated request and handle response for RestError
                    if (shouldSendRequest) {
                        [response, error] = await trySendRequest(request, next);
                    }
                    // If we get another CAE Claim, we will handle it by default and return whatever value we receive for this
                    if (isChallengeResponse(response)) {
                        claims = getCaeChallengeClaims(response.headers.get("WWW-Authenticate"));
                        if (claims) {
                            let parsedClaim;
                            try {
                                parsedClaim = atob(claims);
                            }
                            catch (e) {
                                logger.warning(`The WWW-Authenticate header contains "claims" that cannot be parsed. Unable to perform the Continuous Access Evaluation authentication flow. Unparsable claims: ${claims}`);
                                return response;
                            }
                            shouldSendRequest = await authorizeRequestOnCaeChallenge({
                                scopes: Array.isArray(scopes) ? scopes : [scopes],
                                response,
                                request,
                                getAccessToken,
                                logger,
                            }, parsedClaim);
                            // Send updated request and handle response for RestError
                            if (shouldSendRequest) {
                                [response, error] = await trySendRequest(request, next);
                            }
                        }
                    }
                }
            }
            if (error) {
                throw error;
            }
            else {
                return response;
            }
        },
    };
}
/**
 * Converts: `Bearer a="b", c="d", Pop e="f", g="h"`.
 * Into: `[ { scheme: 'Bearer', params: { a: 'b', c: 'd' } }, { scheme: 'Pop', params: { e: 'f', g: 'h' } } ]`.
 *
 * @internal
 */
function parseChallenges(challenges) {
    // Challenge regex seperates the string to individual challenges with different schemes in the format `Scheme a="b", c=d`
    // The challenge regex captures parameteres with either quotes values or unquoted values
    const challengeRegex = /(\w+)\s+((?:\w+=(?:"[^"]*"|[^,]*),?\s*)+)/g;
    // Parameter regex captures the claims group removed from the scheme in the format `a="b"` and `c="d"`
    // CAE challenge always have quoted parameters. For more reference, https://learn.microsoft.com/entra/identity-platform/claims-challenge
    const paramRegex = /(\w+)="([^"]*)"/g;
    const parsedChallenges = [];
    let match;
    // Iterate over each challenge match
    while ((match = challengeRegex.exec(challenges)) !== null) {
        const scheme = match[1];
        const paramsString = match[2];
        const params = {};
        let paramMatch;
        // Iterate over each parameter match
        while ((paramMatch = paramRegex.exec(paramsString)) !== null) {
            params[paramMatch[1]] = paramMatch[2];
        }
        parsedChallenges.push({ scheme, params });
    }
    return parsedChallenges;
}
/**
 * Parse a pipeline response and look for a CAE challenge with "Bearer" scheme
 * Return the value in the header without parsing the challenge
 * @internal
 */
function getCaeChallengeClaims(challenges) {
    if (!challenges) {
        return;
    }
    // Find all challenges present in the header
    const parsedChallenges = parseChallenges(challenges);
    return parsedChallenges.find((x) => x.scheme === "Bearer" && x.params.claims && x.params.error === "insufficient_claims")?.params.claims;
}
//# sourceMappingURL=bearerTokenAuthenticationPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/policies/auxiliaryAuthenticationHeaderPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * The programmatic identifier of the auxiliaryAuthenticationHeaderPolicy.
 */
const auxiliaryAuthenticationHeaderPolicyName = "auxiliaryAuthenticationHeaderPolicy";
const AUTHORIZATION_AUXILIARY_HEADER = "x-ms-authorization-auxiliary";
async function sendAuthorizeRequest(options) {
    const { scopes, getAccessToken, request } = options;
    const getTokenOptions = {
        abortSignal: request.abortSignal,
        tracingOptions: request.tracingOptions,
    };
    return (await getAccessToken(scopes, getTokenOptions))?.token ?? "";
}
/**
 * A policy for external tokens to `x-ms-authorization-auxiliary` header.
 * This header will be used when creating a cross-tenant application we may need to handle authentication requests
 * for resources that are in different tenants.
 * You could see [ARM docs](https://learn.microsoft.com/azure/azure-resource-manager/management/authenticate-multi-tenant) for a rundown of how this feature works
 */
function auxiliaryAuthenticationHeaderPolicy(options) {
    const { credentials, scopes } = options;
    const logger = options.logger || coreLogger;
    const tokenCyclerMap = new WeakMap();
    return {
        name: auxiliaryAuthenticationHeaderPolicyName,
        async sendRequest(request, next) {
            if (!request.url.toLowerCase().startsWith("https://")) {
                throw new Error("Bearer token authentication for auxiliary header is not permitted for non-TLS protected (non-https) URLs.");
            }
            if (!credentials || credentials.length === 0) {
                logger.info(`${auxiliaryAuthenticationHeaderPolicyName} header will not be set due to empty credentials.`);
                return next(request);
            }
            const tokenPromises = [];
            for (const credential of credentials) {
                let getAccessToken = tokenCyclerMap.get(credential);
                if (!getAccessToken) {
                    getAccessToken = createTokenCycler(credential);
                    tokenCyclerMap.set(credential, getAccessToken);
                }
                tokenPromises.push(sendAuthorizeRequest({
                    scopes: Array.isArray(scopes) ? scopes : [scopes],
                    request,
                    getAccessToken,
                    logger,
                }));
            }
            const auxiliaryTokens = (await Promise.all(tokenPromises)).filter((token) => Boolean(token));
            if (auxiliaryTokens.length === 0) {
                logger.warning(`None of the auxiliary tokens are valid. ${AUTHORIZATION_AUXILIARY_HEADER} header will not be set.`);
                return next(request);
            }
            request.headers.set(AUTHORIZATION_AUXILIARY_HEADER, auxiliaryTokens.map((token) => `Bearer ${token}`).join(", "));
            return next(request);
        },
    };
}
//# sourceMappingURL=auxiliaryAuthenticationHeaderPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-rest-pipeline/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


























//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-auth/dist/esm/keyCredential.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Tests an object to determine whether it implements KeyCredential.
 *
 * @param credential - The assumed KeyCredential to be tested.
 */
function isKeyCredential(credential) {
    return isObjectWithProperties(credential, ["key"]) && typeof credential.key === "string";
}
//# sourceMappingURL=keyCredential.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-auth/dist/esm/azureNamedKeyCredential.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * A static name/key-based credential that supports updating
 * the underlying name and key values.
 */
class AzureNamedKeyCredential {
    _key;
    _name;
    /**
     * The value of the key to be used in authentication.
     */
    get key() {
        return this._key;
    }
    /**
     * The value of the name to be used in authentication.
     */
    get name() {
        return this._name;
    }
    /**
     * Create an instance of an AzureNamedKeyCredential for use
     * with a service client.
     *
     * @param name - The initial value of the name to use in authentication.
     * @param key - The initial value of the key to use in authentication.
     */
    constructor(name, key) {
        if (!name || !key) {
            throw new TypeError("name and key must be non-empty strings");
        }
        this._name = name;
        this._key = key;
    }
    /**
     * Change the value of the key.
     *
     * Updates will take effect upon the next request after
     * updating the key value.
     *
     * @param newName - The new name value to be used.
     * @param newKey - The new key value to be used.
     */
    update(newName, newKey) {
        if (!newName || !newKey) {
            throw new TypeError("newName and newKey must be non-empty strings");
        }
        this._name = newName;
        this._key = newKey;
    }
}
/**
 * Tests an object to determine whether it implements NamedKeyCredential.
 *
 * @param credential - The assumed NamedKeyCredential to be tested.
 */
function isNamedKeyCredential(credential) {
    return (isObjectWithProperties(credential, ["name", "key"]) &&
        typeof credential.key === "string" &&
        typeof credential.name === "string");
}
//# sourceMappingURL=azureNamedKeyCredential.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-auth/dist/esm/azureSASCredential.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * A static-signature-based credential that supports updating
 * the underlying signature value.
 */
class AzureSASCredential {
    _signature;
    /**
     * The value of the shared access signature to be used in authentication
     */
    get signature() {
        return this._signature;
    }
    /**
     * Create an instance of an AzureSASCredential for use
     * with a service client.
     *
     * @param signature - The initial value of the shared access signature to use in authentication
     */
    constructor(signature) {
        if (!signature) {
            throw new Error("shared access signature must be a non-empty string");
        }
        this._signature = signature;
    }
    /**
     * Change the value of the signature.
     *
     * Updates will take effect upon the next request after
     * updating the signature value.
     *
     * @param newSignature - The new shared access signature value to be used
     */
    update(newSignature) {
        if (!newSignature) {
            throw new Error("shared access signature must be a non-empty string");
        }
        this._signature = newSignature;
    }
}
/**
 * Tests an object to determine whether it implements SASCredential.
 *
 * @param credential - The assumed SASCredential to be tested.
 */
function isSASCredential(credential) {
    return (isObjectWithProperties(credential, ["signature"]) && typeof credential.signature === "string");
}
//# sourceMappingURL=azureSASCredential.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-auth/dist/esm/tokenCredential.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * @internal
 * @param accessToken - Access token
 * @returns Whether a token is bearer type or not
 */
function isBearerToken(accessToken) {
    return !accessToken.tokenType || accessToken.tokenType === "Bearer";
}
/**
 * @internal
 * @param accessToken - Access token
 * @returns Whether a token is Pop token or not
 */
function isPopToken(accessToken) {
    return accessToken.tokenType === "pop";
}
/**
 * Tests an object to determine whether it implements TokenCredential.
 *
 * @param credential - The assumed TokenCredential to be tested.
 */
function isTokenCredential(credential) {
    // Check for an object with a 'getToken' function and possibly with
    // a 'signRequest' function.  We do this check to make sure that
    // a ServiceClientCredentials implementor (like TokenClientCredentials
    // in ms-rest-nodeauth) doesn't get mistaken for a TokenCredential if
    // it doesn't actually implement TokenCredential also.
    const castCredential = credential;
    return (castCredential &&
        typeof castCredential.getToken === "function" &&
        (castCredential.signRequest === undefined || castCredential.getToken.length > 0));
}
//# sourceMappingURL=tokenCredential.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-auth/dist/esm/index.js





//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-http-compat/dist/esm/policies/disableKeepAlivePolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
const disableKeepAlivePolicyName = "DisableKeepAlivePolicy";
function createDisableKeepAlivePolicy() {
    return {
        name: disableKeepAlivePolicyName,
        async sendRequest(request, next) {
            request.disableKeepAlive = true;
            return next(request);
        },
    };
}
/**
 * @internal
 */
function pipelineContainsDisableKeepAlivePolicy(pipeline) {
    return pipeline.getOrderedPolicies().some((policy) => policy.name === disableKeepAlivePolicyName);
}
//# sourceMappingURL=disableKeepAlivePolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/base64.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Encodes a string in base64 format.
 * @param value - the string to encode
 * @internal
 */
function encodeString(value) {
    return Buffer.from(value).toString("base64");
}
/**
 * Encodes a byte array in base64 format.
 * @param value - the Uint8Aray to encode
 * @internal
 */
function encodeByteArray(value) {
    const bufferValue = value instanceof Buffer ? value : Buffer.from(value.buffer);
    return bufferValue.toString("base64");
}
/**
 * Decodes a base64 string into a byte array.
 * @param value - the base64 string to decode
 * @internal
 */
function decodeString(value) {
    return Buffer.from(value, "base64");
}
/**
 * Decodes a base64 string into a string.
 * @param value - the base64 string to decode
 * @internal
 */
function base64_decodeStringToString(value) {
    return Buffer.from(value, "base64").toString();
}
//# sourceMappingURL=base64.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/interfaces.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * Default key used to access the XML attributes.
 */
const XML_ATTRKEY = "$";
/**
 * Default key used to access the XML value content.
 */
const XML_CHARKEY = "_";
//# sourceMappingURL=interfaces.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/utils.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * A type guard for a primitive response body.
 * @param value - Value to test
 *
 * @internal
 */
function isPrimitiveBody(value, mapperTypeName) {
    return (mapperTypeName !== "Composite" &&
        mapperTypeName !== "Dictionary" &&
        (typeof value === "string" ||
            typeof value === "number" ||
            typeof value === "boolean" ||
            mapperTypeName?.match(/^(Date|DateTime|DateTimeRfc1123|UnixTime|ByteArray|Base64Url)$/i) !==
                null ||
            value === undefined ||
            value === null));
}
const validateISODuration = /^(-|\+)?P(?:([-+]?[0-9,.]*)Y)?(?:([-+]?[0-9,.]*)M)?(?:([-+]?[0-9,.]*)W)?(?:([-+]?[0-9,.]*)D)?(?:T(?:([-+]?[0-9,.]*)H)?(?:([-+]?[0-9,.]*)M)?(?:([-+]?[0-9,.]*)S)?)?$/;
/**
 * Returns true if the given string is in ISO 8601 format.
 * @param value - The value to be validated for ISO 8601 duration format.
 * @internal
 */
function isDuration(value) {
    return validateISODuration.test(value);
}
const validUuidRegex = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/i;
/**
 * Returns true if the provided uuid is valid.
 *
 * @param uuid - The uuid that needs to be validated.
 *
 * @internal
 */
function isValidUuid(uuid) {
    return validUuidRegex.test(uuid);
}
/**
 * Maps the response as follows:
 * - wraps the response body if needed (typically if its type is primitive).
 * - returns null if the combination of the headers and the body is empty.
 * - otherwise, returns the combination of the headers and the body.
 *
 * @param responseObject - a representation of the parsed response
 * @returns the response that will be returned to the user which can be null and/or wrapped
 *
 * @internal
 */
function handleNullableResponseAndWrappableBody(responseObject) {
    const combinedHeadersAndBody = {
        ...responseObject.headers,
        ...responseObject.body,
    };
    if (responseObject.hasNullableType &&
        Object.getOwnPropertyNames(combinedHeadersAndBody).length === 0) {
        return responseObject.shouldWrapBody ? { body: null } : null;
    }
    else {
        return responseObject.shouldWrapBody
            ? {
                ...responseObject.headers,
                body: responseObject.body,
            }
            : combinedHeadersAndBody;
    }
}
/**
 * Take a `FullOperationResponse` and turn it into a flat
 * response object to hand back to the consumer.
 * @param fullResponse - The processed response from the operation request
 * @param responseSpec - The response map from the OperationSpec
 *
 * @internal
 */
function flattenResponse(fullResponse, responseSpec) {
    const parsedHeaders = fullResponse.parsedHeaders;
    // head methods never have a body, but we return a boolean set to body property
    // to indicate presence/absence of the resource
    if (fullResponse.request.method === "HEAD") {
        return {
            ...parsedHeaders,
            body: fullResponse.parsedBody,
        };
    }
    const bodyMapper = responseSpec && responseSpec.bodyMapper;
    const isNullable = Boolean(bodyMapper?.nullable);
    const expectedBodyTypeName = bodyMapper?.type.name;
    /** If the body is asked for, we look at the expected body type to handle it */
    if (expectedBodyTypeName === "Stream") {
        return {
            ...parsedHeaders,
            blobBody: fullResponse.blobBody,
            readableStreamBody: fullResponse.readableStreamBody,
        };
    }
    const modelProperties = (expectedBodyTypeName === "Composite" &&
        bodyMapper.type.modelProperties) ||
        {};
    const isPageableResponse = Object.keys(modelProperties).some((k) => modelProperties[k].serializedName === "");
    if (expectedBodyTypeName === "Sequence" || isPageableResponse) {
        const arrayResponse = fullResponse.parsedBody ?? [];
        for (const key of Object.keys(modelProperties)) {
            if (modelProperties[key].serializedName) {
                arrayResponse[key] = fullResponse.parsedBody?.[key];
            }
        }
        if (parsedHeaders) {
            for (const key of Object.keys(parsedHeaders)) {
                arrayResponse[key] = parsedHeaders[key];
            }
        }
        return isNullable &&
            !fullResponse.parsedBody &&
            !parsedHeaders &&
            Object.getOwnPropertyNames(modelProperties).length === 0
            ? null
            : arrayResponse;
    }
    return handleNullableResponseAndWrappableBody({
        body: fullResponse.parsedBody,
        headers: parsedHeaders,
        hasNullableType: isNullable,
        shouldWrapBody: isPrimitiveBody(fullResponse.parsedBody, expectedBodyTypeName),
    });
}
//# sourceMappingURL=utils.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/serializer.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



class SerializerImpl {
    modelMappers;
    isXML;
    constructor(modelMappers = {}, isXML = false) {
        this.modelMappers = modelMappers;
        this.isXML = isXML;
    }
    /**
     * @deprecated Removing the constraints validation on client side.
     */
    validateConstraints(mapper, value, objectName) {
        const failValidation = (constraintName, constraintValue) => {
            throw new Error(`"${objectName}" with value "${value}" should satisfy the constraint "${constraintName}": ${constraintValue}.`);
        };
        if (mapper.constraints && value !== undefined && value !== null) {
            const { ExclusiveMaximum, ExclusiveMinimum, InclusiveMaximum, InclusiveMinimum, MaxItems, MaxLength, MinItems, MinLength, MultipleOf, Pattern, UniqueItems, } = mapper.constraints;
            if (ExclusiveMaximum !== undefined && value >= ExclusiveMaximum) {
                failValidation("ExclusiveMaximum", ExclusiveMaximum);
            }
            if (ExclusiveMinimum !== undefined && value <= ExclusiveMinimum) {
                failValidation("ExclusiveMinimum", ExclusiveMinimum);
            }
            if (InclusiveMaximum !== undefined && value > InclusiveMaximum) {
                failValidation("InclusiveMaximum", InclusiveMaximum);
            }
            if (InclusiveMinimum !== undefined && value < InclusiveMinimum) {
                failValidation("InclusiveMinimum", InclusiveMinimum);
            }
            if (MaxItems !== undefined && value.length > MaxItems) {
                failValidation("MaxItems", MaxItems);
            }
            if (MaxLength !== undefined && value.length > MaxLength) {
                failValidation("MaxLength", MaxLength);
            }
            if (MinItems !== undefined && value.length < MinItems) {
                failValidation("MinItems", MinItems);
            }
            if (MinLength !== undefined && value.length < MinLength) {
                failValidation("MinLength", MinLength);
            }
            if (MultipleOf !== undefined && value % MultipleOf !== 0) {
                failValidation("MultipleOf", MultipleOf);
            }
            if (Pattern) {
                const pattern = typeof Pattern === "string" ? new RegExp(Pattern) : Pattern;
                if (typeof value !== "string" || value.match(pattern) === null) {
                    failValidation("Pattern", Pattern);
                }
            }
            if (UniqueItems &&
                value.some((item, i, ar) => ar.indexOf(item) !== i)) {
                failValidation("UniqueItems", UniqueItems);
            }
        }
    }
    /**
     * Serialize the given object based on its metadata defined in the mapper
     *
     * @param mapper - The mapper which defines the metadata of the serializable object
     *
     * @param object - A valid Javascript object to be serialized
     *
     * @param objectName - Name of the serialized object
     *
     * @param options - additional options to serialization
     *
     * @returns A valid serialized Javascript object
     */
    serialize(mapper, object, objectName, options = { xml: {} }) {
        const updatedOptions = {
            xml: {
                rootName: options.xml.rootName ?? "",
                includeRoot: options.xml.includeRoot ?? false,
                xmlCharKey: options.xml.xmlCharKey ?? XML_CHARKEY,
            },
        };
        let payload = {};
        const mapperType = mapper.type.name;
        if (!objectName) {
            objectName = mapper.serializedName;
        }
        if (mapperType.match(/^Sequence$/i) !== null) {
            payload = [];
        }
        if (mapper.isConstant) {
            object = mapper.defaultValue;
        }
        // This table of allowed values should help explain
        // the mapper.required and mapper.nullable properties.
        // X means "neither undefined or null are allowed".
        //           || required
        //           || true      | false
        //  nullable || ==========================
        //      true || null      | undefined/null
        //     false || X         | undefined
        // undefined || X         | undefined/null
        const { required, nullable } = mapper;
        if (required && nullable && object === undefined) {
            throw new Error(`${objectName} cannot be undefined.`);
        }
        if (required && !nullable && (object === undefined || object === null)) {
            throw new Error(`${objectName} cannot be null or undefined.`);
        }
        if (!required && nullable === false && object === null) {
            throw new Error(`${objectName} cannot be null.`);
        }
        if (object === undefined || object === null) {
            payload = object;
        }
        else {
            if (mapperType.match(/^any$/i) !== null) {
                payload = object;
            }
            else if (mapperType.match(/^(Number|String|Boolean|Object|Stream|Uuid)$/i) !== null) {
                payload = serializeBasicTypes(mapperType, objectName, object);
            }
            else if (mapperType.match(/^Enum$/i) !== null) {
                const enumMapper = mapper;
                payload = serializeEnumType(objectName, enumMapper.type.allowedValues, object);
            }
            else if (mapperType.match(/^(Date|DateTime|TimeSpan|DateTimeRfc1123|UnixTime)$/i) !== null) {
                payload = serializeDateTypes(mapperType, object, objectName);
            }
            else if (mapperType.match(/^ByteArray$/i) !== null) {
                payload = serializeByteArrayType(objectName, object);
            }
            else if (mapperType.match(/^Base64Url$/i) !== null) {
                payload = serializeBase64UrlType(objectName, object);
            }
            else if (mapperType.match(/^Sequence$/i) !== null) {
                payload = serializeSequenceType(this, mapper, object, objectName, Boolean(this.isXML), updatedOptions);
            }
            else if (mapperType.match(/^Dictionary$/i) !== null) {
                payload = serializeDictionaryType(this, mapper, object, objectName, Boolean(this.isXML), updatedOptions);
            }
            else if (mapperType.match(/^Composite$/i) !== null) {
                payload = serializeCompositeType(this, mapper, object, objectName, Boolean(this.isXML), updatedOptions);
            }
        }
        return payload;
    }
    /**
     * Deserialize the given object based on its metadata defined in the mapper
     *
     * @param mapper - The mapper which defines the metadata of the serializable object
     *
     * @param responseBody - A valid Javascript entity to be deserialized
     *
     * @param objectName - Name of the deserialized object
     *
     * @param options - Controls behavior of XML parser and builder.
     *
     * @returns A valid deserialized Javascript object
     */
    deserialize(mapper, responseBody, objectName, options = { xml: {} }) {
        const updatedOptions = {
            xml: {
                rootName: options.xml.rootName ?? "",
                includeRoot: options.xml.includeRoot ?? false,
                xmlCharKey: options.xml.xmlCharKey ?? XML_CHARKEY,
            },
            ignoreUnknownProperties: options.ignoreUnknownProperties ?? false,
        };
        if (responseBody === undefined || responseBody === null) {
            if (this.isXML && mapper.type.name === "Sequence" && !mapper.xmlIsWrapped) {
                // Edge case for empty XML non-wrapped lists. xml2js can't distinguish
                // between the list being empty versus being missing,
                // so let's do the more user-friendly thing and return an empty list.
                responseBody = [];
            }
            // specifically check for undefined as default value can be a falsey value `0, "", false, null`
            if (mapper.defaultValue !== undefined) {
                responseBody = mapper.defaultValue;
            }
            return responseBody;
        }
        let payload;
        const mapperType = mapper.type.name;
        if (!objectName) {
            objectName = mapper.serializedName;
        }
        if (mapperType.match(/^Composite$/i) !== null) {
            payload = deserializeCompositeType(this, mapper, responseBody, objectName, updatedOptions);
        }
        else {
            if (this.isXML) {
                const xmlCharKey = updatedOptions.xml.xmlCharKey;
                /**
                 * If the mapper specifies this as a non-composite type value but the responseBody contains
                 * both header ("$" i.e., XML_ATTRKEY) and body ("#" i.e., XML_CHARKEY) properties,
                 * then just reduce the responseBody value to the body ("#" i.e., XML_CHARKEY) property.
                 */
                if (responseBody[XML_ATTRKEY] !== undefined && responseBody[xmlCharKey] !== undefined) {
                    responseBody = responseBody[xmlCharKey];
                }
            }
            if (mapperType.match(/^Number$/i) !== null) {
                payload = parseFloat(responseBody);
                if (isNaN(payload)) {
                    payload = responseBody;
                }
            }
            else if (mapperType.match(/^Boolean$/i) !== null) {
                if (responseBody === "true") {
                    payload = true;
                }
                else if (responseBody === "false") {
                    payload = false;
                }
                else {
                    payload = responseBody;
                }
            }
            else if (mapperType.match(/^(String|Enum|Object|Stream|Uuid|TimeSpan|any)$/i) !== null) {
                payload = responseBody;
            }
            else if (mapperType.match(/^(Date|DateTime|DateTimeRfc1123)$/i) !== null) {
                payload = new Date(responseBody);
            }
            else if (mapperType.match(/^UnixTime$/i) !== null) {
                payload = unixTimeToDate(responseBody);
            }
            else if (mapperType.match(/^ByteArray$/i) !== null) {
                payload = decodeString(responseBody);
            }
            else if (mapperType.match(/^Base64Url$/i) !== null) {
                payload = base64UrlToByteArray(responseBody);
            }
            else if (mapperType.match(/^Sequence$/i) !== null) {
                payload = deserializeSequenceType(this, mapper, responseBody, objectName, updatedOptions);
            }
            else if (mapperType.match(/^Dictionary$/i) !== null) {
                payload = deserializeDictionaryType(this, mapper, responseBody, objectName, updatedOptions);
            }
        }
        if (mapper.isConstant) {
            payload = mapper.defaultValue;
        }
        return payload;
    }
}
/**
 * Method that creates and returns a Serializer.
 * @param modelMappers - Known models to map
 * @param isXML - If XML should be supported
 */
function createSerializer(modelMappers = {}, isXML = false) {
    return new SerializerImpl(modelMappers, isXML);
}
function trimEnd(str, ch) {
    let len = str.length;
    while (len - 1 >= 0 && str[len - 1] === ch) {
        --len;
    }
    return str.substr(0, len);
}
function bufferToBase64Url(buffer) {
    if (!buffer) {
        return undefined;
    }
    if (!(buffer instanceof Uint8Array)) {
        throw new Error(`Please provide an input of type Uint8Array for converting to Base64Url.`);
    }
    // Uint8Array to Base64.
    const str = encodeByteArray(buffer);
    // Base64 to Base64Url.
    return trimEnd(str, "=").replace(/\+/g, "-").replace(/\//g, "_");
}
function base64UrlToByteArray(str) {
    if (!str) {
        return undefined;
    }
    if (str && typeof str.valueOf() !== "string") {
        throw new Error("Please provide an input of type string for converting to Uint8Array");
    }
    // Base64Url to Base64.
    str = str.replace(/-/g, "+").replace(/_/g, "/");
    // Base64 to Uint8Array.
    return decodeString(str);
}
function splitSerializeName(prop) {
    const classes = [];
    let partialclass = "";
    if (prop) {
        const subwords = prop.split(".");
        for (const item of subwords) {
            if (item.charAt(item.length - 1) === "\\") {
                partialclass += item.substr(0, item.length - 1) + ".";
            }
            else {
                partialclass += item;
                classes.push(partialclass);
                partialclass = "";
            }
        }
    }
    return classes;
}
function dateToUnixTime(d) {
    if (!d) {
        return undefined;
    }
    if (typeof d.valueOf() === "string") {
        d = new Date(d);
    }
    return Math.floor(d.getTime() / 1000);
}
function unixTimeToDate(n) {
    if (!n) {
        return undefined;
    }
    return new Date(n * 1000);
}
function serializeBasicTypes(typeName, objectName, value) {
    if (value !== null && value !== undefined) {
        if (typeName.match(/^Number$/i) !== null) {
            if (typeof value !== "number") {
                throw new Error(`${objectName} with value ${value} must be of type number.`);
            }
        }
        else if (typeName.match(/^String$/i) !== null) {
            if (typeof value.valueOf() !== "string") {
                throw new Error(`${objectName} with value "${value}" must be of type string.`);
            }
        }
        else if (typeName.match(/^Uuid$/i) !== null) {
            if (!(typeof value.valueOf() === "string" && isValidUuid(value))) {
                throw new Error(`${objectName} with value "${value}" must be of type string and a valid uuid.`);
            }
        }
        else if (typeName.match(/^Boolean$/i) !== null) {
            if (typeof value !== "boolean") {
                throw new Error(`${objectName} with value ${value} must be of type boolean.`);
            }
        }
        else if (typeName.match(/^Stream$/i) !== null) {
            const objectType = typeof value;
            if (objectType !== "string" &&
                typeof value.pipe !== "function" && // NodeJS.ReadableStream
                typeof value.tee !== "function" && // browser ReadableStream
                !(value instanceof ArrayBuffer) &&
                !ArrayBuffer.isView(value) &&
                // File objects count as a type of Blob, so we want to use instanceof explicitly
                !((typeof Blob === "function" || typeof Blob === "object") && value instanceof Blob) &&
                objectType !== "function") {
                throw new Error(`${objectName} must be a string, Blob, ArrayBuffer, ArrayBufferView, ReadableStream, or () => ReadableStream.`);
            }
        }
    }
    return value;
}
function serializeEnumType(objectName, allowedValues, value) {
    if (!allowedValues) {
        throw new Error(`Please provide a set of allowedValues to validate ${objectName} as an Enum Type.`);
    }
    const isPresent = allowedValues.some((item) => {
        if (typeof item.valueOf() === "string") {
            return item.toLowerCase() === value.toLowerCase();
        }
        return item === value;
    });
    if (!isPresent) {
        throw new Error(`${value} is not a valid value for ${objectName}. The valid values are: ${JSON.stringify(allowedValues)}.`);
    }
    return value;
}
function serializeByteArrayType(objectName, value) {
    if (value !== undefined && value !== null) {
        if (!(value instanceof Uint8Array)) {
            throw new Error(`${objectName} must be of type Uint8Array.`);
        }
        value = encodeByteArray(value);
    }
    return value;
}
function serializeBase64UrlType(objectName, value) {
    if (value !== undefined && value !== null) {
        if (!(value instanceof Uint8Array)) {
            throw new Error(`${objectName} must be of type Uint8Array.`);
        }
        value = bufferToBase64Url(value);
    }
    return value;
}
function serializeDateTypes(typeName, value, objectName) {
    if (value !== undefined && value !== null) {
        if (typeName.match(/^Date$/i) !== null) {
            if (!(value instanceof Date ||
                (typeof value.valueOf() === "string" && !isNaN(Date.parse(value))))) {
                throw new Error(`${objectName} must be an instanceof Date or a string in ISO8601 format.`);
            }
            value =
                value instanceof Date
                    ? value.toISOString().substring(0, 10)
                    : new Date(value).toISOString().substring(0, 10);
        }
        else if (typeName.match(/^DateTime$/i) !== null) {
            if (!(value instanceof Date ||
                (typeof value.valueOf() === "string" && !isNaN(Date.parse(value))))) {
                throw new Error(`${objectName} must be an instanceof Date or a string in ISO8601 format.`);
            }
            value = value instanceof Date ? value.toISOString() : new Date(value).toISOString();
        }
        else if (typeName.match(/^DateTimeRfc1123$/i) !== null) {
            if (!(value instanceof Date ||
                (typeof value.valueOf() === "string" && !isNaN(Date.parse(value))))) {
                throw new Error(`${objectName} must be an instanceof Date or a string in RFC-1123 format.`);
            }
            value = value instanceof Date ? value.toUTCString() : new Date(value).toUTCString();
        }
        else if (typeName.match(/^UnixTime$/i) !== null) {
            if (!(value instanceof Date ||
                (typeof value.valueOf() === "string" && !isNaN(Date.parse(value))))) {
                throw new Error(`${objectName} must be an instanceof Date or a string in RFC-1123/ISO8601 format ` +
                    `for it to be serialized in UnixTime/Epoch format.`);
            }
            value = dateToUnixTime(value);
        }
        else if (typeName.match(/^TimeSpan$/i) !== null) {
            if (!isDuration(value)) {
                throw new Error(`${objectName} must be a string in ISO 8601 format. Instead was "${value}".`);
            }
        }
    }
    return value;
}
function serializeSequenceType(serializer, mapper, object, objectName, isXml, options) {
    if (!Array.isArray(object)) {
        throw new Error(`${objectName} must be of type Array.`);
    }
    let elementType = mapper.type.element;
    if (!elementType || typeof elementType !== "object") {
        throw new Error(`element" metadata for an Array must be defined in the ` +
            `mapper and it must of type "object" in ${objectName}.`);
    }
    // Quirk: Composite mappers referenced by `element` might
    // not have *all* properties declared (like uberParent),
    // so let's try to look up the full definition by name.
    if (elementType.type.name === "Composite" && elementType.type.className) {
        elementType = serializer.modelMappers[elementType.type.className] ?? elementType;
    }
    const tempArray = [];
    for (let i = 0; i < object.length; i++) {
        const serializedValue = serializer.serialize(elementType, object[i], objectName, options);
        if (isXml && elementType.xmlNamespace) {
            const xmlnsKey = elementType.xmlNamespacePrefix
                ? `xmlns:${elementType.xmlNamespacePrefix}`
                : "xmlns";
            if (elementType.type.name === "Composite") {
                tempArray[i] = { ...serializedValue };
                tempArray[i][XML_ATTRKEY] = { [xmlnsKey]: elementType.xmlNamespace };
            }
            else {
                tempArray[i] = {};
                tempArray[i][options.xml.xmlCharKey] = serializedValue;
                tempArray[i][XML_ATTRKEY] = { [xmlnsKey]: elementType.xmlNamespace };
            }
        }
        else {
            tempArray[i] = serializedValue;
        }
    }
    return tempArray;
}
function serializeDictionaryType(serializer, mapper, object, objectName, isXml, options) {
    if (typeof object !== "object") {
        throw new Error(`${objectName} must be of type object.`);
    }
    const valueType = mapper.type.value;
    if (!valueType || typeof valueType !== "object") {
        throw new Error(`"value" metadata for a Dictionary must be defined in the ` +
            `mapper and it must of type "object" in ${objectName}.`);
    }
    const tempDictionary = {};
    for (const key of Object.keys(object)) {
        const serializedValue = serializer.serialize(valueType, object[key], objectName, options);
        // If the element needs an XML namespace we need to add it within the $ property
        tempDictionary[key] = getXmlObjectValue(valueType, serializedValue, isXml, options);
    }
    // Add the namespace to the root element if needed
    if (isXml && mapper.xmlNamespace) {
        const xmlnsKey = mapper.xmlNamespacePrefix ? `xmlns:${mapper.xmlNamespacePrefix}` : "xmlns";
        const result = tempDictionary;
        result[XML_ATTRKEY] = { [xmlnsKey]: mapper.xmlNamespace };
        return result;
    }
    return tempDictionary;
}
/**
 * Resolves the additionalProperties property from a referenced mapper
 * @param serializer - the serializer containing the entire set of mappers
 * @param mapper - the composite mapper to resolve
 * @param objectName - name of the object being serialized
 */
function resolveAdditionalProperties(serializer, mapper, objectName) {
    const additionalProperties = mapper.type.additionalProperties;
    if (!additionalProperties && mapper.type.className) {
        const modelMapper = resolveReferencedMapper(serializer, mapper, objectName);
        return modelMapper?.type.additionalProperties;
    }
    return additionalProperties;
}
/**
 * Finds the mapper referenced by className
 * @param serializer - the serializer containing the entire set of mappers
 * @param mapper - the composite mapper to resolve
 * @param objectName - name of the object being serialized
 */
function resolveReferencedMapper(serializer, mapper, objectName) {
    const className = mapper.type.className;
    if (!className) {
        throw new Error(`Class name for model "${objectName}" is not provided in the mapper "${JSON.stringify(mapper, undefined, 2)}".`);
    }
    return serializer.modelMappers[className];
}
/**
 * Resolves a composite mapper's modelProperties.
 * @param serializer - the serializer containing the entire set of mappers
 * @param mapper - the composite mapper to resolve
 */
function resolveModelProperties(serializer, mapper, objectName) {
    let modelProps = mapper.type.modelProperties;
    if (!modelProps) {
        const modelMapper = resolveReferencedMapper(serializer, mapper, objectName);
        if (!modelMapper) {
            throw new Error(`mapper() cannot be null or undefined for model "${mapper.type.className}".`);
        }
        modelProps = modelMapper?.type.modelProperties;
        if (!modelProps) {
            throw new Error(`modelProperties cannot be null or undefined in the ` +
                `mapper "${JSON.stringify(modelMapper)}" of type "${mapper.type.className}" for object "${objectName}".`);
        }
    }
    return modelProps;
}
function serializeCompositeType(serializer, mapper, object, objectName, isXml, options) {
    if (getPolymorphicDiscriminatorRecursively(serializer, mapper)) {
        mapper = getPolymorphicMapper(serializer, mapper, object, "clientName");
    }
    if (object !== undefined && object !== null) {
        const payload = {};
        const modelProps = resolveModelProperties(serializer, mapper, objectName);
        for (const key of Object.keys(modelProps)) {
            const propertyMapper = modelProps[key];
            if (propertyMapper.readOnly) {
                continue;
            }
            let propName;
            let parentObject = payload;
            if (serializer.isXML) {
                if (propertyMapper.xmlIsWrapped) {
                    propName = propertyMapper.xmlName;
                }
                else {
                    propName = propertyMapper.xmlElementName || propertyMapper.xmlName;
                }
            }
            else {
                const paths = splitSerializeName(propertyMapper.serializedName);
                propName = paths.pop();
                for (const pathName of paths) {
                    const childObject = parentObject[pathName];
                    if ((childObject === undefined || childObject === null) &&
                        ((object[key] !== undefined && object[key] !== null) ||
                            propertyMapper.defaultValue !== undefined)) {
                        parentObject[pathName] = {};
                    }
                    parentObject = parentObject[pathName];
                }
            }
            if (parentObject !== undefined && parentObject !== null) {
                if (isXml && mapper.xmlNamespace) {
                    const xmlnsKey = mapper.xmlNamespacePrefix
                        ? `xmlns:${mapper.xmlNamespacePrefix}`
                        : "xmlns";
                    parentObject[XML_ATTRKEY] = {
                        ...parentObject[XML_ATTRKEY],
                        [xmlnsKey]: mapper.xmlNamespace,
                    };
                }
                const propertyObjectName = propertyMapper.serializedName !== ""
                    ? objectName + "." + propertyMapper.serializedName
                    : objectName;
                let toSerialize = object[key];
                const polymorphicDiscriminator = getPolymorphicDiscriminatorRecursively(serializer, mapper);
                if (polymorphicDiscriminator &&
                    polymorphicDiscriminator.clientName === key &&
                    (toSerialize === undefined || toSerialize === null)) {
                    toSerialize = mapper.serializedName;
                }
                const serializedValue = serializer.serialize(propertyMapper, toSerialize, propertyObjectName, options);
                if (serializedValue !== undefined && propName !== undefined && propName !== null) {
                    const value = getXmlObjectValue(propertyMapper, serializedValue, isXml, options);
                    if (isXml && propertyMapper.xmlIsAttribute) {
                        // XML_ATTRKEY, i.e., $ is the key attributes are kept under in xml2js.
                        // This keeps things simple while preventing name collision
                        // with names in user documents.
                        parentObject[XML_ATTRKEY] = parentObject[XML_ATTRKEY] || {};
                        parentObject[XML_ATTRKEY][propName] = serializedValue;
                    }
                    else if (isXml && propertyMapper.xmlIsWrapped) {
                        parentObject[propName] = { [propertyMapper.xmlElementName]: value };
                    }
                    else {
                        parentObject[propName] = value;
                    }
                }
            }
        }
        const additionalPropertiesMapper = resolveAdditionalProperties(serializer, mapper, objectName);
        if (additionalPropertiesMapper) {
            const propNames = Object.keys(modelProps);
            for (const clientPropName in object) {
                const isAdditionalProperty = propNames.every((pn) => pn !== clientPropName);
                if (isAdditionalProperty) {
                    payload[clientPropName] = serializer.serialize(additionalPropertiesMapper, object[clientPropName], objectName + '["' + clientPropName + '"]', options);
                }
            }
        }
        return payload;
    }
    return object;
}
function getXmlObjectValue(propertyMapper, serializedValue, isXml, options) {
    if (!isXml || !propertyMapper.xmlNamespace) {
        return serializedValue;
    }
    const xmlnsKey = propertyMapper.xmlNamespacePrefix
        ? `xmlns:${propertyMapper.xmlNamespacePrefix}`
        : "xmlns";
    const xmlNamespace = { [xmlnsKey]: propertyMapper.xmlNamespace };
    if (["Composite"].includes(propertyMapper.type.name)) {
        if (serializedValue[XML_ATTRKEY]) {
            return serializedValue;
        }
        else {
            const result = { ...serializedValue };
            result[XML_ATTRKEY] = xmlNamespace;
            return result;
        }
    }
    const result = {};
    result[options.xml.xmlCharKey] = serializedValue;
    result[XML_ATTRKEY] = xmlNamespace;
    return result;
}
function isSpecialXmlProperty(propertyName, options) {
    return [XML_ATTRKEY, options.xml.xmlCharKey].includes(propertyName);
}
function deserializeCompositeType(serializer, mapper, responseBody, objectName, options) {
    const xmlCharKey = options.xml.xmlCharKey ?? XML_CHARKEY;
    if (getPolymorphicDiscriminatorRecursively(serializer, mapper)) {
        mapper = getPolymorphicMapper(serializer, mapper, responseBody, "serializedName");
    }
    const modelProps = resolveModelProperties(serializer, mapper, objectName);
    let instance = {};
    const handledPropertyNames = [];
    for (const key of Object.keys(modelProps)) {
        const propertyMapper = modelProps[key];
        const paths = splitSerializeName(modelProps[key].serializedName);
        handledPropertyNames.push(paths[0]);
        const { serializedName, xmlName, xmlElementName } = propertyMapper;
        let propertyObjectName = objectName;
        if (serializedName !== "" && serializedName !== undefined) {
            propertyObjectName = objectName + "." + serializedName;
        }
        const headerCollectionPrefix = propertyMapper.headerCollectionPrefix;
        if (headerCollectionPrefix) {
            const dictionary = {};
            for (const headerKey of Object.keys(responseBody)) {
                if (headerKey.startsWith(headerCollectionPrefix)) {
                    dictionary[headerKey.substring(headerCollectionPrefix.length)] = serializer.deserialize(propertyMapper.type.value, responseBody[headerKey], propertyObjectName, options);
                }
                handledPropertyNames.push(headerKey);
            }
            instance[key] = dictionary;
        }
        else if (serializer.isXML) {
            if (propertyMapper.xmlIsAttribute && responseBody[XML_ATTRKEY]) {
                instance[key] = serializer.deserialize(propertyMapper, responseBody[XML_ATTRKEY][xmlName], propertyObjectName, options);
            }
            else if (propertyMapper.xmlIsMsText) {
                if (responseBody[xmlCharKey] !== undefined) {
                    instance[key] = responseBody[xmlCharKey];
                }
                else if (typeof responseBody === "string") {
                    // The special case where xml parser parses "<Name>content</Name>" into JSON of
                    //   `{ name: "content"}` instead of `{ name: { "_": "content" }}`
                    instance[key] = responseBody;
                }
            }
            else {
                const propertyName = xmlElementName || xmlName || serializedName;
                if (propertyMapper.xmlIsWrapped) {
                    /* a list of <xmlElementName> wrapped by <xmlName>
                      For the xml example below
                        <Cors>
                          <CorsRule>...</CorsRule>
                          <CorsRule>...</CorsRule>
                        </Cors>
                      the responseBody has
                        {
                          Cors: {
                            CorsRule: [{...}, {...}]
                          }
                        }
                      xmlName is "Cors" and xmlElementName is"CorsRule".
                    */
                    const wrapped = responseBody[xmlName];
                    const elementList = wrapped?.[xmlElementName] ?? [];
                    instance[key] = serializer.deserialize(propertyMapper, elementList, propertyObjectName, options);
                    handledPropertyNames.push(xmlName);
                }
                else {
                    const property = responseBody[propertyName];
                    instance[key] = serializer.deserialize(propertyMapper, property, propertyObjectName, options);
                    handledPropertyNames.push(propertyName);
                }
            }
        }
        else {
            // deserialize the property if it is present in the provided responseBody instance
            let propertyInstance;
            let res = responseBody;
            // traversing the object step by step.
            let steps = 0;
            for (const item of paths) {
                if (!res)
                    break;
                steps++;
                res = res[item];
            }
            // only accept null when reaching the last position of object otherwise it would be undefined
            if (res === null && steps < paths.length) {
                res = undefined;
            }
            propertyInstance = res;
            const polymorphicDiscriminator = mapper.type.polymorphicDiscriminator;
            // checking that the model property name (key)(ex: "fishtype") and the
            // clientName of the polymorphicDiscriminator {metadata} (ex: "fishtype")
            // instead of the serializedName of the polymorphicDiscriminator (ex: "fish.type")
            // is a better approach. The generator is not consistent with escaping '\.' in the
            // serializedName of the property (ex: "fish\.type") that is marked as polymorphic discriminator
            // and the serializedName of the metadata polymorphicDiscriminator (ex: "fish.type"). However,
            // the clientName transformation of the polymorphicDiscriminator (ex: "fishtype") and
            // the transformation of model property name (ex: "fishtype") is done consistently.
            // Hence, it is a safer bet to rely on the clientName of the polymorphicDiscriminator.
            if (polymorphicDiscriminator &&
                key === polymorphicDiscriminator.clientName &&
                (propertyInstance === undefined || propertyInstance === null)) {
                propertyInstance = mapper.serializedName;
            }
            let serializedValue;
            // paging
            if (Array.isArray(responseBody[key]) && modelProps[key].serializedName === "") {
                propertyInstance = responseBody[key];
                const arrayInstance = serializer.deserialize(propertyMapper, propertyInstance, propertyObjectName, options);
                // Copy over any properties that have already been added into the instance, where they do
                // not exist on the newly de-serialized array
                for (const [k, v] of Object.entries(instance)) {
                    if (!Object.prototype.hasOwnProperty.call(arrayInstance, k)) {
                        arrayInstance[k] = v;
                    }
                }
                instance = arrayInstance;
            }
            else if (propertyInstance !== undefined || propertyMapper.defaultValue !== undefined) {
                serializedValue = serializer.deserialize(propertyMapper, propertyInstance, propertyObjectName, options);
                instance[key] = serializedValue;
            }
        }
    }
    const additionalPropertiesMapper = mapper.type.additionalProperties;
    if (additionalPropertiesMapper) {
        const isAdditionalProperty = (responsePropName) => {
            for (const clientPropName in modelProps) {
                const paths = splitSerializeName(modelProps[clientPropName].serializedName);
                if (paths[0] === responsePropName) {
                    return false;
                }
            }
            return true;
        };
        for (const responsePropName in responseBody) {
            if (isAdditionalProperty(responsePropName)) {
                instance[responsePropName] = serializer.deserialize(additionalPropertiesMapper, responseBody[responsePropName], objectName + '["' + responsePropName + '"]', options);
            }
        }
    }
    else if (responseBody && !options.ignoreUnknownProperties) {
        for (const key of Object.keys(responseBody)) {
            if (instance[key] === undefined &&
                !handledPropertyNames.includes(key) &&
                !isSpecialXmlProperty(key, options)) {
                instance[key] = responseBody[key];
            }
        }
    }
    return instance;
}
function deserializeDictionaryType(serializer, mapper, responseBody, objectName, options) {
    /* jshint validthis: true */
    const value = mapper.type.value;
    if (!value || typeof value !== "object") {
        throw new Error(`"value" metadata for a Dictionary must be defined in the ` +
            `mapper and it must of type "object" in ${objectName}`);
    }
    if (responseBody) {
        const tempDictionary = {};
        for (const key of Object.keys(responseBody)) {
            tempDictionary[key] = serializer.deserialize(value, responseBody[key], objectName, options);
        }
        return tempDictionary;
    }
    return responseBody;
}
function deserializeSequenceType(serializer, mapper, responseBody, objectName, options) {
    let element = mapper.type.element;
    if (!element || typeof element !== "object") {
        throw new Error(`element" metadata for an Array must be defined in the ` +
            `mapper and it must of type "object" in ${objectName}`);
    }
    if (responseBody) {
        if (!Array.isArray(responseBody)) {
            // xml2js will interpret a single element array as just the element, so force it to be an array
            responseBody = [responseBody];
        }
        // Quirk: Composite mappers referenced by `element` might
        // not have *all* properties declared (like uberParent),
        // so let's try to look up the full definition by name.
        if (element.type.name === "Composite" && element.type.className) {
            element = serializer.modelMappers[element.type.className] ?? element;
        }
        const tempArray = [];
        for (let i = 0; i < responseBody.length; i++) {
            tempArray[i] = serializer.deserialize(element, responseBody[i], `${objectName}[${i}]`, options);
        }
        return tempArray;
    }
    return responseBody;
}
function getIndexDiscriminator(discriminators, discriminatorValue, typeName) {
    const typeNamesToCheck = [typeName];
    while (typeNamesToCheck.length) {
        const currentName = typeNamesToCheck.shift();
        const indexDiscriminator = discriminatorValue === currentName
            ? discriminatorValue
            : currentName + "." + discriminatorValue;
        if (Object.prototype.hasOwnProperty.call(discriminators, indexDiscriminator)) {
            return discriminators[indexDiscriminator];
        }
        else {
            for (const [name, mapper] of Object.entries(discriminators)) {
                if (name.startsWith(currentName + ".") &&
                    mapper.type.uberParent === currentName &&
                    mapper.type.className) {
                    typeNamesToCheck.push(mapper.type.className);
                }
            }
        }
    }
    return undefined;
}
function getPolymorphicMapper(serializer, mapper, object, polymorphicPropertyName) {
    const polymorphicDiscriminator = getPolymorphicDiscriminatorRecursively(serializer, mapper);
    if (polymorphicDiscriminator) {
        let discriminatorName = polymorphicDiscriminator[polymorphicPropertyName];
        if (discriminatorName) {
            // The serializedName might have \\, which we just want to ignore
            if (polymorphicPropertyName === "serializedName") {
                discriminatorName = discriminatorName.replace(/\\/gi, "");
            }
            const discriminatorValue = object[discriminatorName];
            const typeName = mapper.type.uberParent ?? mapper.type.className;
            if (typeof discriminatorValue === "string" && typeName) {
                const polymorphicMapper = getIndexDiscriminator(serializer.modelMappers.discriminators, discriminatorValue, typeName);
                if (polymorphicMapper) {
                    mapper = polymorphicMapper;
                }
            }
        }
    }
    return mapper;
}
function getPolymorphicDiscriminatorRecursively(serializer, mapper) {
    return (mapper.type.polymorphicDiscriminator ||
        getPolymorphicDiscriminatorSafely(serializer, mapper.type.uberParent) ||
        getPolymorphicDiscriminatorSafely(serializer, mapper.type.className));
}
function getPolymorphicDiscriminatorSafely(serializer, typeName) {
    return (typeName &&
        serializer.modelMappers[typeName] &&
        serializer.modelMappers[typeName].type.polymorphicDiscriminator);
}
/**
 * Known types of Mappers
 */
const MapperTypeNames = {
    Base64Url: "Base64Url",
    Boolean: "Boolean",
    ByteArray: "ByteArray",
    Composite: "Composite",
    Date: "Date",
    DateTime: "DateTime",
    DateTimeRfc1123: "DateTimeRfc1123",
    Dictionary: "Dictionary",
    Enum: "Enum",
    Number: "Number",
    Object: "Object",
    Sequence: "Sequence",
    String: "String",
    Stream: "Stream",
    TimeSpan: "TimeSpan",
    UnixTime: "UnixTime",
};
//# sourceMappingURL=serializer.js.map
// EXTERNAL MODULE: ./node_modules/@azure/core-client/dist/commonjs/state.js
var dist_commonjs_state = __nccwpck_require__(3345);
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/state.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
// @ts-expect-error The recommended approach to sharing module state between ESM and CJS.
// See https://github.com/isaacs/tshy/blob/main/README.md#module-local-state for additional information.

/**
 * Defines the shared state between CJS and ESM by re-exporting the CJS state.
 */
const esm_state_state = dist_commonjs_state/* state */.w;
//# sourceMappingURL=state.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/operationHelpers.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * @internal
 * Retrieves the value to use for a given operation argument
 * @param operationArguments - The arguments passed from the generated client
 * @param parameter - The parameter description
 * @param fallbackObject - If something isn't found in the arguments bag, look here.
 *  Generally used to look at the service client properties.
 */
function getOperationArgumentValueFromParameter(operationArguments, parameter, fallbackObject) {
    let parameterPath = parameter.parameterPath;
    const parameterMapper = parameter.mapper;
    let value;
    if (typeof parameterPath === "string") {
        parameterPath = [parameterPath];
    }
    if (Array.isArray(parameterPath)) {
        if (parameterPath.length > 0) {
            if (parameterMapper.isConstant) {
                value = parameterMapper.defaultValue;
            }
            else {
                let propertySearchResult = getPropertyFromParameterPath(operationArguments, parameterPath);
                if (!propertySearchResult.propertyFound && fallbackObject) {
                    propertySearchResult = getPropertyFromParameterPath(fallbackObject, parameterPath);
                }
                let useDefaultValue = false;
                if (!propertySearchResult.propertyFound) {
                    useDefaultValue =
                        parameterMapper.required ||
                            (parameterPath[0] === "options" && parameterPath.length === 2);
                }
                value = useDefaultValue ? parameterMapper.defaultValue : propertySearchResult.propertyValue;
            }
        }
    }
    else {
        if (parameterMapper.required) {
            value = {};
        }
        for (const propertyName in parameterPath) {
            const propertyMapper = parameterMapper.type.modelProperties[propertyName];
            const propertyPath = parameterPath[propertyName];
            const propertyValue = getOperationArgumentValueFromParameter(operationArguments, {
                parameterPath: propertyPath,
                mapper: propertyMapper,
            }, fallbackObject);
            if (propertyValue !== undefined) {
                if (!value) {
                    value = {};
                }
                value[propertyName] = propertyValue;
            }
        }
    }
    return value;
}
function getPropertyFromParameterPath(parent, parameterPath) {
    const result = { propertyFound: false };
    let i = 0;
    for (; i < parameterPath.length; ++i) {
        const parameterPathPart = parameterPath[i];
        // Make sure to check inherited properties too, so don't use hasOwnProperty().
        if (parent && parameterPathPart in parent) {
            parent = parent[parameterPathPart];
        }
        else {
            break;
        }
    }
    if (i === parameterPath.length) {
        result.propertyValue = parent;
        result.propertyFound = true;
    }
    return result;
}
const originalRequestSymbol = Symbol.for("@azure/core-client original request");
function hasOriginalRequest(request) {
    return originalRequestSymbol in request;
}
function getOperationRequestInfo(request) {
    if (hasOriginalRequest(request)) {
        return getOperationRequestInfo(request[originalRequestSymbol]);
    }
    let info = esm_state_state.operationRequestMap.get(request);
    if (!info) {
        info = {};
        esm_state_state.operationRequestMap.set(request, info);
    }
    return info;
}
//# sourceMappingURL=operationHelpers.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/deserializationPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




const defaultJsonContentTypes = ["application/json", "text/json"];
const defaultXmlContentTypes = ["application/xml", "application/atom+xml"];
/**
 * The programmatic identifier of the deserializationPolicy.
 */
const deserializationPolicyName = "deserializationPolicy";
/**
 * This policy handles parsing out responses according to OperationSpecs on the request.
 */
function deserializationPolicy(options = {}) {
    const jsonContentTypes = options.expectedContentTypes?.json ?? defaultJsonContentTypes;
    const xmlContentTypes = options.expectedContentTypes?.xml ?? defaultXmlContentTypes;
    const parseXML = options.parseXML;
    const serializerOptions = options.serializerOptions;
    const updatedOptions = {
        xml: {
            rootName: serializerOptions?.xml.rootName ?? "",
            includeRoot: serializerOptions?.xml.includeRoot ?? false,
            xmlCharKey: serializerOptions?.xml.xmlCharKey ?? XML_CHARKEY,
        },
    };
    return {
        name: deserializationPolicyName,
        async sendRequest(request, next) {
            const response = await next(request);
            return deserializeResponseBody(jsonContentTypes, xmlContentTypes, response, updatedOptions, parseXML);
        },
    };
}
function getOperationResponseMap(parsedResponse) {
    let result;
    const request = parsedResponse.request;
    const operationInfo = getOperationRequestInfo(request);
    const operationSpec = operationInfo?.operationSpec;
    if (operationSpec) {
        if (!operationInfo?.operationResponseGetter) {
            result = operationSpec.responses[parsedResponse.status];
        }
        else {
            result = operationInfo?.operationResponseGetter(operationSpec, parsedResponse);
        }
    }
    return result;
}
function shouldDeserializeResponse(parsedResponse) {
    const request = parsedResponse.request;
    const operationInfo = getOperationRequestInfo(request);
    const shouldDeserialize = operationInfo?.shouldDeserialize;
    let result;
    if (shouldDeserialize === undefined) {
        result = true;
    }
    else if (typeof shouldDeserialize === "boolean") {
        result = shouldDeserialize;
    }
    else {
        result = shouldDeserialize(parsedResponse);
    }
    return result;
}
async function deserializeResponseBody(jsonContentTypes, xmlContentTypes, response, options, parseXML) {
    const parsedResponse = await parse(jsonContentTypes, xmlContentTypes, response, options, parseXML);
    if (!shouldDeserializeResponse(parsedResponse)) {
        return parsedResponse;
    }
    const operationInfo = getOperationRequestInfo(parsedResponse.request);
    const operationSpec = operationInfo?.operationSpec;
    if (!operationSpec || !operationSpec.responses) {
        return parsedResponse;
    }
    const responseSpec = getOperationResponseMap(parsedResponse);
    const { error, shouldReturnResponse } = handleErrorResponse(parsedResponse, operationSpec, responseSpec, options);
    if (error) {
        throw error;
    }
    else if (shouldReturnResponse) {
        return parsedResponse;
    }
    // An operation response spec does exist for current status code, so
    // use it to deserialize the response.
    if (responseSpec) {
        if (responseSpec.bodyMapper) {
            let valueToDeserialize = parsedResponse.parsedBody;
            if (operationSpec.isXML && responseSpec.bodyMapper.type.name === MapperTypeNames.Sequence) {
                valueToDeserialize =
                    typeof valueToDeserialize === "object"
                        ? valueToDeserialize[responseSpec.bodyMapper.xmlElementName]
                        : [];
            }
            try {
                parsedResponse.parsedBody = operationSpec.serializer.deserialize(responseSpec.bodyMapper, valueToDeserialize, "operationRes.parsedBody", options);
            }
            catch (deserializeError) {
                const restError = new esm_restError_RestError(`Error ${deserializeError} occurred in deserializing the responseBody - ${parsedResponse.bodyAsText}`, {
                    statusCode: parsedResponse.status,
                    request: parsedResponse.request,
                    response: parsedResponse,
                });
                throw restError;
            }
        }
        else if (operationSpec.httpMethod === "HEAD") {
            // head methods never have a body, but we return a boolean to indicate presence/absence of the resource
            parsedResponse.parsedBody = response.status >= 200 && response.status < 300;
        }
        if (responseSpec.headersMapper) {
            parsedResponse.parsedHeaders = operationSpec.serializer.deserialize(responseSpec.headersMapper, parsedResponse.headers.toJSON(), "operationRes.parsedHeaders", { xml: {}, ignoreUnknownProperties: true });
        }
    }
    return parsedResponse;
}
function isOperationSpecEmpty(operationSpec) {
    const expectedStatusCodes = Object.keys(operationSpec.responses);
    return (expectedStatusCodes.length === 0 ||
        (expectedStatusCodes.length === 1 && expectedStatusCodes[0] === "default"));
}
function handleErrorResponse(parsedResponse, operationSpec, responseSpec, options) {
    const isSuccessByStatus = 200 <= parsedResponse.status && parsedResponse.status < 300;
    const isExpectedStatusCode = isOperationSpecEmpty(operationSpec)
        ? isSuccessByStatus
        : !!responseSpec;
    if (isExpectedStatusCode) {
        if (responseSpec) {
            if (!responseSpec.isError) {
                return { error: null, shouldReturnResponse: false };
            }
        }
        else {
            return { error: null, shouldReturnResponse: false };
        }
    }
    const errorResponseSpec = responseSpec ?? operationSpec.responses.default;
    const initialErrorMessage = parsedResponse.request.streamResponseStatusCodes?.has(parsedResponse.status)
        ? `Unexpected status code: ${parsedResponse.status}`
        : parsedResponse.bodyAsText;
    const error = new esm_restError_RestError(initialErrorMessage, {
        statusCode: parsedResponse.status,
        request: parsedResponse.request,
        response: parsedResponse,
    });
    // If the item failed but there's no error spec or default spec to deserialize the error,
    // and the parsed body doesn't look like an error object,
    // we should fail so we just throw the parsed response
    if (!errorResponseSpec &&
        !(parsedResponse.parsedBody?.error?.code && parsedResponse.parsedBody?.error?.message)) {
        throw error;
    }
    const defaultBodyMapper = errorResponseSpec?.bodyMapper;
    const defaultHeadersMapper = errorResponseSpec?.headersMapper;
    try {
        // If error response has a body, try to deserialize it using default body mapper.
        // Then try to extract error code & message from it
        if (parsedResponse.parsedBody) {
            const parsedBody = parsedResponse.parsedBody;
            let deserializedError;
            if (defaultBodyMapper) {
                let valueToDeserialize = parsedBody;
                if (operationSpec.isXML && defaultBodyMapper.type.name === MapperTypeNames.Sequence) {
                    valueToDeserialize = [];
                    const elementName = defaultBodyMapper.xmlElementName;
                    if (typeof parsedBody === "object" && elementName) {
                        valueToDeserialize = parsedBody[elementName];
                    }
                }
                deserializedError = operationSpec.serializer.deserialize(defaultBodyMapper, valueToDeserialize, "error.response.parsedBody", options);
            }
            const internalError = parsedBody.error || deserializedError || parsedBody;
            error.code = internalError.code;
            if (internalError.message) {
                error.message = internalError.message;
            }
            if (defaultBodyMapper) {
                error.response.parsedBody = deserializedError;
            }
        }
        // If error response has headers, try to deserialize it using default header mapper
        if (parsedResponse.headers && defaultHeadersMapper) {
            error.response.parsedHeaders =
                operationSpec.serializer.deserialize(defaultHeadersMapper, parsedResponse.headers.toJSON(), "operationRes.parsedHeaders");
        }
    }
    catch (defaultError) {
        error.message = `Error "${defaultError.message}" occurred in deserializing the responseBody - "${parsedResponse.bodyAsText}" for the default response.`;
    }
    return { error, shouldReturnResponse: false };
}
async function parse(jsonContentTypes, xmlContentTypes, operationResponse, opts, parseXML) {
    if (!operationResponse.request.streamResponseStatusCodes?.has(operationResponse.status) &&
        operationResponse.bodyAsText) {
        const text = operationResponse.bodyAsText;
        const contentType = operationResponse.headers.get("Content-Type") || "";
        const contentComponents = !contentType
            ? []
            : contentType.split(";").map((component) => component.toLowerCase());
        try {
            if (contentComponents.length === 0 ||
                contentComponents.some((component) => jsonContentTypes.indexOf(component) !== -1)) {
                operationResponse.parsedBody = JSON.parse(text);
                return operationResponse;
            }
            else if (contentComponents.some((component) => xmlContentTypes.indexOf(component) !== -1)) {
                if (!parseXML) {
                    throw new Error("Parsing XML not supported.");
                }
                const body = await parseXML(text, opts.xml);
                operationResponse.parsedBody = body;
                return operationResponse;
            }
        }
        catch (err) {
            const msg = `Error "${err}" occurred while parsing the response body - ${operationResponse.bodyAsText}.`;
            const errCode = err.code || esm_restError_RestError.PARSE_ERROR;
            const e = new esm_restError_RestError(msg, {
                code: errCode,
                statusCode: operationResponse.status,
                request: operationResponse.request,
                response: operationResponse,
            });
            throw e;
        }
    }
    return operationResponse;
}
//# sourceMappingURL=deserializationPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/interfaceHelpers.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Gets the list of status codes for streaming responses.
 * @internal
 */
function getStreamingResponseStatusCodes(operationSpec) {
    const result = new Set();
    for (const statusCode in operationSpec.responses) {
        const operationResponse = operationSpec.responses[statusCode];
        if (operationResponse.bodyMapper &&
            operationResponse.bodyMapper.type.name === MapperTypeNames.Stream) {
            result.add(Number(statusCode));
        }
    }
    return result;
}
/**
 * Get the path to this parameter's value as a dotted string (a.b.c).
 * @param parameter - The parameter to get the path string for.
 * @returns The path to this parameter's value as a dotted string.
 * @internal
 */
function getPathStringFromParameter(parameter) {
    const { parameterPath, mapper } = parameter;
    let result;
    if (typeof parameterPath === "string") {
        result = parameterPath;
    }
    else if (Array.isArray(parameterPath)) {
        result = parameterPath.join(".");
    }
    else {
        result = mapper.serializedName;
    }
    return result;
}
//# sourceMappingURL=interfaceHelpers.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/serializationPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




/**
 * The programmatic identifier of the serializationPolicy.
 */
const serializationPolicyName = "serializationPolicy";
/**
 * This policy handles assembling the request body and headers using
 * an OperationSpec and OperationArguments on the request.
 */
function serializationPolicy(options = {}) {
    const stringifyXML = options.stringifyXML;
    return {
        name: serializationPolicyName,
        async sendRequest(request, next) {
            const operationInfo = getOperationRequestInfo(request);
            const operationSpec = operationInfo?.operationSpec;
            const operationArguments = operationInfo?.operationArguments;
            if (operationSpec && operationArguments) {
                serializeHeaders(request, operationArguments, operationSpec);
                serializeRequestBody(request, operationArguments, operationSpec, stringifyXML);
            }
            return next(request);
        },
    };
}
/**
 * @internal
 */
function serializeHeaders(request, operationArguments, operationSpec) {
    if (operationSpec.headerParameters) {
        for (const headerParameter of operationSpec.headerParameters) {
            let headerValue = getOperationArgumentValueFromParameter(operationArguments, headerParameter);
            if ((headerValue !== null && headerValue !== undefined) || headerParameter.mapper.required) {
                headerValue = operationSpec.serializer.serialize(headerParameter.mapper, headerValue, getPathStringFromParameter(headerParameter));
                const headerCollectionPrefix = headerParameter.mapper
                    .headerCollectionPrefix;
                if (headerCollectionPrefix) {
                    for (const key of Object.keys(headerValue)) {
                        request.headers.set(headerCollectionPrefix + key, headerValue[key]);
                    }
                }
                else {
                    request.headers.set(headerParameter.mapper.serializedName || getPathStringFromParameter(headerParameter), headerValue);
                }
            }
        }
    }
    const customHeaders = operationArguments.options?.requestOptions?.customHeaders;
    if (customHeaders) {
        for (const customHeaderName of Object.keys(customHeaders)) {
            request.headers.set(customHeaderName, customHeaders[customHeaderName]);
        }
    }
}
/**
 * @internal
 */
function serializeRequestBody(request, operationArguments, operationSpec, stringifyXML = function () {
    throw new Error("XML serialization unsupported!");
}) {
    const serializerOptions = operationArguments.options?.serializerOptions;
    const updatedOptions = {
        xml: {
            rootName: serializerOptions?.xml.rootName ?? "",
            includeRoot: serializerOptions?.xml.includeRoot ?? false,
            xmlCharKey: serializerOptions?.xml.xmlCharKey ?? XML_CHARKEY,
        },
    };
    const xmlCharKey = updatedOptions.xml.xmlCharKey;
    if (operationSpec.requestBody && operationSpec.requestBody.mapper) {
        request.body = getOperationArgumentValueFromParameter(operationArguments, operationSpec.requestBody);
        const bodyMapper = operationSpec.requestBody.mapper;
        const { required, serializedName, xmlName, xmlElementName, xmlNamespace, xmlNamespacePrefix, nullable, } = bodyMapper;
        const typeName = bodyMapper.type.name;
        try {
            if ((request.body !== undefined && request.body !== null) ||
                (nullable && request.body === null) ||
                required) {
                const requestBodyParameterPathString = getPathStringFromParameter(operationSpec.requestBody);
                request.body = operationSpec.serializer.serialize(bodyMapper, request.body, requestBodyParameterPathString, updatedOptions);
                const isStream = typeName === MapperTypeNames.Stream;
                if (operationSpec.isXML) {
                    const xmlnsKey = xmlNamespacePrefix ? `xmlns:${xmlNamespacePrefix}` : "xmlns";
                    const value = getXmlValueWithNamespace(xmlNamespace, xmlnsKey, typeName, request.body, updatedOptions);
                    if (typeName === MapperTypeNames.Sequence) {
                        request.body = stringifyXML(prepareXMLRootList(value, xmlElementName || xmlName || serializedName, xmlnsKey, xmlNamespace), { rootName: xmlName || serializedName, xmlCharKey });
                    }
                    else if (!isStream) {
                        request.body = stringifyXML(value, {
                            rootName: xmlName || serializedName,
                            xmlCharKey,
                        });
                    }
                }
                else if (typeName === MapperTypeNames.String &&
                    (operationSpec.contentType?.match("text/plain") || operationSpec.mediaType === "text")) {
                    // the String serializer has validated that request body is a string
                    // so just send the string.
                    return;
                }
                else if (!isStream) {
                    request.body = JSON.stringify(request.body);
                }
            }
        }
        catch (error) {
            throw new Error(`Error "${error.message}" occurred in serializing the payload - ${JSON.stringify(serializedName, undefined, "  ")}.`);
        }
    }
    else if (operationSpec.formDataParameters && operationSpec.formDataParameters.length > 0) {
        request.formData = {};
        for (const formDataParameter of operationSpec.formDataParameters) {
            const formDataParameterValue = getOperationArgumentValueFromParameter(operationArguments, formDataParameter);
            if (formDataParameterValue !== undefined && formDataParameterValue !== null) {
                const formDataParameterPropertyName = formDataParameter.mapper.serializedName || getPathStringFromParameter(formDataParameter);
                request.formData[formDataParameterPropertyName] = operationSpec.serializer.serialize(formDataParameter.mapper, formDataParameterValue, getPathStringFromParameter(formDataParameter), updatedOptions);
            }
        }
    }
}
/**
 * Adds an xml namespace to the xml serialized object if needed, otherwise it just returns the value itself
 */
function getXmlValueWithNamespace(xmlNamespace, xmlnsKey, typeName, serializedValue, options) {
    // Composite and Sequence schemas already got their root namespace set during serialization
    // We just need to add xmlns to the other schema types
    if (xmlNamespace && !["Composite", "Sequence", "Dictionary"].includes(typeName)) {
        const result = {};
        result[options.xml.xmlCharKey] = serializedValue;
        result[XML_ATTRKEY] = { [xmlnsKey]: xmlNamespace };
        return result;
    }
    return serializedValue;
}
function prepareXMLRootList(obj, elementName, xmlNamespaceKey, xmlNamespace) {
    if (!Array.isArray(obj)) {
        obj = [obj];
    }
    if (!xmlNamespaceKey || !xmlNamespace) {
        return { [elementName]: obj };
    }
    const result = { [elementName]: obj };
    result[XML_ATTRKEY] = { [xmlNamespaceKey]: xmlNamespace };
    return result;
}
//# sourceMappingURL=serializationPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/pipeline.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.



/**
 * Creates a new Pipeline for use with a Service Client.
 * Adds in deserializationPolicy by default.
 * Also adds in bearerTokenAuthenticationPolicy if passed a TokenCredential.
 * @param options - Options to customize the created pipeline.
 */
function createClientPipeline(options = {}) {
    const pipeline = esm_createPipelineFromOptions_createPipelineFromOptions(options ?? {});
    if (options.credentialOptions) {
        pipeline.addPolicy(bearerTokenAuthenticationPolicy({
            credential: options.credentialOptions.credential,
            scopes: options.credentialOptions.credentialScopes,
        }));
    }
    pipeline.addPolicy(serializationPolicy(options.serializationOptions), { phase: "Serialize" });
    pipeline.addPolicy(deserializationPolicy(options.deserializationOptions), {
        phase: "Deserialize",
    });
    return pipeline;
}
//# sourceMappingURL=pipeline.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/httpClientCache.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

let httpClientCache_cachedHttpClient;
function getCachedDefaultHttpClient() {
    if (!httpClientCache_cachedHttpClient) {
        httpClientCache_cachedHttpClient = esm_defaultHttpClient_createDefaultHttpClient();
    }
    return httpClientCache_cachedHttpClient;
}
//# sourceMappingURL=httpClientCache.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/urlHelpers.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


const CollectionFormatToDelimiterMap = {
    CSV: ",",
    SSV: " ",
    Multi: "Multi",
    TSV: "\t",
    Pipes: "|",
};
function getRequestUrl(baseUri, operationSpec, operationArguments, fallbackObject) {
    const urlReplacements = calculateUrlReplacements(operationSpec, operationArguments, fallbackObject);
    let isAbsolutePath = false;
    let requestUrl = replaceAll(baseUri, urlReplacements);
    if (operationSpec.path) {
        let path = replaceAll(operationSpec.path, urlReplacements);
        // QUIRK: sometimes we get a path component like /{nextLink}
        // which may be a fully formed URL with a leading /. In that case, we should
        // remove the leading /
        if (operationSpec.path === "/{nextLink}" && path.startsWith("/")) {
            path = path.substring(1);
        }
        // QUIRK: sometimes we get a path component like {nextLink}
        // which may be a fully formed URL. In that case, we should
        // ignore the baseUri.
        if (isAbsoluteUrl(path)) {
            requestUrl = path;
            isAbsolutePath = true;
        }
        else {
            requestUrl = appendPath(requestUrl, path);
        }
    }
    const { queryParams, sequenceParams } = calculateQueryParameters(operationSpec, operationArguments, fallbackObject);
    /**
     * Notice that this call sets the `noOverwrite` parameter to true if the `requestUrl`
     * is an absolute path. This ensures that existing query parameter values in `requestUrl`
     * do not get overwritten. On the other hand when `requestUrl` is not absolute path, it
     * is still being built so there is nothing to overwrite.
     */
    requestUrl = appendQueryParams(requestUrl, queryParams, sequenceParams, isAbsolutePath);
    return requestUrl;
}
function replaceAll(input, replacements) {
    let result = input;
    for (const [searchValue, replaceValue] of replacements) {
        result = result.split(searchValue).join(replaceValue);
    }
    return result;
}
function calculateUrlReplacements(operationSpec, operationArguments, fallbackObject) {
    const result = new Map();
    if (operationSpec.urlParameters?.length) {
        for (const urlParameter of operationSpec.urlParameters) {
            let urlParameterValue = getOperationArgumentValueFromParameter(operationArguments, urlParameter, fallbackObject);
            const parameterPathString = getPathStringFromParameter(urlParameter);
            urlParameterValue = operationSpec.serializer.serialize(urlParameter.mapper, urlParameterValue, parameterPathString);
            if (!urlParameter.skipEncoding) {
                urlParameterValue = encodeURIComponent(urlParameterValue);
            }
            result.set(`{${urlParameter.mapper.serializedName || parameterPathString}}`, urlParameterValue);
        }
    }
    return result;
}
function isAbsoluteUrl(url) {
    return url.includes("://");
}
function appendPath(url, pathToAppend) {
    if (!pathToAppend) {
        return url;
    }
    const parsedUrl = new URL(url);
    let newPath = parsedUrl.pathname;
    if (!newPath.endsWith("/")) {
        newPath = `${newPath}/`;
    }
    if (pathToAppend.startsWith("/")) {
        pathToAppend = pathToAppend.substring(1);
    }
    const searchStart = pathToAppend.indexOf("?");
    if (searchStart !== -1) {
        const path = pathToAppend.substring(0, searchStart);
        const search = pathToAppend.substring(searchStart + 1);
        newPath = newPath + path;
        if (search) {
            parsedUrl.search = parsedUrl.search ? `${parsedUrl.search}&${search}` : search;
        }
    }
    else {
        newPath = newPath + pathToAppend;
    }
    parsedUrl.pathname = newPath;
    return parsedUrl.toString();
}
function calculateQueryParameters(operationSpec, operationArguments, fallbackObject) {
    const result = new Map();
    const sequenceParams = new Set();
    if (operationSpec.queryParameters?.length) {
        for (const queryParameter of operationSpec.queryParameters) {
            if (queryParameter.mapper.type.name === "Sequence" && queryParameter.mapper.serializedName) {
                sequenceParams.add(queryParameter.mapper.serializedName);
            }
            let queryParameterValue = getOperationArgumentValueFromParameter(operationArguments, queryParameter, fallbackObject);
            if ((queryParameterValue !== undefined && queryParameterValue !== null) ||
                queryParameter.mapper.required) {
                queryParameterValue = operationSpec.serializer.serialize(queryParameter.mapper, queryParameterValue, getPathStringFromParameter(queryParameter));
                const delimiter = queryParameter.collectionFormat
                    ? CollectionFormatToDelimiterMap[queryParameter.collectionFormat]
                    : "";
                if (Array.isArray(queryParameterValue)) {
                    // replace null and undefined
                    queryParameterValue = queryParameterValue.map((item) => {
                        if (item === null || item === undefined) {
                            return "";
                        }
                        return item;
                    });
                }
                if (queryParameter.collectionFormat === "Multi" && queryParameterValue.length === 0) {
                    continue;
                }
                else if (Array.isArray(queryParameterValue) &&
                    (queryParameter.collectionFormat === "SSV" || queryParameter.collectionFormat === "TSV")) {
                    queryParameterValue = queryParameterValue.join(delimiter);
                }
                if (!queryParameter.skipEncoding) {
                    if (Array.isArray(queryParameterValue)) {
                        queryParameterValue = queryParameterValue.map((item) => {
                            return encodeURIComponent(item);
                        });
                    }
                    else {
                        queryParameterValue = encodeURIComponent(queryParameterValue);
                    }
                }
                // Join pipes and CSV *after* encoding, or the server will be upset.
                if (Array.isArray(queryParameterValue) &&
                    (queryParameter.collectionFormat === "CSV" || queryParameter.collectionFormat === "Pipes")) {
                    queryParameterValue = queryParameterValue.join(delimiter);
                }
                result.set(queryParameter.mapper.serializedName || getPathStringFromParameter(queryParameter), queryParameterValue);
            }
        }
    }
    return {
        queryParams: result,
        sequenceParams,
    };
}
function simpleParseQueryParams(queryString) {
    const result = new Map();
    if (!queryString || queryString[0] !== "?") {
        return result;
    }
    // remove the leading ?
    queryString = queryString.slice(1);
    const pairs = queryString.split("&");
    for (const pair of pairs) {
        const [name, value] = pair.split("=", 2);
        const existingValue = result.get(name);
        if (existingValue) {
            if (Array.isArray(existingValue)) {
                existingValue.push(value);
            }
            else {
                result.set(name, [existingValue, value]);
            }
        }
        else {
            result.set(name, value);
        }
    }
    return result;
}
/** @internal */
function appendQueryParams(url, queryParams, sequenceParams, noOverwrite = false) {
    if (queryParams.size === 0) {
        return url;
    }
    const parsedUrl = new URL(url);
    // QUIRK: parsedUrl.searchParams will have their name/value pairs decoded, which
    // can change their meaning to the server, such as in the case of a SAS signature.
    // To avoid accidentally un-encoding a query param, we parse the key/values ourselves
    const combinedParams = simpleParseQueryParams(parsedUrl.search);
    for (const [name, value] of queryParams) {
        const existingValue = combinedParams.get(name);
        if (Array.isArray(existingValue)) {
            if (Array.isArray(value)) {
                existingValue.push(...value);
                const valueSet = new Set(existingValue);
                combinedParams.set(name, Array.from(valueSet));
            }
            else {
                existingValue.push(value);
            }
        }
        else if (existingValue) {
            if (Array.isArray(value)) {
                value.unshift(existingValue);
            }
            else if (sequenceParams.has(name)) {
                combinedParams.set(name, [existingValue, value]);
            }
            if (!noOverwrite) {
                combinedParams.set(name, value);
            }
        }
        else {
            combinedParams.set(name, value);
        }
    }
    const searchPieces = [];
    for (const [name, value] of combinedParams) {
        if (typeof value === "string") {
            searchPieces.push(`${name}=${value}`);
        }
        else if (Array.isArray(value)) {
            // QUIRK: If we get an array of values, include multiple key/value pairs
            for (const subValue of value) {
                searchPieces.push(`${name}=${subValue}`);
            }
        }
        else {
            searchPieces.push(`${name}=${value}`);
        }
    }
    // QUIRK: we have to set search manually as searchParams will encode comma when it shouldn't.
    parsedUrl.search = searchPieces.length ? `?${searchPieces.join("&")}` : "";
    return parsedUrl.toString();
}
//# sourceMappingURL=urlHelpers.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/log.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const dist_esm_log_logger = esm_createClientLogger("core-client");
//# sourceMappingURL=log.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/serviceClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.








/**
 * Initializes a new instance of the ServiceClient.
 */
class ServiceClient {
    /**
     * If specified, this is the base URI that requests will be made against for this ServiceClient.
     * If it is not specified, then all OperationSpecs must contain a baseUrl property.
     */
    _endpoint;
    /**
     * The default request content type for the service.
     * Used if no requestContentType is present on an OperationSpec.
     */
    _requestContentType;
    /**
     * Set to true if the request is sent over HTTP instead of HTTPS
     */
    _allowInsecureConnection;
    /**
     * The HTTP client that will be used to send requests.
     */
    _httpClient;
    /**
     * The pipeline used by this client to make requests
     */
    pipeline;
    /**
     * The ServiceClient constructor
     * @param options - The service client options that govern the behavior of the client.
     */
    constructor(options = {}) {
        this._requestContentType = options.requestContentType;
        this._endpoint = options.endpoint ?? options.baseUri;
        if (options.baseUri) {
            dist_esm_log_logger.warning("The baseUri option for SDK Clients has been deprecated, please use endpoint instead.");
        }
        this._allowInsecureConnection = options.allowInsecureConnection;
        this._httpClient = options.httpClient || getCachedDefaultHttpClient();
        this.pipeline = options.pipeline || serviceClient_createDefaultPipeline(options);
        if (options.additionalPolicies?.length) {
            for (const { policy, position } of options.additionalPolicies) {
                // Sign happens after Retry and is commonly needed to occur
                // before policies that intercept post-retry.
                const afterPhase = position === "perRetry" ? "Sign" : undefined;
                this.pipeline.addPolicy(policy, {
                    afterPhase,
                });
            }
        }
    }
    /**
     * Send the provided httpRequest.
     */
    async sendRequest(request) {
        return this.pipeline.sendRequest(this._httpClient, request);
    }
    /**
     * Send an HTTP request that is populated using the provided OperationSpec.
     * @typeParam T - The typed result of the request, based on the OperationSpec.
     * @param operationArguments - The arguments that the HTTP request's templated values will be populated from.
     * @param operationSpec - The OperationSpec to use to populate the httpRequest.
     */
    async sendOperationRequest(operationArguments, operationSpec) {
        const endpoint = operationSpec.baseUrl || this._endpoint;
        if (!endpoint) {
            throw new Error("If operationSpec.baseUrl is not specified, then the ServiceClient must have a endpoint string property that contains the base URL to use.");
        }
        // Templatized URLs sometimes reference properties on the ServiceClient child class,
        // so we have to pass `this` below in order to search these properties if they're
        // not part of OperationArguments
        const url = getRequestUrl(endpoint, operationSpec, operationArguments, this);
        const request = esm_pipelineRequest_createPipelineRequest({
            url,
        });
        request.method = operationSpec.httpMethod;
        const operationInfo = getOperationRequestInfo(request);
        operationInfo.operationSpec = operationSpec;
        operationInfo.operationArguments = operationArguments;
        const contentType = operationSpec.contentType || this._requestContentType;
        if (contentType && operationSpec.requestBody) {
            request.headers.set("Content-Type", contentType);
        }
        const options = operationArguments.options;
        if (options) {
            const requestOptions = options.requestOptions;
            if (requestOptions) {
                if (requestOptions.timeout) {
                    request.timeout = requestOptions.timeout;
                }
                if (requestOptions.onUploadProgress) {
                    request.onUploadProgress = requestOptions.onUploadProgress;
                }
                if (requestOptions.onDownloadProgress) {
                    request.onDownloadProgress = requestOptions.onDownloadProgress;
                }
                if (requestOptions.shouldDeserialize !== undefined) {
                    operationInfo.shouldDeserialize = requestOptions.shouldDeserialize;
                }
                if (requestOptions.allowInsecureConnection) {
                    request.allowInsecureConnection = true;
                }
            }
            if (options.abortSignal) {
                request.abortSignal = options.abortSignal;
            }
            if (options.tracingOptions) {
                request.tracingOptions = options.tracingOptions;
            }
        }
        if (this._allowInsecureConnection) {
            request.allowInsecureConnection = true;
        }
        if (request.streamResponseStatusCodes === undefined) {
            request.streamResponseStatusCodes = getStreamingResponseStatusCodes(operationSpec);
        }
        try {
            const rawResponse = await this.sendRequest(request);
            const flatResponse = flattenResponse(rawResponse, operationSpec.responses[rawResponse.status]);
            if (options?.onResponse) {
                options.onResponse(rawResponse, flatResponse);
            }
            return flatResponse;
        }
        catch (error) {
            if (typeof error === "object" && error?.response) {
                const rawResponse = error.response;
                const flatResponse = flattenResponse(rawResponse, operationSpec.responses[error.statusCode] || operationSpec.responses["default"]);
                error.details = flatResponse;
                if (options?.onResponse) {
                    options.onResponse(rawResponse, flatResponse, error);
                }
            }
            throw error;
        }
    }
}
function serviceClient_createDefaultPipeline(options) {
    const credentialScopes = getCredentialScopes(options);
    const credentialOptions = options.credential && credentialScopes
        ? { credentialScopes, credential: options.credential }
        : undefined;
    return createClientPipeline({
        ...options,
        credentialOptions,
    });
}
function getCredentialScopes(options) {
    if (options.credentialScopes) {
        return options.credentialScopes;
    }
    if (options.endpoint) {
        return `${options.endpoint}/.default`;
    }
    if (options.baseUri) {
        return `${options.baseUri}/.default`;
    }
    if (options.credential && !options.credentialScopes) {
        throw new Error(`When using credentials, the ServiceClientOptions must contain either a endpoint or a credentialScopes. Unable to create a bearerTokenAuthenticationPolicy`);
    }
    return undefined;
}
//# sourceMappingURL=serviceClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/authorizeRequestOnClaimChallenge.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * Converts: `Bearer a="b", c="d", Bearer d="e", f="g"`.
 * Into: `[ { a: 'b', c: 'd' }, { d: 'e', f: 'g' } ]`.
 *
 * @internal
 */
function parseCAEChallenge(challenges) {
    const bearerChallenges = `, ${challenges.trim()}`.split(", Bearer ").filter((x) => x);
    return bearerChallenges.map((challenge) => {
        const challengeParts = `${challenge.trim()}, `.split('", ').filter((x) => x);
        const keyValuePairs = challengeParts.map((keyValue) => (([key, value]) => ({ [key]: value }))(keyValue.trim().split('="')));
        // Key-value pairs to plain object:
        return keyValuePairs.reduce((a, b) => ({ ...a, ...b }), {});
    });
}
/**
 * This function can be used as a callback for the `bearerTokenAuthenticationPolicy` of `@azure/core-rest-pipeline`, to support CAE challenges:
 * [Continuous Access Evaluation](https://learn.microsoft.com/azure/active-directory/conditional-access/concept-continuous-access-evaluation).
 *
 * Call the `bearerTokenAuthenticationPolicy` with the following options:
 *
 * ```ts snippet:AuthorizeRequestOnClaimChallenge
 * import { bearerTokenAuthenticationPolicy } from "@azure/core-rest-pipeline";
 * import { authorizeRequestOnClaimChallenge } from "@azure/core-client";
 *
 * const policy = bearerTokenAuthenticationPolicy({
 *   challengeCallbacks: {
 *     authorizeRequestOnChallenge: authorizeRequestOnClaimChallenge,
 *   },
 *   scopes: ["https://service/.default"],
 * });
 * ```
 *
 * Once provided, the `bearerTokenAuthenticationPolicy` policy will internally handle Continuous Access Evaluation (CAE) challenges.
 * When it can't complete a challenge it will return the 401 (unauthorized) response from ARM.
 *
 * Example challenge with claims:
 *
 * ```
 * Bearer authorization_uri="https://login.windows-ppe.net/", error="invalid_token",
 * error_description="User session has been revoked",
 * claims="eyJhY2Nlc3NfdG9rZW4iOnsibmJmIjp7ImVzc2VudGlhbCI6dHJ1ZSwgInZhbHVlIjoiMTYwMzc0MjgwMCJ9fX0="
 * ```
 */
async function authorizeRequestOnClaimChallenge(onChallengeOptions) {
    const { scopes, response } = onChallengeOptions;
    const logger = onChallengeOptions.logger || coreClientLogger;
    const challenge = response.headers.get("WWW-Authenticate");
    if (!challenge) {
        logger.info(`The WWW-Authenticate header was missing. Failed to perform the Continuous Access Evaluation authentication flow.`);
        return false;
    }
    const challenges = parseCAEChallenge(challenge) || [];
    const parsedChallenge = challenges.find((x) => x.claims);
    if (!parsedChallenge) {
        logger.info(`The WWW-Authenticate header was missing the necessary "claims" to perform the Continuous Access Evaluation authentication flow.`);
        return false;
    }
    const accessToken = await onChallengeOptions.getAccessToken(parsedChallenge.scope ? [parsedChallenge.scope] : scopes, {
        claims: decodeStringToString(parsedChallenge.claims),
    });
    if (!accessToken) {
        return false;
    }
    onChallengeOptions.request.headers.set("Authorization", `${accessToken.tokenType ?? "Bearer"} ${accessToken.token}`);
    return true;
}
//# sourceMappingURL=authorizeRequestOnClaimChallenge.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/authorizeRequestOnTenantChallenge.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * A set of constants used internally when processing requests.
 */
const Constants = {
    DefaultScope: "/.default",
    /**
     * Defines constants for use with HTTP headers.
     */
    HeaderConstants: {
        /**
         * The Authorization header.
         */
        AUTHORIZATION: "authorization",
    },
};
function isUuid(text) {
    return /^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$/.test(text);
}
/**
 * Defines a callback to handle auth challenge for Storage APIs.
 * This implements the bearer challenge process described here: https://learn.microsoft.com/rest/api/storageservices/authorize-with-azure-active-directory#bearer-challenge
 * Handling has specific features for storage that departs to the general AAD challenge docs.
 **/
const authorizeRequestOnTenantChallenge = async (challengeOptions) => {
    const requestOptions = requestToOptions(challengeOptions.request);
    const challenge = getChallenge(challengeOptions.response);
    if (challenge) {
        const challengeInfo = parseChallenge(challenge);
        const challengeScopes = buildScopes(challengeOptions, challengeInfo);
        const tenantId = extractTenantId(challengeInfo);
        if (!tenantId) {
            return false;
        }
        const accessToken = await challengeOptions.getAccessToken(challengeScopes, {
            ...requestOptions,
            tenantId,
        });
        if (!accessToken) {
            return false;
        }
        challengeOptions.request.headers.set(Constants.HeaderConstants.AUTHORIZATION, `${accessToken.tokenType ?? "Bearer"} ${accessToken.token}`);
        return true;
    }
    return false;
};
/**
 * Extracts the tenant id from the challenge information
 * The tenant id is contained in the authorization_uri as the first
 * path part.
 */
function extractTenantId(challengeInfo) {
    const parsedAuthUri = new URL(challengeInfo.authorization_uri);
    const pathSegments = parsedAuthUri.pathname.split("/");
    const tenantId = pathSegments[1];
    if (tenantId && isUuid(tenantId)) {
        return tenantId;
    }
    return undefined;
}
/**
 * Builds the authentication scopes based on the information that comes in the
 * challenge information. Scopes url is present in the resource_id, if it is empty
 * we keep using the original scopes.
 */
function buildScopes(challengeOptions, challengeInfo) {
    if (!challengeInfo.resource_id) {
        return challengeOptions.scopes;
    }
    const challengeScopes = new URL(challengeInfo.resource_id);
    challengeScopes.pathname = Constants.DefaultScope;
    let scope = challengeScopes.toString();
    if (scope === "https://disk.azure.com/.default") {
        // the extra slash is required by the service
        scope = "https://disk.azure.com//.default";
    }
    return [scope];
}
/**
 * We will retrieve the challenge only if the response status code was 401,
 * and if the response contained the header "WWW-Authenticate" with a non-empty value.
 */
function getChallenge(response) {
    const challenge = response.headers.get("WWW-Authenticate");
    if (response.status === 401 && challenge) {
        return challenge;
    }
    return;
}
/**
 * Converts: `Bearer a="b" c="d"`.
 * Into: `[ { a: 'b', c: 'd' }]`.
 *
 * @internal
 */
function parseChallenge(challenge) {
    const bearerChallenge = challenge.slice("Bearer ".length);
    const challengeParts = `${bearerChallenge.trim()} `.split(" ").filter((x) => x);
    const keyValuePairs = challengeParts.map((keyValue) => (([key, value]) => ({ [key]: value }))(keyValue.trim().split("=")));
    // Key-value pairs to plain object:
    return keyValuePairs.reduce((a, b) => ({ ...a, ...b }), {});
}
/**
 * Extracts the options form a Pipeline Request for later re-use
 */
function requestToOptions(request) {
    return {
        abortSignal: request.abortSignal,
        requestOptions: {
            timeout: request.timeout,
        },
        tracingOptions: request.tracingOptions,
    };
}
//# sourceMappingURL=authorizeRequestOnTenantChallenge.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-client/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.








//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-http-compat/dist/esm/util.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

// We use a custom symbol to cache a reference to the original request without
// exposing it on the public interface.
const util_originalRequestSymbol = Symbol("Original PipelineRequest");
// Symbol.for() will return the same symbol if it's already been created
// This particular one is used in core-client to handle the case of when a request is
// cloned but we need to retrieve the OperationSpec and OperationArguments from the
// original request.
const originalClientRequestSymbol = Symbol.for("@azure/core-client original request");
function toPipelineRequest(webResource, options = {}) {
    const compatWebResource = webResource;
    const request = compatWebResource[util_originalRequestSymbol];
    const headers = esm_httpHeaders_createHttpHeaders(webResource.headers.toJson({ preserveCase: true }));
    if (request) {
        request.headers = headers;
        return request;
    }
    else {
        const newRequest = esm_pipelineRequest_createPipelineRequest({
            url: webResource.url,
            method: webResource.method,
            headers,
            withCredentials: webResource.withCredentials,
            timeout: webResource.timeout,
            requestId: webResource.requestId,
            abortSignal: webResource.abortSignal,
            body: webResource.body,
            formData: webResource.formData,
            disableKeepAlive: !!webResource.keepAlive,
            onDownloadProgress: webResource.onDownloadProgress,
            onUploadProgress: webResource.onUploadProgress,
            proxySettings: webResource.proxySettings,
            streamResponseStatusCodes: webResource.streamResponseStatusCodes,
            agent: webResource.agent,
            requestOverrides: webResource.requestOverrides,
        });
        if (options.originalRequest) {
            newRequest[originalClientRequestSymbol] =
                options.originalRequest;
        }
        return newRequest;
    }
}
function toWebResourceLike(request, options) {
    const originalRequest = options?.originalRequest ?? request;
    const webResource = {
        url: request.url,
        method: request.method,
        headers: toHttpHeadersLike(request.headers),
        withCredentials: request.withCredentials,
        timeout: request.timeout,
        requestId: request.headers.get("x-ms-client-request-id") || request.requestId,
        abortSignal: request.abortSignal,
        body: request.body,
        formData: request.formData,
        keepAlive: !!request.disableKeepAlive,
        onDownloadProgress: request.onDownloadProgress,
        onUploadProgress: request.onUploadProgress,
        proxySettings: request.proxySettings,
        streamResponseStatusCodes: request.streamResponseStatusCodes,
        agent: request.agent,
        requestOverrides: request.requestOverrides,
        clone() {
            throw new Error("Cannot clone a non-proxied WebResourceLike");
        },
        prepare() {
            throw new Error("WebResourceLike.prepare() is not supported by @azure/core-http-compat");
        },
        validateRequestProperties() {
            /** do nothing */
        },
    };
    if (options?.createProxy) {
        return new Proxy(webResource, {
            get(target, prop, receiver) {
                if (prop === util_originalRequestSymbol) {
                    return request;
                }
                else if (prop === "clone") {
                    return () => {
                        return toWebResourceLike(toPipelineRequest(webResource, { originalRequest }), {
                            createProxy: true,
                            originalRequest,
                        });
                    };
                }
                return Reflect.get(target, prop, receiver);
            },
            set(target, prop, value, receiver) {
                if (prop === "keepAlive") {
                    request.disableKeepAlive = !value;
                }
                const passThroughProps = [
                    "url",
                    "method",
                    "withCredentials",
                    "timeout",
                    "requestId",
                    "abortSignal",
                    "body",
                    "formData",
                    "onDownloadProgress",
                    "onUploadProgress",
                    "proxySettings",
                    "streamResponseStatusCodes",
                    "agent",
                    "requestOverrides",
                ];
                if (typeof prop === "string" && passThroughProps.includes(prop)) {
                    request[prop] = value;
                }
                return Reflect.set(target, prop, value, receiver);
            },
        });
    }
    else {
        return webResource;
    }
}
/**
 * Converts HttpHeaders from core-rest-pipeline to look like
 * HttpHeaders from core-http.
 * @param headers - HttpHeaders from core-rest-pipeline
 * @returns HttpHeaders as they looked in core-http
 */
function toHttpHeadersLike(headers) {
    return new HttpHeaders(headers.toJSON({ preserveCase: true }));
}
/**
 * A collection of HttpHeaders that can be sent with a HTTP request.
 */
function getHeaderKey(headerName) {
    return headerName.toLowerCase();
}
/**
 * A collection of HTTP header key/value pairs.
 */
class HttpHeaders {
    _headersMap;
    constructor(rawHeaders) {
        this._headersMap = {};
        if (rawHeaders) {
            for (const headerName in rawHeaders) {
                this.set(headerName, rawHeaders[headerName]);
            }
        }
    }
    /**
     * Set a header in this collection with the provided name and value. The name is
     * case-insensitive.
     * @param headerName - The name of the header to set. This value is case-insensitive.
     * @param headerValue - The value of the header to set.
     */
    set(headerName, headerValue) {
        this._headersMap[getHeaderKey(headerName)] = {
            name: headerName,
            value: headerValue.toString(),
        };
    }
    /**
     * Get the header value for the provided header name, or undefined if no header exists in this
     * collection with the provided name.
     * @param headerName - The name of the header.
     */
    get(headerName) {
        const header = this._headersMap[getHeaderKey(headerName)];
        return !header ? undefined : header.value;
    }
    /**
     * Get whether or not this header collection contains a header entry for the provided header name.
     */
    contains(headerName) {
        return !!this._headersMap[getHeaderKey(headerName)];
    }
    /**
     * Remove the header with the provided headerName. Return whether or not the header existed and
     * was removed.
     * @param headerName - The name of the header to remove.
     */
    remove(headerName) {
        const result = this.contains(headerName);
        delete this._headersMap[getHeaderKey(headerName)];
        return result;
    }
    /**
     * Get the headers that are contained this collection as an object.
     */
    rawHeaders() {
        return this.toJson({ preserveCase: true });
    }
    /**
     * Get the headers that are contained in this collection as an array.
     */
    headersArray() {
        const headers = [];
        for (const headerKey in this._headersMap) {
            headers.push(this._headersMap[headerKey]);
        }
        return headers;
    }
    /**
     * Get the header names that are contained in this collection.
     */
    headerNames() {
        const headerNames = [];
        const headers = this.headersArray();
        for (let i = 0; i < headers.length; ++i) {
            headerNames.push(headers[i].name);
        }
        return headerNames;
    }
    /**
     * Get the header values that are contained in this collection.
     */
    headerValues() {
        const headerValues = [];
        const headers = this.headersArray();
        for (let i = 0; i < headers.length; ++i) {
            headerValues.push(headers[i].value);
        }
        return headerValues;
    }
    /**
     * Get the JSON object representation of this HTTP header collection.
     */
    toJson(options = {}) {
        const result = {};
        if (options.preserveCase) {
            for (const headerKey in this._headersMap) {
                const header = this._headersMap[headerKey];
                result[header.name] = header.value;
            }
        }
        else {
            for (const headerKey in this._headersMap) {
                const header = this._headersMap[headerKey];
                result[getHeaderKey(header.name)] = header.value;
            }
        }
        return result;
    }
    /**
     * Get the string representation of this HTTP header collection.
     */
    toString() {
        return JSON.stringify(this.toJson({ preserveCase: true }));
    }
    /**
     * Create a deep clone/copy of this HttpHeaders collection.
     */
    clone() {
        const resultPreservingCasing = {};
        for (const headerKey in this._headersMap) {
            const header = this._headersMap[headerKey];
            resultPreservingCasing[header.name] = header.value;
        }
        return new HttpHeaders(resultPreservingCasing);
    }
}
//# sourceMappingURL=util.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-http-compat/dist/esm/response.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


const originalResponse = Symbol("Original FullOperationResponse");
/**
 * A helper to convert response objects from the new pipeline back to the old one.
 * @param response - A response object from core-client.
 * @returns A response compatible with `HttpOperationResponse` from core-http.
 */
function toCompatResponse(response, options) {
    let request = toWebResourceLike(response.request);
    let headers = toHttpHeadersLike(response.headers);
    if (options?.createProxy) {
        return new Proxy(response, {
            get(target, prop, receiver) {
                if (prop === "headers") {
                    return headers;
                }
                else if (prop === "request") {
                    return request;
                }
                else if (prop === originalResponse) {
                    return response;
                }
                return Reflect.get(target, prop, receiver);
            },
            set(target, prop, value, receiver) {
                if (prop === "headers") {
                    headers = value;
                }
                else if (prop === "request") {
                    request = value;
                }
                return Reflect.set(target, prop, value, receiver);
            },
        });
    }
    else {
        return {
            ...response,
            request,
            headers,
        };
    }
}
/**
 * A helper to convert back to a PipelineResponse
 * @param compatResponse - A response compatible with `HttpOperationResponse` from core-http.
 */
function response_toPipelineResponse(compatResponse) {
    const extendedCompatResponse = compatResponse;
    const response = extendedCompatResponse[originalResponse];
    const headers = esm_httpHeaders_createHttpHeaders(compatResponse.headers.toJson({ preserveCase: true }));
    if (response) {
        response.headers = headers;
        return response;
    }
    else {
        return {
            ...compatResponse,
            headers,
            request: toPipelineRequest(compatResponse.request),
        };
    }
}
//# sourceMappingURL=response.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-http-compat/dist/esm/extendedClient.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.




/**
 * Client to provide compatability between core V1 & V2.
 */
class ExtendedServiceClient extends ServiceClient {
    constructor(options) {
        super(options);
        if (options.keepAliveOptions?.enable === false &&
            !pipelineContainsDisableKeepAlivePolicy(this.pipeline)) {
            this.pipeline.addPolicy(createDisableKeepAlivePolicy());
        }
        if (options.redirectOptions?.handleRedirects === false) {
            this.pipeline.removePolicy({
                name: redirectPolicy_redirectPolicyName,
            });
        }
    }
    /**
     * Compatible send operation request function.
     *
     * @param operationArguments - Operation arguments
     * @param operationSpec - Operation Spec
     * @returns
     */
    async sendOperationRequest(operationArguments, operationSpec) {
        const userProvidedCallBack = operationArguments?.options?.onResponse;
        let lastResponse;
        function onResponse(rawResponse, flatResponse, error) {
            lastResponse = rawResponse;
            if (userProvidedCallBack) {
                userProvidedCallBack(rawResponse, flatResponse, error);
            }
        }
        operationArguments.options = {
            ...operationArguments.options,
            onResponse,
        };
        const result = await super.sendOperationRequest(operationArguments, operationSpec);
        if (lastResponse) {
            Object.defineProperty(result, "_response", {
                value: toCompatResponse(lastResponse),
            });
        }
        return result;
    }
}
//# sourceMappingURL=extendedClient.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-http-compat/dist/esm/policies/requestPolicyFactoryPolicy.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * An enum for compatibility with RequestPolicy
 */
var HttpPipelineLogLevel;
(function (HttpPipelineLogLevel) {
    HttpPipelineLogLevel[HttpPipelineLogLevel["ERROR"] = 1] = "ERROR";
    HttpPipelineLogLevel[HttpPipelineLogLevel["INFO"] = 3] = "INFO";
    HttpPipelineLogLevel[HttpPipelineLogLevel["OFF"] = 0] = "OFF";
    HttpPipelineLogLevel[HttpPipelineLogLevel["WARNING"] = 2] = "WARNING";
})(HttpPipelineLogLevel || (HttpPipelineLogLevel = {}));
const mockRequestPolicyOptions = {
    log(_logLevel, _message) {
        /* do nothing */
    },
    shouldLog(_logLevel) {
        return false;
    },
};
/**
 * The name of the RequestPolicyFactoryPolicy
 */
const requestPolicyFactoryPolicyName = "RequestPolicyFactoryPolicy";
/**
 * A policy that wraps policies written for core-http.
 * @param factories - An array of `RequestPolicyFactory` objects from a core-http pipeline
 */
function createRequestPolicyFactoryPolicy(factories) {
    const orderedFactories = factories.slice().reverse();
    return {
        name: requestPolicyFactoryPolicyName,
        async sendRequest(request, next) {
            let httpPipeline = {
                async sendRequest(httpRequest) {
                    const response = await next(toPipelineRequest(httpRequest));
                    return toCompatResponse(response, { createProxy: true });
                },
            };
            for (const factory of orderedFactories) {
                httpPipeline = factory.create(httpPipeline, mockRequestPolicyOptions);
            }
            const webResourceLike = toWebResourceLike(request, { createProxy: true });
            const response = await httpPipeline.sendRequest(webResourceLike);
            return response_toPipelineResponse(response);
        },
    };
}
//# sourceMappingURL=requestPolicyFactoryPolicy.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-http-compat/dist/esm/httpClientAdapter.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.


/**
 * Converts a RequestPolicy based HttpClient to a PipelineRequest based HttpClient.
 * @param requestPolicyClient - A HttpClient compatible with core-http
 * @returns A HttpClient compatible with core-rest-pipeline
 */
function convertHttpClient(requestPolicyClient) {
    return {
        sendRequest: async (request) => {
            const response = await requestPolicyClient.sendRequest(toWebResourceLike(request, { createProxy: true }));
            return response_toPipelineResponse(response);
        },
    };
}
//# sourceMappingURL=httpClientAdapter.js.map
;// CONCATENATED MODULE: ./node_modules/@azure/core-http-compat/dist/esm/index.js
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
/**
 * A Shim Library that provides compatibility between Core V1 & V2 Packages.
 *
 * @packageDocumentation
 */





//# sourceMappingURL=index.js.map
;// CONCATENATED MODULE: ./node_modules/fast-xml-builder/src/orderedJs2Xml.js
const EOL = "\n";

/**
 * 
 * @param {array} jArray 
 * @param {any} options 
 * @returns 
 */
function toXml(jArray, options) {
    let indentation = "";
    if (options.format && options.indentBy.length > 0) {
        indentation = EOL;
    }
    return arrToStr(jArray, options, "", indentation);
}

function arrToStr(arr, options, jPath, indentation) {
    let xmlStr = "";
    let isPreviousElementTag = false;


    if (!Array.isArray(arr)) {
        // Non-array values (e.g. string tag values) should be treated as text content
        if (arr !== undefined && arr !== null) {
            let text = arr.toString();
            text = replaceEntitiesValue(text, options);
            return text;
        }
        return "";
    }

    for (let i = 0; i < arr.length; i++) {
        const tagObj = arr[i];
        const tagName = propName(tagObj);
        if (tagName === undefined) continue;

        let newJPath = "";
        if (jPath.length === 0) newJPath = tagName
        else newJPath = `${jPath}.${tagName}`;

        if (tagName === options.textNodeName) {
            let tagText = tagObj[tagName];
            if (!isStopNode(newJPath, options)) {
                tagText = options.tagValueProcessor(tagName, tagText);
                tagText = replaceEntitiesValue(tagText, options);
            }
            if (isPreviousElementTag) {
                xmlStr += indentation;
            }
            xmlStr += tagText;
            isPreviousElementTag = false;
            continue;
        } else if (tagName === options.cdataPropName) {
            if (isPreviousElementTag) {
                xmlStr += indentation;
            }
            xmlStr += `<![CDATA[${tagObj[tagName][0][options.textNodeName]}]]>`;
            isPreviousElementTag = false;
            continue;
        } else if (tagName === options.commentPropName) {
            xmlStr += indentation + `<!--${tagObj[tagName][0][options.textNodeName]}-->`;
            isPreviousElementTag = true;
            continue;
        } else if (tagName[0] === "?") {
            const attStr = attr_to_str(tagObj[":@"], options);
            const tempInd = tagName === "?xml" ? "" : indentation;
            let piTextNodeName = tagObj[tagName][0][options.textNodeName];
            piTextNodeName = piTextNodeName.length !== 0 ? " " + piTextNodeName : ""; //remove extra spacing
            xmlStr += tempInd + `<${tagName}${piTextNodeName}${attStr}?>`;
            isPreviousElementTag = true;
            continue;
        }
        let newIdentation = indentation;
        if (newIdentation !== "") {
            newIdentation += options.indentBy;
        }
        const attStr = attr_to_str(tagObj[":@"], options);
        const tagStart = indentation + `<${tagName}${attStr}`;
        const tagValue = arrToStr(tagObj[tagName], options, newJPath, newIdentation);
        if (options.unpairedTags.indexOf(tagName) !== -1) {
            if (options.suppressUnpairedNode) xmlStr += tagStart + ">";
            else xmlStr += tagStart + "/>";
        } else if ((!tagValue || tagValue.length === 0) && options.suppressEmptyNode) {
            xmlStr += tagStart + "/>";
        } else if (tagValue && tagValue.endsWith(">")) {
            xmlStr += tagStart + `>${tagValue}${indentation}</${tagName}>`;
        } else {
            xmlStr += tagStart + ">";
            if (tagValue && indentation !== "" && (tagValue.includes("/>") || tagValue.includes("</"))) {
                xmlStr += indentation + options.indentBy + tagValue + indentation;
            } else {
                xmlStr += tagValue;
            }
            xmlStr += `</${tagName}>`;
        }
        isPreviousElementTag = true;
    }

    return xmlStr;
}

function propName(obj) {
    const keys = Object.keys(obj);
    for (let i = 0; i < keys.length; i++) {
        const key = keys[i];
        if (!Object.prototype.hasOwnProperty.call(obj, key)) continue;
        if (key !== ":@") return key;
    }
}

function attr_to_str(attrMap, options) {
    let attrStr = "";
    if (attrMap && !options.ignoreAttributes) {
        for (let attr in attrMap) {
            if (!Object.prototype.hasOwnProperty.call(attrMap, attr)) continue;
            let attrVal = options.attributeValueProcessor(attr, attrMap[attr]);
            attrVal = replaceEntitiesValue(attrVal, options);
            if (attrVal === true && options.suppressBooleanAttributes) {
                attrStr += ` ${attr.substr(options.attributeNamePrefix.length)}`;
            } else {
                attrStr += ` ${attr.substr(options.attributeNamePrefix.length)}="${attrVal}"`;
            }
        }
    }
    return attrStr;
}

function isStopNode(jPath, options) {
    jPath = jPath.substr(0, jPath.length - options.textNodeName.length - 1);
    let tagName = jPath.substr(jPath.lastIndexOf(".") + 1);
    for (let index in options.stopNodes) {
        if (options.stopNodes[index] === jPath || options.stopNodes[index] === "*." + tagName) return true;
    }
    return false;
}

function replaceEntitiesValue(textValue, options) {
    if (textValue && textValue.length > 0 && options.processEntities) {
        for (let i = 0; i < options.entities.length; i++) {
            const entity = options.entities[i];
            textValue = textValue.replace(entity.regex, entity.val);
        }
    }
    return textValue;
}

;// CONCATENATED MODULE: ./node_modules/fast-xml-builder/src/ignoreAttributes.js
function getIgnoreAttributesFn(ignoreAttributes) {
    if (typeof ignoreAttributes === 'function') {
        return ignoreAttributes
    }
    if (Array.isArray(ignoreAttributes)) {
        return (attrName) => {
            for (const pattern of ignoreAttributes) {
                if (typeof pattern === 'string' && attrName === pattern) {
                    return true
                }
                if (pattern instanceof RegExp && pattern.test(attrName)) {
                    return true
                }
            }
        }
    }
    return () => false
}
;// CONCATENATED MODULE: ./node_modules/fast-xml-builder/src/fxb.js

//parse Empty Node as self closing node



const defaultOptions = {
  attributeNamePrefix: '@_',
  attributesGroupName: false,
  textNodeName: '#text',
  ignoreAttributes: true,
  cdataPropName: false,
  format: false,
  indentBy: '  ',
  suppressEmptyNode: false,
  suppressUnpairedNode: true,
  suppressBooleanAttributes: true,
  tagValueProcessor: function (key, a) {
    return a;
  },
  attributeValueProcessor: function (attrName, a) {
    return a;
  },
  preserveOrder: false,
  commentPropName: false,
  unpairedTags: [],
  entities: [
    { regex: new RegExp("&", "g"), val: "&amp;" },//it must be on top
    { regex: new RegExp(">", "g"), val: "&gt;" },
    { regex: new RegExp("<", "g"), val: "&lt;" },
    { regex: new RegExp("\'", "g"), val: "&apos;" },
    { regex: new RegExp("\"", "g"), val: "&quot;" }
  ],
  processEntities: true,
  stopNodes: [],
  // transformTagName: false,
  // transformAttributeName: false,
  oneListGroup: false
};

function Builder(options) {
  this.options = Object.assign({}, defaultOptions, options);
  if (this.options.ignoreAttributes === true || this.options.attributesGroupName) {
    this.isAttribute = function (/*a*/) {
      return false;
    };
  } else {
    this.ignoreAttributesFn = getIgnoreAttributesFn(this.options.ignoreAttributes)
    this.attrPrefixLen = this.options.attributeNamePrefix.length;
    this.isAttribute = isAttribute;
  }

  this.processTextOrObjNode = processTextOrObjNode

  if (this.options.format) {
    this.indentate = indentate;
    this.tagEndChar = '>\n';
    this.newLine = '\n';
  } else {
    this.indentate = function () {
      return '';
    };
    this.tagEndChar = '>';
    this.newLine = '';
  }
}

Builder.prototype.build = function (jObj) {
  if (this.options.preserveOrder) {
    return toXml(jObj, this.options);
  } else {
    if (Array.isArray(jObj) && this.options.arrayNodeName && this.options.arrayNodeName.length > 1) {
      jObj = {
        [this.options.arrayNodeName]: jObj
      }
    }
    return this.j2x(jObj, 0, []).val;
  }
};

Builder.prototype.j2x = function (jObj, level, ajPath) {
  let attrStr = '';
  let val = '';
  const jPath = ajPath.join('.')
  for (let key in jObj) {
    if (!Object.prototype.hasOwnProperty.call(jObj, key)) continue;
    if (typeof jObj[key] === 'undefined') {
      // supress undefined node only if it is not an attribute
      if (this.isAttribute(key)) {
        val += '';
      }
    } else if (jObj[key] === null) {
      // null attribute should be ignored by the attribute list, but should not cause the tag closing
      if (this.isAttribute(key)) {
        val += '';
      } else if (key === this.options.cdataPropName) {
        val += '';
      } else if (key[0] === '?') {
        val += this.indentate(level) + '<' + key + '?' + this.tagEndChar;
      } else {
        val += this.indentate(level) + '<' + key + '/' + this.tagEndChar;
      }
      // val += this.indentate(level) + '<' + key + '/' + this.tagEndChar;
    } else if (jObj[key] instanceof Date) {
      val += this.buildTextValNode(jObj[key], key, '', level);
    } else if (typeof jObj[key] !== 'object') {
      //premitive type
      const attr = this.isAttribute(key);
      if (attr && !this.ignoreAttributesFn(attr, jPath)) {
        attrStr += this.buildAttrPairStr(attr, '' + jObj[key]);
      } else if (!attr) {
        //tag value
        if (key === this.options.textNodeName) {
          let newval = this.options.tagValueProcessor(key, '' + jObj[key]);
          val += this.replaceEntitiesValue(newval);
        } else {
          val += this.buildTextValNode(jObj[key], key, '', level);
        }
      }
    } else if (Array.isArray(jObj[key])) {
      //repeated nodes
      const arrLen = jObj[key].length;
      let listTagVal = "";
      let listTagAttr = "";
      for (let j = 0; j < arrLen; j++) {
        const item = jObj[key][j];
        if (typeof item === 'undefined') {
          // supress undefined node
        } else if (item === null) {
          if (key[0] === "?") val += this.indentate(level) + '<' + key + '?' + this.tagEndChar;
          else val += this.indentate(level) + '<' + key + '/' + this.tagEndChar;
          // val += this.indentate(level) + '<' + key + '/' + this.tagEndChar;
        } else if (typeof item === 'object') {
          if (this.options.oneListGroup) {
            const result = this.j2x(item, level + 1, ajPath.concat(key));
            listTagVal += result.val;
            if (this.options.attributesGroupName && item.hasOwnProperty(this.options.attributesGroupName)) {
              listTagAttr += result.attrStr
            }
          } else {
            listTagVal += this.processTextOrObjNode(item, key, level, ajPath)
          }
        } else {
          if (this.options.oneListGroup) {
            let textValue = this.options.tagValueProcessor(key, item);
            textValue = this.replaceEntitiesValue(textValue);
            listTagVal += textValue;
          } else {
            listTagVal += this.buildTextValNode(item, key, '', level);
          }
        }
      }
      if (this.options.oneListGroup) {
        listTagVal = this.buildObjectNode(listTagVal, key, listTagAttr, level);
      }
      val += listTagVal;
    } else {
      //nested node
      if (this.options.attributesGroupName && key === this.options.attributesGroupName) {
        const Ks = Object.keys(jObj[key]);
        const L = Ks.length;
        for (let j = 0; j < L; j++) {
          attrStr += this.buildAttrPairStr(Ks[j], '' + jObj[key][Ks[j]]);
        }
      } else {
        val += this.processTextOrObjNode(jObj[key], key, level, ajPath)
      }
    }
  }
  return { attrStr: attrStr, val: val };
};

Builder.prototype.buildAttrPairStr = function (attrName, val) {
  val = this.options.attributeValueProcessor(attrName, '' + val);
  val = this.replaceEntitiesValue(val);
  if (this.options.suppressBooleanAttributes && val === "true") {
    return ' ' + attrName;
  } else return ' ' + attrName + '="' + val + '"';
}

function processTextOrObjNode(object, key, level, ajPath) {
  const result = this.j2x(object, level + 1, ajPath.concat(key));
  if (object[this.options.textNodeName] !== undefined && Object.keys(object).length === 1) {
    return this.buildTextValNode(object[this.options.textNodeName], key, result.attrStr, level);
  } else {
    return this.buildObjectNode(result.val, key, result.attrStr, level);
  }
}

Builder.prototype.buildObjectNode = function (val, key, attrStr, level) {
  if (val === "") {
    if (key[0] === "?") return this.indentate(level) + '<' + key + attrStr + '?' + this.tagEndChar;
    else {
      return this.indentate(level) + '<' + key + attrStr + this.closeTag(key) + this.tagEndChar;
    }
  } else {

    let tagEndExp = '</' + key + this.tagEndChar;
    let piClosingChar = "";

    if (key[0] === "?") {
      piClosingChar = "?";
      tagEndExp = "";
    }

    // attrStr is an empty string in case the attribute came as undefined or null
    if ((attrStr || attrStr === '') && val.indexOf('<') === -1) {
      return (this.indentate(level) + '<' + key + attrStr + piClosingChar + '>' + val + tagEndExp);
    } else if (this.options.commentPropName !== false && key === this.options.commentPropName && piClosingChar.length === 0) {
      return this.indentate(level) + `<!--${val}-->` + this.newLine;
    } else {
      return (
        this.indentate(level) + '<' + key + attrStr + piClosingChar + this.tagEndChar +
        val +
        this.indentate(level) + tagEndExp);
    }
  }
}

Builder.prototype.closeTag = function (key) {
  let closeTag = "";
  if (this.options.unpairedTags.indexOf(key) !== -1) { //unpaired
    if (!this.options.suppressUnpairedNode) closeTag = "/"
  } else if (this.options.suppressEmptyNode) { //empty
    closeTag = "/";
  } else {
    closeTag = `></${key}`
  }
  return closeTag;
}

function buildEmptyObjNode(val, key, attrStr, level) {
  if (val !== '') {
    return this.buildObjectNode(val, key, attrStr, level);
  } else {
    if (key[0] === "?") return this.indentate(level) + '<' + key + attrStr + '?' + this.tagEndChar;
    else {
      return this.indentate(level) + '<' + key + attrStr + '/' + this.tagEndChar;
      // return this.buildTagStr(level,key, attrStr);
    }
  }
}

Builder.prototype.buildTextValNode = function (val, key, attrStr, level) {
  if (this.options.cdataPropName !== false && key === this.options.cdataPropName) {
    return this.indentate(level) + `<![CDATA[${val}]]>` + this.newLine;
  } else if (this.options.commentPropName !== false && key === this.options.commentPropName) {
    return this.indentate(level) + `<!--${val}-->` + this.newLine;
  } else if (key[0] === "?") {//PI tag
    return this.indentate(level) + '<' + key + attrStr + '?' + this.tagEndChar;
  } else {
    let textValue = this.options.tagValueProcessor(key, val);
    textValue = this.replaceEntitiesValue(textValue);

    if (textValue === '') {
      return this.indentate(level) + '<' + key + attrStr + this.closeTag(key) + this.tagEndChar;
    } else {
      return this.indentate(level) + '<' + key + attrStr + '>' +
        textValue +
        '</' + key + this.tagEndChar;
    }
  }
}

Builder.prototype.replaceEntitiesValue = function (textValue) {
  if (textValue && textValue.length > 0 && this.options.processEntities) {
    for (let i = 0; i < this.options.entities.length; i++) {
      const entity = this.options.entities[i];
      textValue = textValue.replace(entity.regex, entity.val);
    }
  }
  return textValue;
}

function indentate(level) {
  return this.options.indentBy.repeat(level);
}

function isAttribute(name /*, options*/) {
  if (name.startsWith(this.options.attributeNamePrefix) && name !== this.options.textNodeName) {
    return name.substr(this.attrPrefixLen);
  } else {
    return false;
  }
}


;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/xmlbuilder/json2xml.js
// Re-export from fast-xml-builder for backward compatibility

/* harmony default export */ const json2xml = (Builder);

// If there are any named exports you also want to re-export:

;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/util.js


const nameStartChar = ':A-Za-z_\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD';
const nameChar = nameStartChar + '\\-.\\d\\u00B7\\u0300-\\u036F\\u203F-\\u2040';
const nameRegexp = '[' + nameStartChar + '][' + nameChar + ']*';
const regexName = new RegExp('^' + nameRegexp + '$');

function getAllMatches(string, regex) {
  const matches = [];
  let match = regex.exec(string);
  while (match) {
    const allmatches = [];
    allmatches.startIndex = regex.lastIndex - match[0].length;
    const len = match.length;
    for (let index = 0; index < len; index++) {
      allmatches.push(match[index]);
    }
    matches.push(allmatches);
    match = regex.exec(string);
  }
  return matches;
}

const isName = function (string) {
  const match = regexName.exec(string);
  return !(match === null || typeof match === 'undefined');
}

function isExist(v) {
  return typeof v !== 'undefined';
}

function isEmptyObject(obj) {
  return Object.keys(obj).length === 0;
}

function getValue(v) {
  if (exports.isExist(v)) {
    return v;
  } else {
    return '';
  }
}

;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/validator.js




const validator_defaultOptions = {
  allowBooleanAttributes: false, //A tag can have attributes without any value
  unpairedTags: []
};

//const tagsPattern = new RegExp("<\\/?([\\w:\\-_\.]+)\\s*\/?>","g");
function validate(xmlData, options) {
  options = Object.assign({}, validator_defaultOptions, options);

  //xmlData = xmlData.replace(/(\r\n|\n|\r)/gm,"");//make it single line
  //xmlData = xmlData.replace(/(^\s*<\?xml.*?\?>)/g,"");//Remove XML starting tag
  //xmlData = xmlData.replace(/(<!DOCTYPE[\s\w\"\.\/\-\:]+(\[.*\])*\s*>)/g,"");//Remove DOCTYPE
  const tags = [];
  let tagFound = false;

  //indicates that the root tag has been closed (aka. depth 0 has been reached)
  let reachedRoot = false;

  if (xmlData[0] === '\ufeff') {
    // check for byte order mark (BOM)
    xmlData = xmlData.substr(1);
  }

  for (let i = 0; i < xmlData.length; i++) {

    if (xmlData[i] === '<' && xmlData[i + 1] === '?') {
      i += 2;
      i = readPI(xmlData, i);
      if (i.err) return i;
    } else if (xmlData[i] === '<') {
      //starting of tag
      //read until you reach to '>' avoiding any '>' in attribute value
      let tagStartPos = i;
      i++;

      if (xmlData[i] === '!') {
        i = readCommentAndCDATA(xmlData, i);
        continue;
      } else {
        let closingTag = false;
        if (xmlData[i] === '/') {
          //closing tag
          closingTag = true;
          i++;
        }
        //read tagname
        let tagName = '';
        for (; i < xmlData.length &&
          xmlData[i] !== '>' &&
          xmlData[i] !== ' ' &&
          xmlData[i] !== '\t' &&
          xmlData[i] !== '\n' &&
          xmlData[i] !== '\r'; i++
        ) {
          tagName += xmlData[i];
        }
        tagName = tagName.trim();
        //console.log(tagName);

        if (tagName[tagName.length - 1] === '/') {
          //self closing tag without attributes
          tagName = tagName.substring(0, tagName.length - 1);
          //continue;
          i--;
        }
        if (!validateTagName(tagName)) {
          let msg;
          if (tagName.trim().length === 0) {
            msg = "Invalid space after '<'.";
          } else {
            msg = "Tag '" + tagName + "' is an invalid name.";
          }
          return getErrorObject('InvalidTag', msg, getLineNumberForPosition(xmlData, i));
        }

        const result = readAttributeStr(xmlData, i);
        if (result === false) {
          return getErrorObject('InvalidAttr', "Attributes for '" + tagName + "' have open quote.", getLineNumberForPosition(xmlData, i));
        }
        let attrStr = result.value;
        i = result.index;

        if (attrStr[attrStr.length - 1] === '/') {
          //self closing tag
          const attrStrStart = i - attrStr.length;
          attrStr = attrStr.substring(0, attrStr.length - 1);
          const isValid = validateAttributeString(attrStr, options);
          if (isValid === true) {
            tagFound = true;
            //continue; //text may presents after self closing tag
          } else {
            //the result from the nested function returns the position of the error within the attribute
            //in order to get the 'true' error line, we need to calculate the position where the attribute begins (i - attrStr.length) and then add the position within the attribute
            //this gives us the absolute index in the entire xml, which we can use to find the line at last
            return getErrorObject(isValid.err.code, isValid.err.msg, getLineNumberForPosition(xmlData, attrStrStart + isValid.err.line));
          }
        } else if (closingTag) {
          if (!result.tagClosed) {
            return getErrorObject('InvalidTag', "Closing tag '" + tagName + "' doesn't have proper closing.", getLineNumberForPosition(xmlData, i));
          } else if (attrStr.trim().length > 0) {
            return getErrorObject('InvalidTag', "Closing tag '" + tagName + "' can't have attributes or invalid starting.", getLineNumberForPosition(xmlData, tagStartPos));
          } else if (tags.length === 0) {
            return getErrorObject('InvalidTag', "Closing tag '" + tagName + "' has not been opened.", getLineNumberForPosition(xmlData, tagStartPos));
          } else {
            const otg = tags.pop();
            if (tagName !== otg.tagName) {
              let openPos = getLineNumberForPosition(xmlData, otg.tagStartPos);
              return getErrorObject('InvalidTag',
                "Expected closing tag '" + otg.tagName + "' (opened in line " + openPos.line + ", col " + openPos.col + ") instead of closing tag '" + tagName + "'.",
                getLineNumberForPosition(xmlData, tagStartPos));
            }

            //when there are no more tags, we reached the root level.
            if (tags.length == 0) {
              reachedRoot = true;
            }
          }
        } else {
          const isValid = validateAttributeString(attrStr, options);
          if (isValid !== true) {
            //the result from the nested function returns the position of the error within the attribute
            //in order to get the 'true' error line, we need to calculate the position where the attribute begins (i - attrStr.length) and then add the position within the attribute
            //this gives us the absolute index in the entire xml, which we can use to find the line at last
            return getErrorObject(isValid.err.code, isValid.err.msg, getLineNumberForPosition(xmlData, i - attrStr.length + isValid.err.line));
          }

          //if the root level has been reached before ...
          if (reachedRoot === true) {
            return getErrorObject('InvalidXml', 'Multiple possible root nodes found.', getLineNumberForPosition(xmlData, i));
          } else if (options.unpairedTags.indexOf(tagName) !== -1) {
            //don't push into stack
          } else {
            tags.push({ tagName, tagStartPos });
          }
          tagFound = true;
        }

        //skip tag text value
        //It may include comments and CDATA value
        for (i++; i < xmlData.length; i++) {
          if (xmlData[i] === '<') {
            if (xmlData[i + 1] === '!') {
              //comment or CADATA
              i++;
              i = readCommentAndCDATA(xmlData, i);
              continue;
            } else if (xmlData[i + 1] === '?') {
              i = readPI(xmlData, ++i);
              if (i.err) return i;
            } else {
              break;
            }
          } else if (xmlData[i] === '&') {
            const afterAmp = validateAmpersand(xmlData, i);
            if (afterAmp == -1)
              return getErrorObject('InvalidChar', "char '&' is not expected.", getLineNumberForPosition(xmlData, i));
            i = afterAmp;
          } else {
            if (reachedRoot === true && !isWhiteSpace(xmlData[i])) {
              return getErrorObject('InvalidXml', "Extra text at the end", getLineNumberForPosition(xmlData, i));
            }
          }
        } //end of reading tag text value
        if (xmlData[i] === '<') {
          i--;
        }
      }
    } else {
      if (isWhiteSpace(xmlData[i])) {
        continue;
      }
      return getErrorObject('InvalidChar', "char '" + xmlData[i] + "' is not expected.", getLineNumberForPosition(xmlData, i));
    }
  }

  if (!tagFound) {
    return getErrorObject('InvalidXml', 'Start tag expected.', 1);
  } else if (tags.length == 1) {
    return getErrorObject('InvalidTag', "Unclosed tag '" + tags[0].tagName + "'.", getLineNumberForPosition(xmlData, tags[0].tagStartPos));
  } else if (tags.length > 0) {
    return getErrorObject('InvalidXml', "Invalid '" +
      JSON.stringify(tags.map(t => t.tagName), null, 4).replace(/\r?\n/g, '') +
      "' found.", { line: 1, col: 1 });
  }

  return true;
};

function isWhiteSpace(char) {
  return char === ' ' || char === '\t' || char === '\n' || char === '\r';
}
/**
 * Read Processing insstructions and skip
 * @param {*} xmlData
 * @param {*} i
 */
function readPI(xmlData, i) {
  const start = i;
  for (; i < xmlData.length; i++) {
    if (xmlData[i] == '?' || xmlData[i] == ' ') {
      //tagname
      const tagname = xmlData.substr(start, i - start);
      if (i > 5 && tagname === 'xml') {
        return getErrorObject('InvalidXml', 'XML declaration allowed only at the start of the document.', getLineNumberForPosition(xmlData, i));
      } else if (xmlData[i] == '?' && xmlData[i + 1] == '>') {
        //check if valid attribut string
        i++;
        break;
      } else {
        continue;
      }
    }
  }
  return i;
}

function readCommentAndCDATA(xmlData, i) {
  if (xmlData.length > i + 5 && xmlData[i + 1] === '-' && xmlData[i + 2] === '-') {
    //comment
    for (i += 3; i < xmlData.length; i++) {
      if (xmlData[i] === '-' && xmlData[i + 1] === '-' && xmlData[i + 2] === '>') {
        i += 2;
        break;
      }
    }
  } else if (
    xmlData.length > i + 8 &&
    xmlData[i + 1] === 'D' &&
    xmlData[i + 2] === 'O' &&
    xmlData[i + 3] === 'C' &&
    xmlData[i + 4] === 'T' &&
    xmlData[i + 5] === 'Y' &&
    xmlData[i + 6] === 'P' &&
    xmlData[i + 7] === 'E'
  ) {
    let angleBracketsCount = 1;
    for (i += 8; i < xmlData.length; i++) {
      if (xmlData[i] === '<') {
        angleBracketsCount++;
      } else if (xmlData[i] === '>') {
        angleBracketsCount--;
        if (angleBracketsCount === 0) {
          break;
        }
      }
    }
  } else if (
    xmlData.length > i + 9 &&
    xmlData[i + 1] === '[' &&
    xmlData[i + 2] === 'C' &&
    xmlData[i + 3] === 'D' &&
    xmlData[i + 4] === 'A' &&
    xmlData[i + 5] === 'T' &&
    xmlData[i + 6] === 'A' &&
    xmlData[i + 7] === '['
  ) {
    for (i += 8; i < xmlData.length; i++) {
      if (xmlData[i] === ']' && xmlData[i + 1] === ']' && xmlData[i + 2] === '>') {
        i += 2;
        break;
      }
    }
  }

  return i;
}

const doubleQuote = '"';
const singleQuote = "'";

/**
 * Keep reading xmlData until '<' is found outside the attribute value.
 * @param {string} xmlData
 * @param {number} i
 */
function readAttributeStr(xmlData, i) {
  let attrStr = '';
  let startChar = '';
  let tagClosed = false;
  for (; i < xmlData.length; i++) {
    if (xmlData[i] === doubleQuote || xmlData[i] === singleQuote) {
      if (startChar === '') {
        startChar = xmlData[i];
      } else if (startChar !== xmlData[i]) {
        //if vaue is enclosed with double quote then single quotes are allowed inside the value and vice versa
      } else {
        startChar = '';
      }
    } else if (xmlData[i] === '>') {
      if (startChar === '') {
        tagClosed = true;
        break;
      }
    }
    attrStr += xmlData[i];
  }
  if (startChar !== '') {
    return false;
  }

  return {
    value: attrStr,
    index: i,
    tagClosed: tagClosed
  };
}

/**
 * Select all the attributes whether valid or invalid.
 */
const validAttrStrRegxp = new RegExp('(\\s*)([^\\s=]+)(\\s*=)?(\\s*([\'"])(([\\s\\S])*?)\\5)?', 'g');

//attr, ="sd", a="amit's", a="sd"b="saf", ab  cd=""

function validateAttributeString(attrStr, options) {
  //console.log("start:"+attrStr+":end");

  //if(attrStr.trim().length === 0) return true; //empty string

  const matches = getAllMatches(attrStr, validAttrStrRegxp);
  const attrNames = {};

  for (let i = 0; i < matches.length; i++) {
    if (matches[i][1].length === 0) {
      //nospace before attribute name: a="sd"b="saf"
      return getErrorObject('InvalidAttr', "Attribute '" + matches[i][2] + "' has no space in starting.", getPositionFromMatch(matches[i]))
    } else if (matches[i][3] !== undefined && matches[i][4] === undefined) {
      return getErrorObject('InvalidAttr', "Attribute '" + matches[i][2] + "' is without value.", getPositionFromMatch(matches[i]));
    } else if (matches[i][3] === undefined && !options.allowBooleanAttributes) {
      //independent attribute: ab
      return getErrorObject('InvalidAttr', "boolean attribute '" + matches[i][2] + "' is not allowed.", getPositionFromMatch(matches[i]));
    }
    /* else if(matches[i][6] === undefined){//attribute without value: ab=
                    return { err: { code:"InvalidAttr",msg:"attribute " + matches[i][2] + " has no value assigned."}};
                } */
    const attrName = matches[i][2];
    if (!validateAttrName(attrName)) {
      return getErrorObject('InvalidAttr', "Attribute '" + attrName + "' is an invalid name.", getPositionFromMatch(matches[i]));
    }
    if (!Object.prototype.hasOwnProperty.call(attrNames, attrName)) {
      //check for duplicate attribute.
      attrNames[attrName] = 1;
    } else {
      return getErrorObject('InvalidAttr', "Attribute '" + attrName + "' is repeated.", getPositionFromMatch(matches[i]));
    }
  }

  return true;
}

function validateNumberAmpersand(xmlData, i) {
  let re = /\d/;
  if (xmlData[i] === 'x') {
    i++;
    re = /[\da-fA-F]/;
  }
  for (; i < xmlData.length; i++) {
    if (xmlData[i] === ';')
      return i;
    if (!xmlData[i].match(re))
      break;
  }
  return -1;
}

function validateAmpersand(xmlData, i) {
  // https://www.w3.org/TR/xml/#dt-charref
  i++;
  if (xmlData[i] === ';')
    return -1;
  if (xmlData[i] === '#') {
    i++;
    return validateNumberAmpersand(xmlData, i);
  }
  let count = 0;
  for (; i < xmlData.length; i++, count++) {
    if (xmlData[i].match(/\w/) && count < 20)
      continue;
    if (xmlData[i] === ';')
      break;
    return -1;
  }
  return i;
}

function getErrorObject(code, message, lineNumber) {
  return {
    err: {
      code: code,
      msg: message,
      line: lineNumber.line || lineNumber,
      col: lineNumber.col,
    },
  };
}

function validateAttrName(attrName) {
  return isName(attrName);
}

// const startsWithXML = /^xml/i;

function validateTagName(tagname) {
  return isName(tagname) /* && !tagname.match(startsWithXML) */;
}

//this function returns the line number for the character at the given index
function getLineNumberForPosition(xmlData, index) {
  const lines = xmlData.substring(0, index).split(/\r?\n/);
  return {
    line: lines.length,

    // column number is last line's length + 1, because column numbering starts at 1:
    col: lines[lines.length - 1].length + 1
  };
}

//this function returns the position of the first character of match within attrStr
function getPositionFromMatch(match) {
  return match.startIndex + match[1].length;
}

;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/fxp.js






const XMLValidator = {
  validate: validate
}

;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/xmlparser/OptionsBuilder.js
const OptionsBuilder_defaultOptions = {
  preserveOrder: false,
  attributeNamePrefix: '@_',
  attributesGroupName: false,
  textNodeName: '#text',
  ignoreAttributes: true,
  removeNSPrefix: false, // remove NS from tag name or attribute name if true
  allowBooleanAttributes: false, //a tag can have attributes without any value
  //ignoreRootElement : false,
  parseTagValue: true,
  parseAttributeValue: false,
  trimValues: true, //Trim string values of tag and attributes
  cdataPropName: false,
  numberParseOptions: {
    hex: true,
    leadingZeros: true,
    eNotation: true
  },
  tagValueProcessor: function (tagName, val) {
    return val;
  },
  attributeValueProcessor: function (attrName, val) {
    return val;
  },
  stopNodes: [], //nested tags will not be parsed even for errors
  alwaysCreateTextNode: false,
  isArray: () => false,
  commentPropName: false,
  unpairedTags: [],
  processEntities: true,
  htmlEntities: false,
  ignoreDeclaration: false,
  ignorePiTags: false,
  transformTagName: false,
  transformAttributeName: false,
  updateTag: function (tagName, jPath, attrs) {
    return tagName
  },
  // skipEmptyListItem: false
  captureMetaData: false,
  maxNestedTags: 100,
  strictReservedNames: true,
};

/**
 * Normalizes processEntities option for backward compatibility
 * @param {boolean|object} value 
 * @returns {object} Always returns normalized object
 */
function normalizeProcessEntities(value) {
  // Boolean backward compatibility
  if (typeof value === 'boolean') {
    return {
      enabled: value, // true or false
      maxEntitySize: 10000,
      maxExpansionDepth: 10,
      maxTotalExpansions: 1000,
      maxExpandedLength: 100000,
      allowedTags: null,
      tagFilter: null
    };
  }

  // Object config - merge with defaults
  if (typeof value === 'object' && value !== null) {
    return {
      enabled: value.enabled !== false, // default true if not specified
      maxEntitySize: value.maxEntitySize ?? 10000,
      maxExpansionDepth: value.maxExpansionDepth ?? 10,
      maxTotalExpansions: value.maxTotalExpansions ?? 1000,
      maxExpandedLength: value.maxExpandedLength ?? 100000,
      allowedTags: value.allowedTags ?? null,
      tagFilter: value.tagFilter ?? null
    };
  }

  // Default to enabled with limits
  return normalizeProcessEntities(true);
}

const buildOptions = function (options) {
  const built = Object.assign({}, OptionsBuilder_defaultOptions, options);

  // Always normalize processEntities for backward compatibility and validation
  built.processEntities = normalizeProcessEntities(built.processEntities);
  //console.debug(built.processEntities)
  return built;
};
;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/xmlparser/xmlNode.js


let METADATA_SYMBOL;

if (typeof Symbol !== "function") {
  METADATA_SYMBOL = "@@xmlMetadata";
} else {
  METADATA_SYMBOL = Symbol("XML Node Metadata");
}

class XmlNode {
  constructor(tagname) {
    this.tagname = tagname;
    this.child = []; //nested tags, text, cdata, comments in order
    this[":@"] = Object.create(null); //attributes map
  }
  add(key, val) {
    // this.child.push( {name : key, val: val, isCdata: isCdata });
    if (key === "__proto__") key = "#__proto__";
    this.child.push({ [key]: val });
  }
  addChild(node, startIndex) {
    if (node.tagname === "__proto__") node.tagname = "#__proto__";
    if (node[":@"] && Object.keys(node[":@"]).length > 0) {
      this.child.push({ [node.tagname]: node.child, [":@"]: node[":@"] });
    } else {
      this.child.push({ [node.tagname]: node.child });
    }
    // if requested, add the startIndex
    if (startIndex !== undefined) {
      // Note: for now we just overwrite the metadata. If we had more complex metadata,
      // we might need to do an object append here:  metadata = { ...metadata, startIndex }
      this.child[this.child.length - 1][METADATA_SYMBOL] = { startIndex };
    }
  }
  /** symbol used for metadata */
  static getMetaDataSymbol() {
    return METADATA_SYMBOL;
  }
}

;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/xmlparser/DocTypeReader.js


class DocTypeReader {
    constructor(options) {
        this.suppressValidationErr = !options;
        this.options = options;
    }

    readDocType(xmlData, i) {

        const entities = Object.create(null);
        if (xmlData[i + 3] === 'O' &&
            xmlData[i + 4] === 'C' &&
            xmlData[i + 5] === 'T' &&
            xmlData[i + 6] === 'Y' &&
            xmlData[i + 7] === 'P' &&
            xmlData[i + 8] === 'E') {
            i = i + 9;
            let angleBracketsCount = 1;
            let hasBody = false, comment = false;
            let exp = "";
            for (; i < xmlData.length; i++) {
                if (xmlData[i] === '<' && !comment) { //Determine the tag type
                    if (hasBody && hasSeq(xmlData, "!ENTITY", i)) {
                        i += 7;
                        let entityName, val;
                        [entityName, val, i] = this.readEntityExp(xmlData, i + 1, this.suppressValidationErr);
                        if (val.indexOf("&") === -1) { //Parameter entities are not supported
                            const escaped = entityName.replace(/[.\-+*:]/g, '\\.');
                            entities[entityName] = {
                                regx: RegExp(`&${escaped};`, "g"),
                                val: val
                            };
                        }
                    }
                    else if (hasBody && hasSeq(xmlData, "!ELEMENT", i)) {
                        i += 8;//Not supported
                        const { index } = this.readElementExp(xmlData, i + 1);
                        i = index;
                    } else if (hasBody && hasSeq(xmlData, "!ATTLIST", i)) {
                        i += 8;//Not supported
                        // const {index} = this.readAttlistExp(xmlData,i+1);
                        // i = index;
                    } else if (hasBody && hasSeq(xmlData, "!NOTATION", i)) {
                        i += 9;//Not supported
                        const { index } = this.readNotationExp(xmlData, i + 1, this.suppressValidationErr);
                        i = index;
                    } else if (hasSeq(xmlData, "!--", i)) comment = true;
                    else throw new Error(`Invalid DOCTYPE`);

                    angleBracketsCount++;
                    exp = "";
                } else if (xmlData[i] === '>') { //Read tag content
                    if (comment) {
                        if (xmlData[i - 1] === "-" && xmlData[i - 2] === "-") {
                            comment = false;
                            angleBracketsCount--;
                        }
                    } else {
                        angleBracketsCount--;
                    }
                    if (angleBracketsCount === 0) {
                        break;
                    }
                } else if (xmlData[i] === '[') {
                    hasBody = true;
                } else {
                    exp += xmlData[i];
                }
            }
            if (angleBracketsCount !== 0) {
                throw new Error(`Unclosed DOCTYPE`);
            }
        } else {
            throw new Error(`Invalid Tag instead of DOCTYPE`);
        }
        return { entities, i };
    }
    readEntityExp(xmlData, i) {
        //External entities are not supported
        //    <!ENTITY ext SYSTEM "http://normal-website.com" >

        //Parameter entities are not supported
        //    <!ENTITY entityname "&anotherElement;">

        //Internal entities are supported
        //    <!ENTITY entityname "replacement text">

        // Skip leading whitespace after <!ENTITY
        i = skipWhitespace(xmlData, i);

        // Read entity name
        let entityName = "";
        while (i < xmlData.length && !/\s/.test(xmlData[i]) && xmlData[i] !== '"' && xmlData[i] !== "'") {
            entityName += xmlData[i];
            i++;
        }
        validateEntityName(entityName);

        // Skip whitespace after entity name
        i = skipWhitespace(xmlData, i);

        // Check for unsupported constructs (external entities or parameter entities)
        if (!this.suppressValidationErr) {
            if (xmlData.substring(i, i + 6).toUpperCase() === "SYSTEM") {
                throw new Error("External entities are not supported");
            } else if (xmlData[i] === "%") {
                throw new Error("Parameter entities are not supported");
            }
        }

        // Read entity value (internal entity)
        let entityValue = "";
        [i, entityValue] = this.readIdentifierVal(xmlData, i, "entity");

        // Validate entity size
        if (this.options.enabled !== false &&
            this.options.maxEntitySize &&
            entityValue.length > this.options.maxEntitySize) {
            throw new Error(
                `Entity "${entityName}" size (${entityValue.length}) exceeds maximum allowed size (${this.options.maxEntitySize})`
            );
        }

        i--;
        return [entityName, entityValue, i];
    }

    readNotationExp(xmlData, i) {
        // Skip leading whitespace after <!NOTATION
        i = skipWhitespace(xmlData, i);

        // Read notation name
        let notationName = "";
        while (i < xmlData.length && !/\s/.test(xmlData[i])) {
            notationName += xmlData[i];
            i++;
        }
        !this.suppressValidationErr && validateEntityName(notationName);

        // Skip whitespace after notation name
        i = skipWhitespace(xmlData, i);

        // Check identifier type (SYSTEM or PUBLIC)
        const identifierType = xmlData.substring(i, i + 6).toUpperCase();
        if (!this.suppressValidationErr && identifierType !== "SYSTEM" && identifierType !== "PUBLIC") {
            throw new Error(`Expected SYSTEM or PUBLIC, found "${identifierType}"`);
        }
        i += identifierType.length;

        // Skip whitespace after identifier type
        i = skipWhitespace(xmlData, i);

        // Read public identifier (if PUBLIC)
        let publicIdentifier = null;
        let systemIdentifier = null;

        if (identifierType === "PUBLIC") {
            [i, publicIdentifier] = this.readIdentifierVal(xmlData, i, "publicIdentifier");

            // Skip whitespace after public identifier
            i = skipWhitespace(xmlData, i);

            // Optionally read system identifier
            if (xmlData[i] === '"' || xmlData[i] === "'") {
                [i, systemIdentifier] = this.readIdentifierVal(xmlData, i, "systemIdentifier");
            }
        } else if (identifierType === "SYSTEM") {
            // Read system identifier (mandatory for SYSTEM)
            [i, systemIdentifier] = this.readIdentifierVal(xmlData, i, "systemIdentifier");

            if (!this.suppressValidationErr && !systemIdentifier) {
                throw new Error("Missing mandatory system identifier for SYSTEM notation");
            }
        }

        return { notationName, publicIdentifier, systemIdentifier, index: --i };
    }

    readIdentifierVal(xmlData, i, type) {
        let identifierVal = "";
        const startChar = xmlData[i];
        if (startChar !== '"' && startChar !== "'") {
            throw new Error(`Expected quoted string, found "${startChar}"`);
        }
        i++;

        while (i < xmlData.length && xmlData[i] !== startChar) {
            identifierVal += xmlData[i];
            i++;
        }

        if (xmlData[i] !== startChar) {
            throw new Error(`Unterminated ${type} value`);
        }
        i++;
        return [i, identifierVal];
    }

    readElementExp(xmlData, i) {
        // <!ELEMENT br EMPTY>
        // <!ELEMENT div ANY>
        // <!ELEMENT title (#PCDATA)>
        // <!ELEMENT book (title, author+)>
        // <!ELEMENT name (content-model)>

        // Skip leading whitespace after <!ELEMENT
        i = skipWhitespace(xmlData, i);

        // Read element name
        let elementName = "";
        while (i < xmlData.length && !/\s/.test(xmlData[i])) {
            elementName += xmlData[i];
            i++;
        }

        // Validate element name
        if (!this.suppressValidationErr && !isName(elementName)) {
            throw new Error(`Invalid element name: "${elementName}"`);
        }

        // Skip whitespace after element name
        i = skipWhitespace(xmlData, i);
        let contentModel = "";
        // Expect '(' to start content model
        if (xmlData[i] === "E" && hasSeq(xmlData, "MPTY", i)) i += 4;
        else if (xmlData[i] === "A" && hasSeq(xmlData, "NY", i)) i += 2;
        else if (xmlData[i] === "(") {
            i++; // Move past '('

            // Read content model
            while (i < xmlData.length && xmlData[i] !== ")") {
                contentModel += xmlData[i];
                i++;
            }
            if (xmlData[i] !== ")") {
                throw new Error("Unterminated content model");
            }

        } else if (!this.suppressValidationErr) {
            throw new Error(`Invalid Element Expression, found "${xmlData[i]}"`);
        }

        return {
            elementName,
            contentModel: contentModel.trim(),
            index: i
        };
    }

    readAttlistExp(xmlData, i) {
        // Skip leading whitespace after <!ATTLIST
        i = skipWhitespace(xmlData, i);

        // Read element name
        let elementName = "";
        while (i < xmlData.length && !/\s/.test(xmlData[i])) {
            elementName += xmlData[i];
            i++;
        }

        // Validate element name
        validateEntityName(elementName)

        // Skip whitespace after element name
        i = skipWhitespace(xmlData, i);

        // Read attribute name
        let attributeName = "";
        while (i < xmlData.length && !/\s/.test(xmlData[i])) {
            attributeName += xmlData[i];
            i++;
        }

        // Validate attribute name
        if (!validateEntityName(attributeName)) {
            throw new Error(`Invalid attribute name: "${attributeName}"`);
        }

        // Skip whitespace after attribute name
        i = skipWhitespace(xmlData, i);

        // Read attribute type
        let attributeType = "";
        if (xmlData.substring(i, i + 8).toUpperCase() === "NOTATION") {
            attributeType = "NOTATION";
            i += 8; // Move past "NOTATION"

            // Skip whitespace after "NOTATION"
            i = skipWhitespace(xmlData, i);

            // Expect '(' to start the list of notations
            if (xmlData[i] !== "(") {
                throw new Error(`Expected '(', found "${xmlData[i]}"`);
            }
            i++; // Move past '('

            // Read the list of allowed notations
            let allowedNotations = [];
            while (i < xmlData.length && xmlData[i] !== ")") {
                let notation = "";
                while (i < xmlData.length && xmlData[i] !== "|" && xmlData[i] !== ")") {
                    notation += xmlData[i];
                    i++;
                }

                // Validate notation name
                notation = notation.trim();
                if (!validateEntityName(notation)) {
                    throw new Error(`Invalid notation name: "${notation}"`);
                }

                allowedNotations.push(notation);

                // Skip '|' separator or exit loop
                if (xmlData[i] === "|") {
                    i++; // Move past '|'
                    i = skipWhitespace(xmlData, i); // Skip optional whitespace after '|'
                }
            }

            if (xmlData[i] !== ")") {
                throw new Error("Unterminated list of notations");
            }
            i++; // Move past ')'

            // Store the allowed notations as part of the attribute type
            attributeType += " (" + allowedNotations.join("|") + ")";
        } else {
            // Handle simple types (e.g., CDATA, ID, IDREF, etc.)
            while (i < xmlData.length && !/\s/.test(xmlData[i])) {
                attributeType += xmlData[i];
                i++;
            }

            // Validate simple attribute type
            const validTypes = ["CDATA", "ID", "IDREF", "IDREFS", "ENTITY", "ENTITIES", "NMTOKEN", "NMTOKENS"];
            if (!this.suppressValidationErr && !validTypes.includes(attributeType.toUpperCase())) {
                throw new Error(`Invalid attribute type: "${attributeType}"`);
            }
        }

        // Skip whitespace after attribute type
        i = skipWhitespace(xmlData, i);

        // Read default value
        let defaultValue = "";
        if (xmlData.substring(i, i + 8).toUpperCase() === "#REQUIRED") {
            defaultValue = "#REQUIRED";
            i += 8;
        } else if (xmlData.substring(i, i + 7).toUpperCase() === "#IMPLIED") {
            defaultValue = "#IMPLIED";
            i += 7;
        } else {
            [i, defaultValue] = this.readIdentifierVal(xmlData, i, "ATTLIST");
        }

        return {
            elementName,
            attributeName,
            attributeType,
            defaultValue,
            index: i
        }
    }
}



const skipWhitespace = (data, index) => {
    while (index < data.length && /\s/.test(data[index])) {
        index++;
    }
    return index;
};



function hasSeq(data, seq, i) {
    for (let j = 0; j < seq.length; j++) {
        if (seq[j] !== data[i + j + 1]) return false;
    }
    return true;
}

function validateEntityName(name) {
    if (isName(name))
        return name;
    else
        throw new Error(`Invalid entity name ${name}`);
}
;// CONCATENATED MODULE: ./node_modules/strnum/strnum.js
const hexRegex = /^[-+]?0x[a-fA-F0-9]+$/;
const numRegex = /^([\-\+])?(0*)([0-9]*(\.[0-9]*)?)$/;
// const octRegex = /^0x[a-z0-9]+/;
// const binRegex = /0x[a-z0-9]+/;

 
const consider = {
    hex :  true,
    // oct: false,
    leadingZeros: true,
    decimalPoint: "\.",
    eNotation: true,
    //skipLike: /regex/
};

function toNumber(str, options = {}){
    options = Object.assign({}, consider, options );
    if(!str || typeof str !== "string" ) return str;
    
    let trimmedStr  = str.trim();
    
    if(options.skipLike !== undefined && options.skipLike.test(trimmedStr)) return str;
    else if(str==="0") return 0;
    else if (options.hex && hexRegex.test(trimmedStr)) {
        return parse_int(trimmedStr, 16);
    // }else if (options.oct && octRegex.test(str)) {
    //     return Number.parseInt(val, 8);
    }else if (trimmedStr.includes('e') || trimmedStr.includes('E')) { //eNotation
        return resolveEnotation(str,trimmedStr,options);
    // }else if (options.parseBin && binRegex.test(str)) {
    //     return Number.parseInt(val, 2);
    }else{
        //separate negative sign, leading zeros, and rest number
        const match = numRegex.exec(trimmedStr);
        // +00.123 => [ , '+', '00', '.123', ..
        if(match){
            const sign = match[1] || "";
            const leadingZeros = match[2];
            let numTrimmedByZeros = trimZeros(match[3]); //complete num without leading zeros
            const decimalAdjacentToLeadingZeros = sign ? // 0., -00., 000.
                str[leadingZeros.length+1] === "." 
                : str[leadingZeros.length] === ".";

            //trim ending zeros for floating number
            if(!options.leadingZeros //leading zeros are not allowed
                && (leadingZeros.length > 1 
                    || (leadingZeros.length === 1 && !decimalAdjacentToLeadingZeros))){
                // 00, 00.3, +03.24, 03, 03.24
                return str;
            }
            else{//no leading zeros or leading zeros are allowed
                const num = Number(trimmedStr);
                const parsedStr = String(num);

                if( num === 0) return num;
                if(parsedStr.search(/[eE]/) !== -1){ //given number is long and parsed to eNotation
                    if(options.eNotation) return num;
                    else return str;
                }else if(trimmedStr.indexOf(".") !== -1){ //floating number
                    if(parsedStr === "0") return num; //0.0
                    else if(parsedStr === numTrimmedByZeros) return num; //0.456. 0.79000
                    else if( parsedStr === `${sign}${numTrimmedByZeros}`) return num;
                    else return str;
                }
                
                let n = leadingZeros? numTrimmedByZeros : trimmedStr;
                if(leadingZeros){
                    // -009 => -9
                    return (n === parsedStr) || (sign+n === parsedStr) ? num : str
                }else  {
                    // +9
                    return (n === parsedStr) || (n === sign+parsedStr) ? num : str
                }
            }
        }else{ //non-numeric string
            return str;
        }
    }
}

const eNotationRegx = /^([-+])?(0*)(\d*(\.\d*)?[eE][-\+]?\d+)$/;
function resolveEnotation(str,trimmedStr,options){
    if(!options.eNotation) return str;
    const notation = trimmedStr.match(eNotationRegx); 
    if(notation){
        let sign = notation[1] || "";
        const eChar = notation[3].indexOf("e") === -1 ? "E" : "e";
        const leadingZeros = notation[2];
        const eAdjacentToLeadingZeros = sign ? // 0E.
            str[leadingZeros.length+1] === eChar 
            : str[leadingZeros.length] === eChar;

        if(leadingZeros.length > 1 && eAdjacentToLeadingZeros) return str;
        else if(leadingZeros.length === 1 
            && (notation[3].startsWith(`.${eChar}`) || notation[3][0] === eChar)){
                return Number(trimmedStr);
        }else if(options.leadingZeros && !eAdjacentToLeadingZeros){ //accept with leading zeros
            //remove leading 0s
            trimmedStr = (notation[1] || "") + notation[3];
            return Number(trimmedStr);
        }else return str;
    }else{
        return str;
    }
}

/**
 * 
 * @param {string} numStr without leading zeros
 * @returns 
 */
function trimZeros(numStr){
    if(numStr && numStr.indexOf(".") !== -1){//float
        numStr = numStr.replace(/0+$/, ""); //remove ending zeros
        if(numStr === ".")  numStr = "0";
        else if(numStr[0] === ".")  numStr = "0"+numStr;
        else if(numStr[numStr.length-1] === ".")  numStr = numStr.substring(0,numStr.length-1);
        return numStr;
    }
    return numStr;
}

function parse_int(numStr, base){
    //polyfill
    if(parseInt) return parseInt(numStr, base);
    else if(Number.parseInt) return Number.parseInt(numStr, base);
    else if(window && window.parseInt) return window.parseInt(numStr, base);
    else throw new Error("parseInt, Number.parseInt, window.parseInt are not supported")
}
;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/ignoreAttributes.js
function ignoreAttributes_getIgnoreAttributesFn(ignoreAttributes) {
    if (typeof ignoreAttributes === 'function') {
        return ignoreAttributes
    }
    if (Array.isArray(ignoreAttributes)) {
        return (attrName) => {
            for (const pattern of ignoreAttributes) {
                if (typeof pattern === 'string' && attrName === pattern) {
                    return true
                }
                if (pattern instanceof RegExp && pattern.test(attrName)) {
                    return true
                }
            }
        }
    }
    return () => false
}
;// CONCATENATED MODULE: ./node_modules/fast-xml-parser/src/xmlparser/OrderedObjParser.js

///@ts-check







// const regx =
//   '<((!\\[CDATA\\[([\\s\\S]*?)(]]>))|((NAME:)?(NAME))([^>]*)>|((\\/)(NAME)\\s*>))([^<]*)'
//   .replace(/NAME/g, util.nameRegexp);

//const tagsRegx = new RegExp("<(\\/?[\\w:\\-\._]+)([^>]*)>(\\s*"+cdataRegx+")*([^<]+)?","g");
//const tagsRegx = new RegExp("<(\\/?)((\\w*:)?([\\w:\\-\._]+))([^>]*)>([^<]*)("+cdataRegx+"([^<]*))*([^<]+)?","g");

class OrderedObjParser {
  constructor(options) {
    this.options = options;
    this.currentNode = null;
    this.tagsNodeStack = [];
    this.docTypeEntities = {};
    this.lastEntities = {
      "apos": { regex: /&(apos|#39|#x27);/g, val: "'" },
      "gt": { regex: /&(gt|#62|#x3E);/g, val: ">" },
      "lt": { regex: /&(lt|#60|#x3C);/g, val: "<" },
      "quot": { regex: /&(quot|#34|#x22);/g, val: "\"" },
    };
    this.ampEntity = { regex: /&(amp|#38|#x26);/g, val: "&" };
    this.htmlEntities = {
      "space": { regex: /&(nbsp|#160);/g, val: " " },
      // "lt" : { regex: /&(lt|#60);/g, val: "<" },
      // "gt" : { regex: /&(gt|#62);/g, val: ">" },
      // "amp" : { regex: /&(amp|#38);/g, val: "&" },
      // "quot" : { regex: /&(quot|#34);/g, val: "\"" },
      // "apos" : { regex: /&(apos|#39);/g, val: "'" },
      "cent": { regex: /&(cent|#162);/g, val: "¢" },
      "pound": { regex: /&(pound|#163);/g, val: "£" },
      "yen": { regex: /&(yen|#165);/g, val: "¥" },
      "euro": { regex: /&(euro|#8364);/g, val: "€" },
      "copyright": { regex: /&(copy|#169);/g, val: "©" },
      "reg": { regex: /&(reg|#174);/g, val: "®" },
      "inr": { regex: /&(inr|#8377);/g, val: "₹" },
      "num_dec": { regex: /&#([0-9]{1,7});/g, val: (_, str) => fromCodePoint(str, 10, "&#") },
      "num_hex": { regex: /&#x([0-9a-fA-F]{1,6});/g, val: (_, str) => fromCodePoint(str, 16, "&#x") },
    };
    this.addExternalEntities = addExternalEntities;
    this.parseXml = parseXml;
    this.parseTextData = parseTextData;
    this.resolveNameSpace = resolveNameSpace;
    this.buildAttributesMap = buildAttributesMap;
    this.isItStopNode = isItStopNode;
    this.replaceEntitiesValue = OrderedObjParser_replaceEntitiesValue;
    this.readStopNodeData = readStopNodeData;
    this.saveTextToParentTag = saveTextToParentTag;
    this.addChild = addChild;
    this.ignoreAttributesFn = ignoreAttributes_getIgnoreAttributesFn(this.options.ignoreAttributes)
    this.entityExpansionCount = 0;
    this.currentExpandedLength = 0;

    if (this.options.stopNodes && this.options.stopNodes.length > 0) {
      this.stopNodesExact = new Set();
      this.stopNodesWildcard = new Set();
      for (let i = 0; i < this.options.stopNodes.length; i++) {
        const stopNodeExp = this.options.stopNodes[i];
        if (typeof stopNodeExp !== 'string') continue;
        if (stopNodeExp.startsWith("*.")) {
          this.stopNodesWildcard.add(stopNodeExp.substring(2));
        } else {
          this.stopNodesExact.add(stopNodeExp);
        }
      }
    }
  }

}

function addExternalEntities(externalEntities) {
  const entKeys = Object.keys(externalEntities);
  for (let i = 0; i < entKeys.length; i++) {
    const ent = entKeys[i];
    const escaped = ent.replace(/[.\-+*:]/g, '\\.');
    this.lastEntities[ent] = {
      regex: new RegExp("&" + escaped + ";", "g"),
      val: externalEntities[ent]
    }
  }
}

/**
 * @param {string} val
 * @param {string} tagName
 * @param {string} jPath
 * @param {boolean} dontTrim
 * @param {boolean} hasAttributes
 * @param {boolean} isLeafNode
 * @param {boolean} escapeEntities
 */
function parseTextData(val, tagName, jPath, dontTrim, hasAttributes, isLeafNode, escapeEntities) {
  if (val !== undefined) {
    if (this.options.trimValues && !dontTrim) {
      val = val.trim();
    }
    if (val.length > 0) {
      if (!escapeEntities) val = this.replaceEntitiesValue(val, tagName, jPath);

      const newval = this.options.tagValueProcessor(tagName, val, jPath, hasAttributes, isLeafNode);
      if (newval === null || newval === undefined) {
        //don't parse
        return val;
      } else if (typeof newval !== typeof val || newval !== val) {
        //overwrite
        return newval;
      } else if (this.options.trimValues) {
        return parseValue(val, this.options.parseTagValue, this.options.numberParseOptions);
      } else {
        const trimmedVal = val.trim();
        if (trimmedVal === val) {
          return parseValue(val, this.options.parseTagValue, this.options.numberParseOptions);
        } else {
          return val;
        }
      }
    }
  }
}

function resolveNameSpace(tagname) {
  if (this.options.removeNSPrefix) {
    const tags = tagname.split(':');
    const prefix = tagname.charAt(0) === '/' ? '/' : '';
    if (tags[0] === 'xmlns') {
      return '';
    }
    if (tags.length === 2) {
      tagname = prefix + tags[1];
    }
  }
  return tagname;
}

//TODO: change regex to capture NS
//const attrsRegx = new RegExp("([\\w\\-\\.\\:]+)\\s*=\\s*(['\"])((.|\n)*?)\\2","gm");
const attrsRegx = new RegExp('([^\\s=]+)\\s*(=\\s*([\'"])([\\s\\S]*?)\\3)?', 'gm');

function buildAttributesMap(attrStr, jPath, tagName) {
  if (this.options.ignoreAttributes !== true && typeof attrStr === 'string') {
    // attrStr = attrStr.replace(/\r?\n/g, ' ');
    //attrStr = attrStr || attrStr.trim();

    const matches = getAllMatches(attrStr, attrsRegx);
    const len = matches.length; //don't make it inline
    const attrs = {};
    for (let i = 0; i < len; i++) {
      const attrName = this.resolveNameSpace(matches[i][1]);
      if (this.ignoreAttributesFn(attrName, jPath)) {
        continue
      }
      let oldVal = matches[i][4];
      let aName = this.options.attributeNamePrefix + attrName;
      if (attrName.length) {
        if (this.options.transformAttributeName) {
          aName = this.options.transformAttributeName(aName);
        }
        if (aName === "__proto__") aName = "#__proto__";

        if (oldVal !== undefined) {
          if (this.options.trimValues) {
            oldVal = oldVal.trim();
          }
          oldVal = this.replaceEntitiesValue(oldVal, tagName, jPath);
          const newVal = this.options.attributeValueProcessor(attrName, oldVal, jPath);
          if (newVal === null || newVal === undefined) {
            //don't parse
            attrs[aName] = oldVal;
          } else if (typeof newVal !== typeof oldVal || newVal !== oldVal) {
            //overwrite
            attrs[aName] = newVal;
          } else {
            //parse
            attrs[aName] = parseValue(
              oldVal,
              this.options.parseAttributeValue,
              this.options.numberParseOptions
            );
          }
        } else if (this.options.allowBooleanAttributes) {
          attrs[aName] = true;
        }
      }
    }
    if (!Object.keys(attrs).length) {
      return;
    }
    if (this.options.attributesGroupName) {
      const attrCollection = {};
      attrCollection[this.options.attributesGroupName] = attrs;
      return attrCollection;
    }
    return attrs
  }
}

const parseXml = function (xmlData) {
  xmlData = xmlData.replace(/\r\n?/g, "\n"); //TODO: remove this line
  const xmlObj = new XmlNode('!xml');
  let currentNode = xmlObj;
  let textData = "";
  let jPath = "";

  // Reset entity expansion counters for this document
  this.entityExpansionCount = 0;
  this.currentExpandedLength = 0;

  const docTypeReader = new DocTypeReader(this.options.processEntities);
  for (let i = 0; i < xmlData.length; i++) {//for each char in XML data
    const ch = xmlData[i];
    if (ch === '<') {
      // const nextIndex = i+1;
      // const _2ndChar = xmlData[nextIndex];
      if (xmlData[i + 1] === '/') {//Closing Tag
        const closeIndex = findClosingIndex(xmlData, ">", i, "Closing Tag is not closed.")
        let tagName = xmlData.substring(i + 2, closeIndex).trim();

        if (this.options.removeNSPrefix) {
          const colonIndex = tagName.indexOf(":");
          if (colonIndex !== -1) {
            tagName = tagName.substr(colonIndex + 1);
          }
        }

        if (this.options.transformTagName) {
          tagName = this.options.transformTagName(tagName);
        }

        if (currentNode) {
          textData = this.saveTextToParentTag(textData, currentNode, jPath);
        }

        //check if last tag of nested tag was unpaired tag
        const lastTagName = jPath.substring(jPath.lastIndexOf(".") + 1);
        if (tagName && this.options.unpairedTags.indexOf(tagName) !== -1) {
          throw new Error(`Unpaired tag can not be used as closing tag: </${tagName}>`);
        }
        let propIndex = 0
        if (lastTagName && this.options.unpairedTags.indexOf(lastTagName) !== -1) {
          propIndex = jPath.lastIndexOf('.', jPath.lastIndexOf('.') - 1)
          this.tagsNodeStack.pop();
        } else {
          propIndex = jPath.lastIndexOf(".");
        }
        jPath = jPath.substring(0, propIndex);

        currentNode = this.tagsNodeStack.pop();//avoid recursion, set the parent tag scope
        textData = "";
        i = closeIndex;
      } else if (xmlData[i + 1] === '?') {

        let tagData = readTagExp(xmlData, i, false, "?>");
        if (!tagData) throw new Error("Pi Tag is not closed.");

        textData = this.saveTextToParentTag(textData, currentNode, jPath);
        if ((this.options.ignoreDeclaration && tagData.tagName === "?xml") || this.options.ignorePiTags) {
          //do nothing
        } else {

          const childNode = new XmlNode(tagData.tagName);
          childNode.add(this.options.textNodeName, "");

          if (tagData.tagName !== tagData.tagExp && tagData.attrExpPresent) {
            childNode[":@"] = this.buildAttributesMap(tagData.tagExp, jPath, tagData.tagName);
          }
          this.addChild(currentNode, childNode, jPath, i);
        }


        i = tagData.closeIndex + 1;
      } else if (xmlData.substr(i + 1, 3) === '!--') {
        const endIndex = findClosingIndex(xmlData, "-->", i + 4, "Comment is not closed.")
        if (this.options.commentPropName) {
          const comment = xmlData.substring(i + 4, endIndex - 2);

          textData = this.saveTextToParentTag(textData, currentNode, jPath);

          currentNode.add(this.options.commentPropName, [{ [this.options.textNodeName]: comment }]);
        }
        i = endIndex;
      } else if (xmlData.substr(i + 1, 2) === '!D') {
        const result = docTypeReader.readDocType(xmlData, i);
        this.docTypeEntities = result.entities;
        i = result.i;
      } else if (xmlData.substr(i + 1, 2) === '![') {
        const closeIndex = findClosingIndex(xmlData, "]]>", i, "CDATA is not closed.") - 2;
        const tagExp = xmlData.substring(i + 9, closeIndex);

        textData = this.saveTextToParentTag(textData, currentNode, jPath);

        let val = this.parseTextData(tagExp, currentNode.tagname, jPath, true, false, true, true);
        if (val == undefined) val = "";

        //cdata should be set even if it is 0 length string
        if (this.options.cdataPropName) {
          currentNode.add(this.options.cdataPropName, [{ [this.options.textNodeName]: tagExp }]);
        } else {
          currentNode.add(this.options.textNodeName, val);
        }

        i = closeIndex + 2;
      } else {//Opening tag
        let result = readTagExp(xmlData, i, this.options.removeNSPrefix);
        let tagName = result.tagName;
        const rawTagName = result.rawTagName;
        let tagExp = result.tagExp;
        let attrExpPresent = result.attrExpPresent;
        let closeIndex = result.closeIndex;

        if (this.options.transformTagName) {
          //console.log(tagExp, tagName)
          const newTagName = this.options.transformTagName(tagName);
          if (tagExp === tagName) {
            tagExp = newTagName
          }
          tagName = newTagName;
        }

        if (this.options.strictReservedNames &&
          (tagName === this.options.commentPropName
            || tagName === this.options.cdataPropName
          )) {
          throw new Error(`Invalid tag name: ${tagName}`);
        }

        //save text as child node
        if (currentNode && textData) {
          if (currentNode.tagname !== '!xml') {
            //when nested tag is found
            textData = this.saveTextToParentTag(textData, currentNode, jPath, false);
          }
        }

        //check if last tag was unpaired tag
        const lastTag = currentNode;
        if (lastTag && this.options.unpairedTags.indexOf(lastTag.tagname) !== -1) {
          currentNode = this.tagsNodeStack.pop();
          jPath = jPath.substring(0, jPath.lastIndexOf("."));
        }
        if (tagName !== xmlObj.tagname) {
          jPath += jPath ? "." + tagName : tagName;
        }
        const startIndex = i;
        if (this.isItStopNode(this.stopNodesExact, this.stopNodesWildcard, jPath, tagName)) {
          let tagContent = "";
          //self-closing tag
          if (tagExp.length > 0 && tagExp.lastIndexOf("/") === tagExp.length - 1) {
            if (tagName[tagName.length - 1] === "/") { //remove trailing '/'
              tagName = tagName.substr(0, tagName.length - 1);
              jPath = jPath.substr(0, jPath.length - 1);
              tagExp = tagName;
            } else {
              tagExp = tagExp.substr(0, tagExp.length - 1);
            }
            i = result.closeIndex;
          }
          //unpaired tag
          else if (this.options.unpairedTags.indexOf(tagName) !== -1) {

            i = result.closeIndex;
          }
          //normal tag
          else {
            //read until closing tag is found
            const result = this.readStopNodeData(xmlData, rawTagName, closeIndex + 1);
            if (!result) throw new Error(`Unexpected end of ${rawTagName}`);
            i = result.i;
            tagContent = result.tagContent;
          }

          const childNode = new XmlNode(tagName);

          if (tagName !== tagExp && attrExpPresent) {
            childNode[":@"] = this.buildAttributesMap(tagExp, jPath, tagName);
          }
          if (tagContent) {
            tagContent = this.parseTextData(tagContent, tagName, jPath, true, attrExpPresent, true, true);
          }

          jPath = jPath.substr(0, jPath.lastIndexOf("."));
          childNode.add(this.options.textNodeName, tagContent);

          this.addChild(currentNode, childNode, jPath, startIndex);
        } else {
          //selfClosing tag
          if (tagExp.length > 0 && tagExp.lastIndexOf("/") === tagExp.length - 1) {
            if (tagName[tagName.length - 1] === "/") { //remove trailing '/'
              tagName = tagName.substr(0, tagName.length - 1);
              jPath = jPath.substr(0, jPath.length - 1);
              tagExp = tagName;
            } else {
              tagExp = tagExp.substr(0, tagExp.length - 1);
            }

            if (this.options.transformTagName) {
              const newTagName = this.options.transformTagName(tagName);
              if (tagExp === tagName) {
                tagExp = newTagName
              }
              tagName = newTagName;
            }

            const childNode = new XmlNode(tagName);
            if (tagName !== tagExp && attrExpPresent) {
              childNode[":@"] = this.buildAttributesMap(tagExp, jPath, tagName);
            }
            this.addChild(currentNode, childNode, jPath, startIndex);
            jPath = jPath.substr(0, jPath.lastIndexOf("."));
          }
          else if(this.options.unpairedTags.indexOf(tagName) !== -1){//unpaired tag
            const childNode = new XmlNode(tagName);
            if(tagName !== tagExp && attrExpPresent){
              childNode[":@"] = this.buildAttributesMap(tagExp, jPath);
            }
            this.addChild(currentNode, childNode, jPath, startIndex);
            jPath = jPath.substr(0, jPath.lastIndexOf("."));
            i = result.closeIndex;
            // Continue to next iteration without changing currentNode
            continue;
          }
          //opening tag
          else {
            const childNode = new XmlNode(tagName);
            if (this.tagsNodeStack.length > this.options.maxNestedTags) {
              throw new Error("Maximum nested tags exceeded");
            }
            this.tagsNodeStack.push(currentNode);

            if (tagName !== tagExp && attrExpPresent) {
              childNode[":@"] = this.buildAttributesMap(tagExp, jPath, tagName);
            }
            this.addChild(currentNode, childNode, jPath, startIndex);
            currentNode = childNode;
          }
          textData = "";
          i = closeIndex;
        }
      }
    } else {
      textData += xmlData[i];
    }
  }
  return xmlObj.child;
}

function addChild(currentNode, childNode, jPath, startIndex) {
  // unset startIndex if not requested
  if (!this.options.captureMetaData) startIndex = undefined;
  const result = this.options.updateTag(childNode.tagname, jPath, childNode[":@"])
  if (result === false) {
    //do nothing
  } else if (typeof result === "string") {
    childNode.tagname = result
    currentNode.addChild(childNode, startIndex);
  } else {
    currentNode.addChild(childNode, startIndex);
  }
}

const OrderedObjParser_replaceEntitiesValue = function (val, tagName, jPath) {
  // Performance optimization: Early return if no entities to replace
  if (val.indexOf('&') === -1) {
    return val;
  }

  const entityConfig = this.options.processEntities;

  if (!entityConfig.enabled) {
    return val;
  }

  // Check tag-specific filtering
  if (entityConfig.allowedTags) {
    if (!entityConfig.allowedTags.includes(tagName)) {
      return val; // Skip entity replacement for current tag as not set
    }
  }

  if (entityConfig.tagFilter) {
    if (!entityConfig.tagFilter(tagName, jPath)) {
      return val; // Skip based on custom filter
    }
  }

  // Replace DOCTYPE entities
  for (let entityName in this.docTypeEntities) {
    const entity = this.docTypeEntities[entityName];
    const matches = val.match(entity.regx);

    if (matches) {
      // Track expansions
      this.entityExpansionCount += matches.length;

      // Check expansion limit
      if (entityConfig.maxTotalExpansions &&
        this.entityExpansionCount > entityConfig.maxTotalExpansions) {
        throw new Error(
          `Entity expansion limit exceeded: ${this.entityExpansionCount} > ${entityConfig.maxTotalExpansions}`
        );
      }

      // Store length before replacement
      const lengthBefore = val.length;
      val = val.replace(entity.regx, entity.val);

      // Check expanded length immediately after replacement
      if (entityConfig.maxExpandedLength) {
        this.currentExpandedLength += (val.length - lengthBefore);

        if (this.currentExpandedLength > entityConfig.maxExpandedLength) {
          throw new Error(
            `Total expanded content size exceeded: ${this.currentExpandedLength} > ${entityConfig.maxExpandedLength}`
          );
        }
      }
    }
  }
  if (val.indexOf('&') === -1) return val;  // Early exit

