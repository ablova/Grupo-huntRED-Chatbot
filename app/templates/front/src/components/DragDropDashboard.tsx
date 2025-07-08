import React, { useState } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Clock, CheckCircle, User, Calendar, Briefcase, ArrowRight, MessageSquare, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Definición de tipos para candidatos y columnas
interface Candidate {
  id: string;
  name: string;
  position: string;
  company: string;
  avatar: string;
  match: number;
  status: string;
  interview?: Date;
}

interface Column {
  id: string;
  title: string;
  color: string;
  icon: React.ReactNode;
  description: string;
  candidateIds: string[];
  actionDescription: string;
}

const DragDropDashboard = () => {
  // Estado para mostrar notificaciones/popups
  const [notification, setNotification] = useState<{
    visible: boolean;
    message: string;
    type: string;
    action?: string;
    candidate?: string;
  }>({
    visible: false,
    message: '',
    type: '',
    action: '',
    candidate: '',
  });

  // Datos de candidatos simulados
  const initialCandidates: { [key: string]: Candidate } = {
    'c1': {
      id: 'c1',
      name: 'María González',
      position: 'Full Stack Developer',
      company: 'TechCorp',
      avatar: 'https://randomuser.me/api/portraits/women/44.jpg',
      match: 92,
      status: 'Evaluación',
    },
    'c2': {
      id: 'c2',
      name: 'Carlos Rodríguez',
      position: 'Data Scientist',
      company: 'DataInsights',
      avatar: 'https://randomuser.me/api/portraits/men/32.jpg',
      match: 89,
      status: 'Evaluación',
    },
    'c3': {
      id: 'c3',
      name: 'Ana Martínez',
      position: 'UX Designer',
      company: 'CreativeStudio',
      avatar: 'https://randomuser.me/api/portraits/women/68.jpg',
      match: 85,
      status: 'Evaluación',
    },
    'c4': {
      id: 'c4',
      name: 'Juan Pérez',
      position: 'Backend Developer',
      company: 'ServerPro',
      avatar: 'https://randomuser.me/api/portraits/men/46.jpg',
      match: 78,
      status: 'Evaluación',
    },
    'c5': {
      id: 'c5',
      name: 'Sofía Vega',
      position: 'Product Manager',
      company: 'InnovateTech',
      avatar: 'https://randomuser.me/api/portraits/women/65.jpg',
      match: 94,
      status: 'Evaluación',
    },
  };

  // Columnas iniciales con estados de selección
  const initialColumns: { [key: string]: Column } = {
    'evaluacion': {
      id: 'evaluacion',
      title: 'Evaluación',
      color: 'bg-blue-500',
      icon: <User className="h-4 w-4" />,
      description: 'Candidatos en fase de revisión inicial',
      candidateIds: ['c1', 'c2', 'c3', 'c4', 'c5'],
      actionDescription: 'Revisión inicial de perfil'
    },
    'entrevista': {
      id: 'entrevista',
      title: 'Entrevista',
      color: 'bg-purple-500',
      icon: <Calendar className="h-4 w-4" />,
      description: 'Programados para entrevista',
      candidateIds: [],
      actionDescription: 'Programación automática de entrevista'
    },
    'oferta': {
      id: 'oferta',
      title: 'Oferta',
      color: 'bg-green-500',
      icon: <FileText className="h-4 w-4" />,
      description: 'Preparados para envío de oferta',
      candidateIds: [],
      actionDescription: 'Envío automático de carta oferta'
    },
    'contratado': {
      id: 'contratado',
      title: 'Contratado',
      color: 'bg-red-500',
      icon: <Briefcase className="h-4 w-4" />,
      description: 'Proceso de contratación iniciado',
      candidateIds: [],
      actionDescription: 'Inicio de onboarding'
    }
  };

  // Estado para gestionar candidatos y columnas
  const [candidates, setCandidates] = useState(initialCandidates);
  const [columns, setColumns] = useState(initialColumns);
  
  // Maneja el fin de un evento de drag & drop
  const onDragEnd = (result: any) => {
    const { destination, source, draggableId } = result;

    // Si no hay destino o el destino es el mismo que el origen, no hacemos nada
    if (!destination || 
        (destination.droppableId === source.droppableId && 
         destination.index === source.index)) {
      return;
    }

    // Columna de origen
    const sourceColumn = columns[source.droppableId];
    // Columna de destino
    const destColumn = columns[destination.droppableId];
    
    // Si es la misma columna, solo reordenamos dentro de la misma
    if (source.droppableId === destination.droppableId) {
      const newCandidateIds = Array.from(sourceColumn.candidateIds);
      newCandidateIds.splice(source.index, 1);
      newCandidateIds.splice(destination.index, 0, draggableId);
      
      const newColumn = {
        ...sourceColumn,
        candidateIds: newCandidateIds
      };
      
      setColumns({
        ...columns,
        [newColumn.id]: newColumn
      });
      
    } else {
      // Moviendo de una columna a otra
      // Quitamos de la columna de origen
      const sourceIds = Array.from(sourceColumn.candidateIds);
      sourceIds.splice(source.index, 1);
      
      // Añadimos a la columna destino
      const destIds = Array.from(destColumn.candidateIds);
      destIds.splice(destination.index, 0, draggableId);
      
      // Actualizamos ambas columnas
      const newSourceColumn = {
        ...sourceColumn,
        candidateIds: sourceIds
      };
      
      const newDestColumn = {
        ...destColumn,
        candidateIds: destIds
      };
      
      setColumns({
        ...columns,
        [newSourceColumn.id]: newSourceColumn,
        [newDestColumn.id]: newDestColumn
      });

      // Actualizar estado del candidato
      setCandidates({
        ...candidates,
        [draggableId]: {
          ...candidates[draggableId],
          status: destColumn.title
        }
      });
      
      // Mostrar notificación de acción automática
      handleAutomatedAction(destination.droppableId, draggableId);
    }
  };

  // Simular acciones automáticas basadas en el movimiento
  const handleAutomatedAction = (columnId: string, candidateId: string) => {
    const candidate = candidates[candidateId];
    const column = columns[columnId];

    switch (columnId) {
      case 'entrevista':
        // Simular programación de entrevista
        const interviewDate = new Date();
        interviewDate.setDate(interviewDate.getDate() + 3); // Entrevista en 3 días
        
        setCandidates({
          ...candidates,
          [candidateId]: {
            ...candidate,
            interview: interviewDate
          }
        });
        
        setNotification({
          visible: true,
          type: 'success',
          message: `Se ha programado automáticamente una entrevista con ${candidate.name} para el ${interviewDate.toLocaleDateString()}`,
          action: 'interview_scheduled',
          candidate: candidate.name
        });
        break;
        
      case 'oferta':
        // Simular envío de carta oferta
        setNotification({
          visible: true,
          type: 'success',
          message: `Se ha enviado automáticamente la carta oferta a ${candidate.name}. El sistema notificará cuando sea firmada.`,
          action: 'offer_sent',
          candidate: candidate.name
        });
        break;
        
      case 'contratado':
        // Simular inicio de onboarding
        setNotification({
          visible: true,
          type: 'success',
          message: `Se ha iniciado el proceso de onboarding para ${candidate.name}. RH recibirá notificación automática.`,
          action: 'onboarding_started',
          candidate: candidate.name
        });
        break;
        
      default:
        // Para cualquier otra columna
        setNotification({
          visible: true,
          type: 'info',
          message: `${candidate.name} ha sido movido a ${column.title}`,
          action: 'status_changed',
          candidate: candidate.name
        });
    }

    // Ocultar notificación después de 5 segundos
    setTimeout(() => {
      setNotification({...notification, visible: false});
    }, 5000);
  };

  // Ordenar las columnas para visualizarlas en orden específico
  const columnOrder = ['evaluacion', 'entrevista', 'oferta', 'contratado'];

  return (
    <div className="bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-extrabold text-gray-900 dark:text-gray-100 sm:text-4xl">
            Dashboard de Selección
          </h2>
          <p className="mt-4 text-xl text-gray-600 dark:text-gray-300">
            Arrastra candidatos entre categorías para activar acciones automáticas
          </p>
        </div>

        {/* Sistema de notificación animado */}
        <AnimatePresence>
          {notification.visible && (
            <motion.div
              initial={{ opacity: 0, y: -50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -50 }}
              className={`fixed top-4 right-4 z-50 max-w-md ${
                notification.type === 'success' ? 'bg-green-50 dark:bg-green-900/30' : 'bg-blue-50 dark:bg-blue-900/30'
              } p-4 rounded-lg shadow-lg border ${
                notification.type === 'success' ? 'border-green-300 dark:border-green-700' : 'border-blue-300 dark:border-blue-700'
              }`}
            >
              <div className="flex items-start">
                <div className={`flex-shrink-0 ${
                  notification.type === 'success' ? 'text-green-400' : 'text-blue-400'
                }`}>
                  {notification.type === 'success' ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <MessageSquare className="h-5 w-5" />
                  )}
                </div>
                <div className="ml-3">
                  <h3 className={`text-sm font-medium ${
                    notification.type === 'success' ? 'text-green-800 dark:text-green-200' : 'text-blue-800 dark:text-blue-200'
                  }`}>
                    Acción Automática
                  </h3>
                  <div className={`mt-2 text-sm ${
                    notification.type === 'success' ? 'text-green-700 dark:text-green-300' : 'text-blue-700 dark:text-blue-300'
                  }`}>
                    {notification.message}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Dashboard Drag & Drop */}
        <DragDropContext onDragEnd={onDragEnd}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
            {columnOrder.map(columnId => {
              const column = columns[columnId];
              const columnCandidates = column.candidateIds.map(id => candidates[id]);
              
              return (
                <div key={columnId} className="flex flex-col h-full">
                  {/* Encabezado de columna */}
                  <div className={`rounded-t-lg px-4 py-3 ${column.color} text-white`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        {column.icon}
                        <h3 className="text-lg font-semibold ml-2">{column.title}</h3>
                      </div>
                      <Badge className="bg-white/20 text-white">{column.candidateIds.length}</Badge>
                    </div>
                    <p className="text-sm text-white/80 mt-1">{column.description}</p>
                  </div>

                  {/* Contenido de la columna (lista de candidatos) */}
                  <Droppable droppableId={columnId}>
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.droppableProps}
                        className={`flex-grow p-2 min-h-[50vh] rounded-b-lg border-x border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 ${
                          snapshot.isDraggingOver ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                        }`}
                      >
                        {columnCandidates.map((candidate, index) => (
                          <Draggable key={candidate.id} draggableId={candidate.id} index={index}>
                            {(provided, snapshot) => (
                              <Card
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                                className={`mb-3 border ${
                                  snapshot.isDragging
                                    ? 'border-blue-300 dark:border-blue-600 shadow-lg'
                                    : 'border-gray-200 dark:border-gray-700'
                                } transition-all duration-200 hover:shadow-md`}
                              >
                                <CardContent className="p-3">
                                  <div className="flex items-start space-x-3">
                                    <Avatar className="h-10 w-10">
                                      <AvatarImage src={candidate.avatar} alt={candidate.name} />
                                      <AvatarFallback>{candidate.name.charAt(0)}</AvatarFallback>
                                    </Avatar>
                                    <div className="flex-1">
                                      <div className="flex items-center justify-between">
                                        <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                          {candidate.name}
                                        </h4>
                                        <Badge className={`bg-gradient-to-r ${
                                          candidate.match > 90 
                                            ? 'from-green-500 to-green-600'
                                            : candidate.match > 80
                                              ? 'from-blue-500 to-blue-600'
                                              : 'from-yellow-500 to-yellow-600'
                                        }`}>
                                          {candidate.match}% Match
                                        </Badge>
                                      </div>
                                      <p className="text-sm text-gray-600 dark:text-gray-400">
                                        {candidate.position}
                                      </p>
                                      <div className="flex items-center mt-2 text-xs text-gray-500 dark:text-gray-400">
                                        <Briefcase className="h-3 w-3 mr-1" />
                                        <span>{candidate.company}</span>
                                        {candidate.interview && (
                                          <>
                                            <Clock className="h-3 w-3 ml-2 mr-1" />
                                            <span>
                                              Entrevista: {candidate.interview.toLocaleDateString()}
                                            </span>
                                          </>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                </CardContent>
                              </Card>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                        
                        {/* Mensaje cuando la columna está vacía */}
                        {columnCandidates.length === 0 && (
                          <div className="flex flex-col items-center justify-center h-32 text-gray-400 dark:text-gray-500 text-sm border border-dashed border-gray-200 dark:border-gray-700 rounded-lg p-4">
                            <ArrowRight className="h-5 w-5 mb-2" />
                            <p>Arrastra candidatos aquí</p>
                            <p className="mt-1 text-xs text-center">{column.actionDescription}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </Droppable>
                  
                  {/* Indicador de acción automática */}
                  <div className="mt-2 text-xs text-center text-gray-500 dark:text-gray-400 flex items-center justify-center">
                    <span className="inline-block w-2 h-2 rounded-full bg-blue-400 mr-1"></span>
                    <span>Acción: {column.actionDescription}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </DragDropContext>
        
        {/* Instrucciones para el demo */}
        <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-center">
          <h3 className="font-medium text-blue-800 dark:text-blue-200">Prueba el sistema</h3>
          <p className="text-sm text-blue-700 dark:text-blue-300">
            Arrastra cualquier candidato a otra columna para ver las acciones automáticas en acción
          </p>
        </div>
      </div>
    </div>
  );
};

export default DragDropDashboard;
