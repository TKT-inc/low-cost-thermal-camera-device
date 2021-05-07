# import the necessary packages
from scipy.spatial import distance as dist
from collections import OrderedDict
from datetime import datetime
import numpy as np
import base64
import cv2
import yaml
with open("configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

MAX_DISAPEARED_FRAMES = cfg['personTracking']['noOfDisapearFrames']
MAX_DISAPEARED_FRAMES_FOR_CALIB = cfg['personTracking']['noOfDisapearFramesForCalib']
BUFFER_TEMP = cfg['personTracking']['bufSizeTempPersonTracking']
BUFFER_RECONITE = cfg['personTracking']['bufSizeNameAndIdPersonTracking']
RECORD_FACE_SIZE = cfg['personTracking']['recordFaceSize']
MIN_FACE_SIZE_ONE_PERSON_MODE = cfg['personTracking']['minFaceSizeOfOnePersonMode']
MAX_FACE_SIZE_ONE_PERSON_MODE = cfg['personTracking']['maxFaceSizeOfOnePersonMode']

class ObjectInfo():
	def __init__(self, coor, rgb, scale, fever_temp=38):
		self.coor = coor
		self.name = "None"
		self.id = "None"
		self.temperature = "None"
		self.record_temperature = 0
		self.have_mask = "N/A"
		self.face_rgb = rgb[int(coor[1]*scale):int(coor[3]*scale), int(coor[0]*scale):int(coor[2]*scale)]
		self.rec_stacks = []
		self.temp_stacks = []
		self.fever_temp = fever_temp
		self.sending_recs_img = False
		self.temporary_dissapear = False
		self.internet_available = False
	
	# def turnToOffline(self):
	# 	self.internet_available = False

	def updateInfo(self, name, id, have_mask):
		self.internet_available = True
		self.have_mask = have_mask == "True"
		self.rec_stacks.append((name, id))
		if (len(self.rec_stacks) > BUFFER_RECONITE):
			self.rec_stacks.pop(0)
			self.name, self.id = max(self.rec_stacks, key=self.rec_stacks.count)
		else:
			self.name = name
			self.id = id

	def updateTemperature(self, temp):
		self.temp_stacks.append(temp)

		if (len(self.temp_stacks) > BUFFER_TEMP):
			self.temp_stacks.pop(0)

		self.record_temperature = np.average(self.temp_stacks) 
		self.temperature = "{:.2f}".format(temp) + " oC"

	def resetTemperature(self):
		self.temp_stacks = []

	def gotFever(self):
		if(self.record_temperature >= self.fever_temp):
			return True
		return False


class RecordsObject():
	def __init__(self ):
		self.records = OrderedDict()

	def addNewRecord(self, objectId, obj):
		if (obj.record_temperature > 25 and obj.record_temperature < 42):
			self.records[objectId] = self.Record(id = obj.id, name=obj.name, record_temperature = obj.record_temperature, got_fever = obj.gotFever(), face_rgb = obj.face_rgb, have_mask = obj.have_mask, internet_available=obj.internet_available)
		
	class Record():
		def __init__(self, id, name, record_temperature, got_fever, face_rgb, have_mask, internet_available):
			self.id = id
			self.name= name
			self.record_temperature = record_temperature
			self.got_fever = got_fever
			self.face_rgb = face_rgb
			self.have_mask = have_mask
			self.record_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
			self.internet_available = internet_available
		
		def convertBinaryImg(self):
			_, buffer = cv2.imencode('.jpg', cv2.resize(self.face_rgb,(RECORD_FACE_SIZE,RECORD_FACE_SIZE)))
			pic_str = base64.b64encode(buffer)
			pic_str = pic_str.decode()
			return pic_str

		def jsonable(self):
			return dict(id=self.id, record_time=self.record_time, record_temperature=self.record_temperature, have_mask=self.have_mask , internet_available=self.internet_available, pic_str=self.convertBinaryImg())


class CentroidTracker():
	def __init__(self):
		# initialize the next unique object ID along with two ordered
		# dictionaries used to keep track of mapping a given object
		# ID to its centroid and number of consecutive frames it has
		# been marked as "disappeared", respectively
		self.nextObjectID = 0
		self.objects = OrderedDict()
		self.disappeared = OrderedDict()

		# store the number of maximum consecutive frames a given
		# object is allowed to be marked as "disappeared" until we
		# need to deregister the object from tracking

	def getCentroid(self, coor):
		cX = int((coor[0] + coor[2]) / 2.0)
		cY = int((coor[1] + coor[3]) / 2.0)
		return (cX, cY)

	def register(self, coor, rgb, scale, fever_temp):
		# when registering an object we use the next available object
		# ID to store the centroid
		obj = ObjectInfo(coor, rgb, scale, fever_temp)
		self.objects[self.nextObjectID] = obj
		self.disappeared[self.nextObjectID] = 0
		self.nextObjectID += 1
	
	def deregister(self, objectID):
		# to deregister an object ID we delete the object ID from
		# both of our respective dictionaries
		del self.objects[objectID]
		del self.disappeared[objectID]


	def update(self, rects, rgb, scale, fever_temp=38, onePersonMeasurement=False, calibrateFlag=False):
		# check to see if the list of input bounding box rectangles
		# is empty
		if (calibrateFlag):
			maxDisapearedFrames = MAX_DISAPEARED_FRAMES_FOR_CALIB
		else: 
			maxDisapearedFrames = MAX_DISAPEARED_FRAMES
		
		disappearedObjects = RecordsObject()

		if (onePersonMeasurement and len(rects) > 0):
			maxAreaFace = max(rects, key=lambda x : (x[2]-x[0])*(x[3]-x[1]))
			area = (maxAreaFace[2]-maxAreaFace[0])*(maxAreaFace[3]-maxAreaFace[1])*scale*scale
			if area <= MAX_FACE_SIZE_ONE_PERSON_MODE and area >= MIN_FACE_SIZE_ONE_PERSON_MODE:
				rects = [maxAreaFace]
			else:
				rects = []
		
		if len(rects) == 0:
			# loop over any existing tracked objects and mark them
			# as disappeared
			for objectID in list(self.disappeared.keys()):
				self.disappeared[objectID] += 1
				if self.disappeared[objectID] > 7:
					self.objects[objectID].temporary_dissapear = True
				# if we have reached a maximum number of consecutive
				# frames where a given object has been marked as
				# missing, deregister it
				if self.disappeared[objectID] > maxDisapearedFrames:
					disappearedObjects.addNewRecord(objectID, self.objects[objectID])
					self.deregister(objectID)

			# return early as there are no centroids or tracking info
			# to update
			return self.objects, disappearedObjects
		# initialize an array of input centroids for the current frame
		inputCentroids = np.zeros((len(rects), 2), dtype="int")

		# loop over the bounding box rectangles
		for (i, (startX, startY, endX, endY)) in enumerate(rects):
			# use the bounding box coordinates to derive the centroid
			(cX, cY) = self.getCentroid((startX, startY, endX, endY))
			inputCentroids[i] = (cX, cY)

		# if we are currently not tracking any objects take the input
		# centroids and register each of them
		if len(self.objects) == 0:
			for i in range(0, len(inputCentroids)):
				self.register(rects[i], rgb, scale, fever_temp)

		# otherwise, are are currently tracking objects so we need to
		# try to match the input centroids to existing object
		# centroids
		else:
			# grab the set of object IDs and corresponding centroids
			objectIDs = list(self.objects.keys())
			arr = list(self.objects.values())
			objectCoors = list()
			for i in range(len(arr)):
				objectCoors.append(arr[i].coor)
			objectCentroids = list()
			for (i, (startX, startY, endX, endY)) in enumerate(objectCoors):
				(cX, cY) = self.getCentroid((startX, startY, endX, endY))
				objectCentroids.append((cX, cY))
			# compute the distance between each pair of object
			# centroids and input centroids, respectively -- our
			# goal will be to match an input centroid to an existing
			# object centroid
			D = dist.cdist(np.array(objectCentroids), inputCentroids)

			# in order to perform this matching we must (1) find the
			# smallest value in each row and then (2) sort the row
			# indexes based on their minimum values so that the row
			# with the smallest value as at the *front* of the index
			# list
			rows = D.min(axis=1).argsort()

			# next, we perform a similar process on the columns by
			# finding the smallest value in each column and then
			# sorting using the previously computed row index list
			cols = D.argmin(axis=1)[rows]

			# in order to determine if we need to update, register,
			# or deregister an object we need to keep track of which
			# of the rows and column indexes we have already examined
			usedRows = set()
			usedCols = set()

			# loop over the combination of the (row, column) index
			# tuples
			for (row, col) in zip(rows, cols):
				# if we have already examined either the row or
				# column value before, ignore it
				# val
				if row in usedRows or col in usedCols:
					continue

				# otherwise, grab the object ID for the current row,
				# set its new centroid, and reset the disappeared
				# counter
				objectID = objectIDs[row]
				self.objects[objectID].coor = rects[col]
				self.objects[objectID].temporary_dissapear = False
				face = rgb[int(rects[col][1]*scale):int(rects[col][3]*scale), int(rects[col][0]*scale):int(rects[col][2]*scale)]
				if (len(face) != 0):
					self.objects[objectID].face_rgb =  face
				self.disappeared[objectID] = 0

				# indicate that we have examined each of the row and
				# column indexes, respectively
				usedRows.add(row)
				usedCols.add(col)

			# compute both the row and column index we have NOT yet
			# examined
			unusedRows = set(range(0, D.shape[0])).difference(usedRows)
			unusedCols = set(range(0, D.shape[1])).difference(usedCols)

			# in the event that the number of object centroids is
			# equal or greater than the number of input centroids
			# we need to check and see if some of these objects have
			# potentially disappeared
			if D.shape[0] >= D.shape[1]:
				# loop over the unused row indexes
				for row in unusedRows:
					# grab the object ID for the corresponding row
					# index and increment the disappeared counter
					objectID = objectIDs[row]
					self.disappeared[objectID] += 1

					if self.disappeared[objectID] > 7:
						self.objects[objectID].temporary_dissapear = True

					# check to see if the number of consecutive
					# frames the object has been marked "disappeared"
					# for warrants deregistering the object
					if self.disappeared[objectID] > maxDisapearedFrames:
						disappearedObjects.addNewRecord(objectID, self.objects[objectID])
						self.deregister(objectID)

			# otherwise, if the number of input centroids is greater
			# than the number of existing object centroids we need to
			# register each new input centroid as a trackable object
			else:
				for col in unusedCols:
					self.register(rects[col],rgb, scale, fever_temp)

		# return the set of trackable objects
		return self.objects, disappearedObjects